"""CA FirmHub — Mail client-context. Designed & Built by Harsh Pala.

Fetches per-client pending queries (via engagements) and compliance due dates.
Optional sections only appended when ticked; never cross-client data.
"""
from datetime import date, timedelta, datetime
from flask import request, jsonify, g


def register_mail_context(app, helpers):
    qry = helpers["qry"]
    login_required = helpers["login_required"]
    orig_send = app.view_functions.get("mail_send")

    def staff_ok():
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "TeamLeader", "Member", "SuperAdmin", "Team Leader")

    def _parse_date(dd):
        if dd is None:
            return None, ""
        if hasattr(dd, "isoformat"):
            ddate = dd if isinstance(dd, date) and not isinstance(dd, datetime) else (dd.date() if hasattr(dd, "date") else dd)
            if isinstance(ddate, datetime):
                ddate = ddate.date()
            return ddate, ddate.isoformat()[:10]
        ds = str(dd or "")[:10]
        try:
            return datetime.strptime(ds, "%Y-%m-%d").date(), ds
        except Exception:
            return None, ds

    def _ctx(firm_id, client_ids, days=30):
        today = date.today()
        end = today + timedelta(days=days)
        out = {int(c): {"pending_queries": [], "overdue": [], "upcoming": []} for c in client_ids}
        if not client_ids:
            return out

        # Pending queries: queries table links via engagement → client
        try:
            ph = ",".join(["%s"] * len(client_ids))
            rows = qry(
                f"""
                SELECT q.query_text, q.status, q.sr_no, e.client_id
                FROM queries q
                JOIN engagements e ON e.id = q.engagement_id
                WHERE q.firm_id = %s
                  AND e.client_id IN ({ph})
                  AND LOWER(COALESCE(q.status, '')) <> 'closed'
                ORDER BY q.sr_no NULLS LAST, q.id
                LIMIT 200
                """,
                tuple([firm_id] + [int(c) for c in client_ids]),
            ) or []
            for r in rows:
                cid = int(r.get("client_id") or 0)
                if cid not in out:
                    continue
                text = (r.get("query_text") or "").strip() or "Query"
                if r.get("sr_no") is not None:
                    text = f"#{r['sr_no']}: {text}"
                st = (r.get("status") or "").strip()
                if st:
                    text = f"{text} [{st}]"
                if len(out[cid]["pending_queries"]) < 15:
                    out[cid]["pending_queries"].append(text)
        except Exception as e:
            print("[mail_ctx] queries:", e)

        # Compliance: prefer client_id column; also match via engagement
        try:
            ph = ",".join(["%s"] * len(client_ids))
            rows = qry(
                f"""
                SELECT c.title, c.category, c.due_date, c.status,
                       COALESCE(c.client_id, e.client_id) AS client_id
                FROM compliance_calendar c
                LEFT JOIN engagements e ON e.id = c.engagement_id
                WHERE c.firm_id = %s
                  AND c.due_date IS NOT NULL
                  AND LOWER(COALESCE(c.status, '')) NOT IN ('completed', 'missed', 'filed', 'done', 'closed')
                  AND (
                    c.client_id IN ({ph})
                    OR e.client_id IN ({ph})
                  )
                """,
                tuple([firm_id] + [int(x) for x in client_ids] + [int(x) for x in client_ids]),
            ) or []
            for r in rows:
                cid = int(r.get("client_id") or 0)
                if cid not in out:
                    continue
                ddate, ds = _parse_date(r.get("due_date"))
                if not ddate:
                    continue
                title = (r.get("title") or "Item").strip()
                cat = (r.get("category") or "").strip()
                line = title + (f" ({cat})" if cat else "") + f" — due {ds}"
                if ddate < today:
                    out[cid]["overdue"].append(line)
                elif ddate <= end:
                    out[cid]["upcoming"].append(line)
        except Exception as e:
            print("[mail_ctx] compliance:", e)
            try:
                rows = qry(
                    """
                    SELECT title, category, due_date, status, client_id
                    FROM compliance_calendar
                    WHERE firm_id = %s AND due_date IS NOT NULL
                      AND LOWER(COALESCE(status, '')) NOT IN ('completed', 'missed', 'filed', 'done', 'closed')
                    """,
                    (firm_id,),
                ) or []
                idset = {int(c) for c in client_ids}
                for r in rows:
                    cid = r.get("client_id")
                    if cid is None or int(cid) not in idset:
                        continue
                    cid = int(cid)
                    ddate, ds = _parse_date(r.get("due_date"))
                    if not ddate:
                        continue
                    title = (r.get("title") or "Item").strip()
                    cat = (r.get("category") or "").strip()
                    line = title + (f" ({cat})" if cat else "") + f" — due {ds}"
                    if ddate < today:
                        out[cid]["overdue"].append(line)
                    elif ddate <= end:
                        out[cid]["upcoming"].append(line)
            except Exception as e2:
                print("[mail_ctx] compliance fallback:", e2)

        for cid in out:
            out[cid]["pending_queries"] = out[cid]["pending_queries"][:15]
            out[cid]["overdue"] = sorted(set(out[cid]["overdue"]))[:20]
            out[cid]["upcoming"] = sorted(set(out[cid]["upcoming"]))[:20]
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
        try:
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
        except Exception as e:
            print("[mail_ctx] client-context:", e)
            return jsonify({"detail": str(e), "clients": {}}), 500

    if orig_send:
        from functools import wraps

        @wraps(orig_send)
        def wrapped():
            try:
                d = request.get_json(silent=True) or {}
            except Exception:
                d = {}
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
            sent, skipped, errors = [], [], []

            for cid in client_ids:
                try:
                    r = qry(
                        "SELECT id, name, contact_email FROM clients WHERE firm_id=%s AND id=%s",
                        (g.firm_id, cid),
                        one=True,
                    )
                except Exception as e:
                    errors.append({"id": cid, "name": "?", "error": str(e)})
                    continue
                if not r:
                    skipped.append({"id": cid, "name": "?", "reason": "Not found"})
                    continue
                em = (r.get("contact_email") or "").strip()
                if not em or "@" not in em:
                    skipped.append({"id": r["id"], "name": r.get("name"), "reason": "No contact email"})
                    continue
                text = body.replace("{{client_name}}", r.get("name") or "").replace("{{name}}", r.get("name") or "")
                if cid in ctx_map:
                    text = _append(text, ctx_map[cid], iq, io, iu)

                payload = {"subject": subject, "body": text, "client_ids": [cid]}
                prev = getattr(request, "_cached_json", None)
                try:
                    request._cached_json = (False, payload)
                    resp = orig_send()
                    if isinstance(resp, tuple):
                        data = resp[0].get_json(silent=True) if hasattr(resp[0], "get_json") else {}
                        status = resp[1] if len(resp) > 1 else 200
                    else:
                        data = resp.get_json(silent=True) if hasattr(resp, "get_json") else {}
                        status = getattr(resp, "status_code", 200) or 200
                    data = data or {}
                    if data.get("sent_count"):
                        sent.append({"id": r["id"], "name": r.get("name"), "email": em})
                    elif data.get("errors"):
                        errors.extend(data["errors"])
                    else:
                        errors.append({
                            "id": r["id"],
                            "name": r.get("name"),
                            "email": em,
                            "error": data.get("detail") or f"HTTP {status}",
                        })
                except Exception as e:
                    errors.append({"id": r["id"], "name": r.get("name"), "email": em, "error": str(e)})
                finally:
                    if prev is not None:
                        request._cached_json = prev
                    else:
                        try:
                            delattr(request, "_cached_json")
                        except Exception:
                            try:
                                request._cached_json = (False, None)
                            except Exception:
                                pass

            st = 200 if sent and not errors else (207 if sent else 400)
            return jsonify({
                "sent_count": len(sent),
                "skipped_count": len(skipped),
                "error_count": len(errors),
                "sent": sent,
                "skipped": skipped,
                "errors": errors,
                "detail": (
                    f"Sent {len(sent)}"
                    + (f", skipped {len(skipped)}" if skipped else "")
                    + (f", failed {len(errors)}" if errors else "")
                ),
            }), st

        app.view_functions["mail_send"] = wrapped
        for ep, fn in list(app.view_functions.items()):
            if fn is orig_send:
                app.view_functions[ep] = wrapped

    print("[mail_ctx] Client-context mail sections registered")
