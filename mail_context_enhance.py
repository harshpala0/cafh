"""CA FirmHub — Mail client-context API. Designed & Built by Harsh Pala.

Preview endpoint for optional per-client sections in Mail UI.
Actual enrichment runs inside mail_enhance.mail_send (no fragile wrapper).
"""
from datetime import date, timedelta, datetime
from flask import request, jsonify, g


def register_mail_context(app, helpers):
    qry = helpers["qry"]
    login_required = helpers["login_required"]

    def staff_ok():
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "TeamLeader", "Member", "SuperAdmin", "Team Leader")

    def _parse_date(dd):
        if dd is None:
            return None, ""
        if hasattr(dd, "isoformat"):
            ddate = dd if isinstance(dd, date) and not isinstance(dd, datetime) else (
                dd.date() if hasattr(dd, "date") else dd
            )
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
        try:
            ph = ",".join(["%s"] * len(client_ids))
            rows = qry(
                f"""
                SELECT q.query_text, q.status, q.sr_no, e.client_id
                FROM queries q
                JOIN engagements e ON e.id = q.engagement_id
                WHERE q.firm_id = %s AND e.client_id IN ({ph})
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
        try:
            ph = ",".join(["%s"] * len(client_ids))
            rows = qry(
                f"""
                SELECT c.title, c.category, c.due_date, c.status,
                       COALESCE(c.client_id, e.client_id) AS client_id
                FROM compliance_calendar c
                LEFT JOIN engagements e ON e.id = c.engagement_id
                WHERE c.firm_id = %s AND c.due_date IS NOT NULL
                  AND LOWER(COALESCE(c.status, '')) NOT IN ('completed','missed','filed','done','closed')
                  AND (c.client_id IN ({ph}) OR e.client_id IN ({ph}))
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
        for cid in out:
            out[cid]["pending_queries"] = out[cid]["pending_queries"][:15]
            out[cid]["overdue"] = sorted(set(out[cid]["overdue"]))[:20]
            out[cid]["upcoming"] = sorted(set(out[cid]["upcoming"]))[:20]
        return out

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

    print("[mail_ctx] Client-context preview API registered (send enrichment in mail_enhance)")
