"""CA FirmHub — Mail client-context. Designed & Built by Harsh Pala."""
from datetime import date, timedelta, datetime
from flask import request, jsonify, g


def register_mail_context(app, helpers):
    qry = helpers["qry"]
    login_required = helpers["login_required"]
    orig_send = app.view_functions.get("mail_send")

    def staff_ok():
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "TeamLeader", "Member", "SuperAdmin", "Team Leader")

    def _ctx(firm_id, client_ids, days=30):
        today = date.today()
        end = today + timedelta(days=days)
        out = {int(c): {"pending_queries": [], "overdue": [], "upcoming": []} for c in client_ids}
        for cid in client_ids:
            for sql in (
                "SELECT COALESCE(subject,title,query_text,description,'') AS subject, COALESCE(status,'') AS status "
                "FROM queries WHERE firm_id=%s AND client_id=%s AND LOWER(COALESCE(status,'')) "
                "NOT IN ('closed','resolved','completed','done','answered') LIMIT 20",
                "SELECT COALESCE(subject,title,query_text,'') AS subject, COALESCE(status,'') AS status "
                "FROM client_queries WHERE firm_id=%s AND client_id=%s AND LOWER(COALESCE(status,'')) "
                "NOT IN ('closed','resolved','completed','done') LIMIT 20",
            ):
                try:
                    for r in (qry(sql, (firm_id, cid)) or []):
                        s = (r.get("subject") or "").strip() or "Query"
                        st = (r.get("status") or "").strip()
                        out[int(cid)]["pending_queries"].append(s if not st else f"{s} [{st}]")
                    if out[int(cid)]["pending_queries"]:
                        break
                except Exception:
                    continue
            try:
                rows = qry(
                    "SELECT title, category, due_date FROM compliance_calendar "
                    "WHERE firm_id=%s AND client_id=%s AND due_date IS NOT NULL "
                    "AND LOWER(COALESCE(status,'')) NOT IN ('completed','filed','done','closed')",
                    (firm_id, cid),
                ) or []
            except Exception:
                rows = []
            for r in rows:
                dd = r.get("due_date")
                if hasattr(dd, "isoformat"):
                    ddate = dd if isinstance(dd, date) else dd.date()
                    ds = dd.isoformat()[:10]
                else:
                    ds = str(dd or "")[:10]
                    try:
                        ddate = datetime.strptime(ds, "%Y-%m-%d").date()
                    except Exception:
                        continue
                title = (r.get("title") or "Item").strip()
                cat = (r.get("category") or "").strip()
                line = f"{title}" + (f" ({cat})" if cat else "") + f" — due {ds}"
                if ddate < today:
                    out[int(cid)]["overdue"].append(line)
                elif ddate <= end:
                    out[int(cid)]["upcoming"].append(line)
        for cid in out:
            out[cid]["pending_queries"] = out[cid]["pending_queries"][:15]
            out[cid]["overdue"] = sorted(out[cid]["overdue"])[:20]
            out[cid]["upcoming"] = sorted(out[cid]["upcoming"])[:20]
        return out

    def _append(body, ctx, q, o, u):
        parts = [body.rstrip()]
        if q and ctx.get("pending_queries"):
            parts.append("\n\n--- Pending queries ---\n" + "\n".join(f"• {x}" for x in ctx["pending_queries"]))
        if o and ctx.get("overdue"):
            parts.append("\n\n--- Overdue compliance dates ---\n" + "\n".join(f"• {x}" for x in ctx["overdue"]))
        if u and ctx.get("upcoming"):
            parts.append("\n\n--- Upcoming due dates ---\n" + "\n".join(f"• {x}" for x in ctx["upcoming"]))
        return "\n".join(parts).strip() + "\n"

    @app.route("/api/mail/client-context")
    @login_required
    def mail_client_context():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        ids = [int(x) for x in (request.args.get("client_ids") or "").split(",") if x.strip().isdigit()]
        if not ids:
            rows = qry(
                "SELECT id FROM clients WHERE firm_id=%s AND COALESCE(is_active,TRUE)=TRUE "
                "AND contact_email IS NOT NULL AND contact_email LIKE '%%@%%'",
                (g.firm_id,),
            ) or []
            ids = [int(r["id"]) for r in rows if r.get("id") is not None]
        ctx = _ctx(g.firm_id, ids)
        summary = {
            str(cid): {
                "pending_queries_count": len(v["pending_queries"]),
                "overdue_count": len(v["overdue"]),
                "upcoming_count": len(v["upcoming"]),
                "pending_queries": v["pending_queries"][:5],
                "overdue": v["overdue"][:5],
                "upcoming": v["upcoming"][:5],
            }
            for cid, v in ctx.items()
        }
        return jsonify({"clients": summary, "upcoming_days": 30})

    if orig_send:
        from functools import wraps
        from flask import request as fr

        @wraps(orig_send)
        def wrapped():
            d = request.get_json(silent=True) or {}
            iq = bool(d.get("include_pending_queries"))
            io = bool(d.get("include_overdue"))
            iu = bool(d.get("include_upcoming"))
            if not (iq or io or iu):
                return orig_send()
            subject = (d.get("subject") or "").strip()
            body = (d.get("body") or "").strip()
            client_ids = d.get("client_ids") or []
            if not subject or not body or not client_ids:
                return orig_send()
            try:
                client_ids = [int(x) for x in client_ids]
            except Exception:
                return orig_send()
            try:
                settings = qry("SELECT * FROM firm_mail_settings WHERE firm_id=%s", (g.firm_id,), one=True) or {}
            except Exception:
                settings = {}
            if settings.get("signature"):
                body = body.rstrip() + "\n\n" + settings["signature"]
            ctx_map = _ctx(g.firm_id, client_ids)
            ph = ",".join(["%s"] * len(client_ids))
            rows = qry(
                f"SELECT id, name, contact_email FROM clients WHERE firm_id=%s AND id IN ({ph})",
                tuple([g.firm_id] + client_ids),
            ) or []
            sent, skipped, errors = [], [], []
            for r in rows:
                em = (r.get("contact_email") or "").strip()
                if not em or "@" not in em:
                    skipped.append({"id": r["id"], "name": r["name"], "reason": "No contact email"})
                    continue
                text = body.replace("{{client_name}}", r["name"] or "").replace("{{name}}", r["name"] or "")
                cid = int(r["id"])
                if cid in ctx_map:
                    text = _append(text, ctx_map[cid], iq, io, iu)
                real = fr.get_json
                fr.get_json = lambda silent=True, **kw: {"subject": subject, "body": text, "client_ids": [cid]}
                try:
                    resp = orig_send()
                    data = resp[0].get_json() if isinstance(resp, tuple) else resp.get_json()
                    if data.get("sent_count"):
                        sent.append({"id": r["id"], "name": r["name"], "email": em})
                    elif data.get("errors"):
                        errors.extend(data["errors"])
                    else:
                        errors.append({"id": r["id"], "name": r["name"], "email": em, "error": data.get("detail") or "failed"})
                except Exception as e:
                    errors.append({"id": r["id"], "name": r["name"], "email": em, "error": str(e)})
                finally:
                    fr.get_json = real
            st = 200 if sent and not errors else (207 if sent else 400)
            return jsonify({
                "sent_count": len(sent), "skipped_count": len(skipped), "error_count": len(errors),
                "sent": sent, "skipped": skipped, "errors": errors,
                "detail": f"Sent {len(sent)}" + (f", skipped {len(skipped)}" if skipped else "") + (f", failed {len(errors)}" if errors else ""),
            }), st

        app.view_functions["mail_send"] = wrapped
        for ep, fn in list(app.view_functions.items()):
            if fn is orig_send:
                app.view_functions[ep] = wrapped

    print("[mail_ctx] Client-context mail sections registered")
