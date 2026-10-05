"""
CA FirmHub — Ops enhancements (additive):
- Receivables / fee ageing board
- Staff portal inbox (doc requests + uploads)
- Unified reminders (compliance, docs, fees)
"""
from datetime import date, datetime, timedelta
from flask import request, jsonify, g


def register_ops_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    login_required = helpers["login_required"]
    require_role = helpers["require_role"]
    log_action = helpers.get("log_action", lambda *a, **k: None)

    def staff_ok():
        return g.user.get("role") in ("Admin", "Team Leader", "Member")

    def j():
        return request.get_json(silent=True) or {}

    @app.route("/api/ops/receivables")
    @login_required
    def ops_receivables():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        today = date.today()
        rows = qry(
            "SELECT i.id, i.invoice_no, i.invoice_date, i.total_amount, i.payment_status, "
            "i.payment_date, i.payment_note, i.description, i.client_id, c.name as client_name "
            "FROM invoices i JOIN clients c ON i.client_id=c.id "
            "WHERE i.firm_id=%s AND i.payment_status IN ('Unpaid','Partial') "
            "ORDER BY i.invoice_date ASC",
            (g.firm_id,)) or []

        buckets = {"current": [], "d1_30": [], "d31_60": [], "d61_90": [], "d90_plus": []}
        total_os = 0.0
        for r in rows:
            inv_d = r.get("invoice_date")
            if isinstance(inv_d, str):
                try:
                    inv_d = datetime.strptime(inv_d[:10], "%Y-%m-%d").date()
                except Exception:
                    inv_d = today
            age = (today - inv_d).days if inv_d else 0
            r["age_days"] = age
            amt = float(r.get("total_amount") or 0)
            total_os += amt
            if age <= 0:
                buckets["current"].append(r)
            elif age <= 30:
                buckets["d1_30"].append(r)
            elif age <= 60:
                buckets["d31_60"].append(r)
            elif age <= 90:
                buckets["d61_90"].append(r)
            else:
                buckets["d90_plus"].append(r)

        def sum_bucket(key):
            return round(sum(float(x.get("total_amount") or 0) for x in buckets[key]), 2)

        return jsonify({
            "total_outstanding": round(total_os, 2),
            "counts": {k: len(v) for k, v in buckets.items()},
            "amounts": {k: sum_bucket(k) for k in buckets},
            "buckets": buckets,
            "all": rows,
        })

    @app.route("/api/ops/portal-inbox")
    @login_required
    def ops_portal_inbox():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        status = request.args.get("status")
        sql = (
            "SELECT r.*, c.name as client_name, u.full_name as created_by_name, "
            "(SELECT COUNT(*) FROM portal_files f WHERE f.request_id=r.id) as file_count "
            "FROM portal_doc_requests r "
            "JOIN clients c ON r.client_id=c.id "
            "LEFT JOIN users u ON r.created_by_id=u.id "
            "WHERE r.firm_id=%s"
        )
        params = [g.firm_id]
        if status and status != "all":
            sql += " AND r.status=%s"
            params.append(status)
        sql += " ORDER BY CASE r.status WHEN 'Submitted' THEN 0 WHEN 'Open' THEN 1 ELSE 2 END, r.id DESC LIMIT 200"
        return jsonify(qry(sql, tuple(params)) or [])

    @app.route("/api/ops/portal-inbox/<int:rid>/files")
    @login_required
    def ops_portal_files(rid):
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        req = qry("SELECT * FROM portal_doc_requests WHERE id=%s AND firm_id=%s",
                  (rid, g.firm_id), one=True)
        if not req:
            return jsonify({"detail": "Not found"}), 404
        files = qry(
            "SELECT id, original_filename, file_size, mime_type, note, uploaded_at, file_key "
            "FROM portal_files WHERE request_id=%s AND firm_id=%s ORDER BY id DESC",
            (rid, g.firm_id)) or []
        for f in files:
            key = f.get("file_key") or ""
            if key.startswith("static/"):
                f["download_url"] = "/" + key.replace("\\", "/")
            elif key.startswith("portal/"):
                f["download_url"] = None
                f["storage"] = "r2"
            else:
                f["download_url"] = None
        return jsonify({"request": req, "files": files})

    @app.route("/api/ops/portal-inbox/<int:rid>/close", methods=["POST"])
    @login_required
    def ops_portal_close(rid):
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        execute(
            "UPDATE portal_doc_requests SET status='Closed' WHERE id=%s AND firm_id=%s",
            (rid, g.firm_id))
        log_action(g.firm_id, g.user["id"], "PORTAL_REQ_CLOSE", "PortalRequest", rid)
        return jsonify({"ok": True})

    @app.route("/api/ops/reminders")
    @login_required
    def ops_reminders():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        today = date.today()
        week = today + timedelta(days=7)
        fid = g.firm_id
        try:
            execute(
                "UPDATE compliance_calendar SET status='Missed' "
                "WHERE firm_id=%s AND status='Upcoming' AND due_date < %s",
                (fid, today.isoformat()))
        except Exception:
            pass

        compliance = qry(
            "SELECT id, title, category, due_date, status, client_id FROM compliance_calendar "
            "WHERE firm_id=%s AND status IN ('Upcoming','Missed') "
            "AND due_date <= %s ORDER BY due_date LIMIT 40",
            (fid, week.isoformat())) or []

        doc_reqs = qry(
            "SELECT r.id, r.title, r.due_date, r.status, c.name as client_name "
            "FROM portal_doc_requests r JOIN clients c ON r.client_id=c.id "
            "WHERE r.firm_id=%s AND r.status IN ('Open','Submitted') "
            "ORDER BY r.status='Submitted' DESC, r.due_date NULLS LAST LIMIT 30",
            (fid,)) or []

        fees = qry(
            "SELECT i.id, i.invoice_no, i.invoice_date, i.total_amount, i.payment_status, "
            "c.name as client_name FROM invoices i JOIN clients c ON i.client_id=c.id "
            "WHERE i.firm_id=%s AND i.payment_status IN ('Unpaid','Partial') "
            "ORDER BY i.invoice_date LIMIT 30",
            (fid,)) or []

        items = []
        for c in compliance:
            due = str(c.get("due_date") or "")[:10]
            sev = "high" if c.get("status") == "Missed" else "warn"
            items.append({
                "type": "compliance", "severity": sev,
                "title": c.get("title"), "due_date": due,
                "meta": c.get("category"), "ref_id": c.get("id"),
            })
        for d in doc_reqs:
            items.append({
                "type": "doc_request",
                "severity": "info" if d.get("status") == "Open" else "ok",
                "title": d.get("title"),
                "due_date": str(d.get("due_date") or "")[:10] or None,
                "meta": (d.get("client_name") or "") + " · " + (d.get("status") or ""),
                "ref_id": d.get("id"),
            })
        for f in fees:
            items.append({
                "type": "fee", "severity": "warn",
                "title": f"Invoice {f.get('invoice_no')} — ₹{f.get('total_amount')}",
                "due_date": str(f.get("invoice_date") or "")[:10],
                "meta": f.get("client_name"),
                "ref_id": f.get("id"),
            })

        return jsonify({
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "counts": {
                "compliance": len(compliance),
                "doc_requests": len(doc_reqs),
                "fees": len(fees),
                "total": len(items),
            },
            "items": items,
        })

    @app.route("/api/ops/reminders/log", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def ops_reminder_log():
        d = j()
        log_action(
            g.firm_id, g.user["id"], "REMINDER_SENT",
            d.get("type") or "Reminder", d.get("ref_id"),
            details=str(d.get("note") or d.get("channel") or "manual"))
        return jsonify({"ok": True})

    print("[ops] Ops enhancement routes registered")
