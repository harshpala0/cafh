"""
CA FirmHub — Client Portal (additive module).
Registered by main bootstrap after the core app loads.
Does not modify existing routes; only adds /portal and /api/portal/*.
"""
from datetime import datetime
from functools import wraps
from pathlib import Path
import uuid
import os

from flask import g, request, jsonify, send_from_directory, Response


def register_portal(app, helpers):
    """
    helpers must provide:
      qry, execute, login_required, require_role, log_action,
      _upload_to_r2 (optional), hash_pw
    """
    qry = helpers["qry"]
    execute = helpers["execute"]
    login_required = helpers["login_required"]
    require_role = helpers["require_role"]
    log_action = helpers.get("log_action", lambda *a, **k: None)
    upload_to_r2 = helpers.get("upload_to_r2")

    def _ensure_tables():
        execute("""
        CREATE TABLE IF NOT EXISTS portal_doc_requests (
            id SERIAL PRIMARY KEY,
            firm_id INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            status TEXT NOT NULL DEFAULT 'Open'
                CHECK (status IN ('Open','Submitted','Closed')),
            created_by_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS portal_files (
            id SERIAL PRIMARY KEY,
            firm_id INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            request_id INTEGER REFERENCES portal_doc_requests(id) ON DELETE SET NULL,
            original_filename TEXT NOT NULL,
            file_key TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT,
            note TEXT,
            uploaded_by_id INTEGER REFERENCES users(id),
            uploaded_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_portal_req_client ON portal_doc_requests(client_id);
        CREATE INDEX IF NOT EXISTS idx_portal_files_client ON portal_files(client_id);
        """)

    try:
        _ensure_tables()
    except Exception as e:
        print("[portal] table ensure warning:", e)

    def client_only(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user.get("role") != "Client":
                return jsonify({"detail": "Client portal access only"}), 403
            if not g.user.get("client_id"):
                return jsonify({"detail": "No client linked to this account. Contact your CA firm."}), 403
            return f(*args, **kwargs)
        return wrapped

    def staff_only(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user.get("role") not in ("Admin", "Team Leader", "Member"):
                return jsonify({"detail": "Staff only"}), 403
            return f(*args, **kwargs)
        return wrapped

    @app.route("/portal")
    @app.route("/portal/")
    def portal_page():
        return send_from_directory("static", "client_portal.html")

    @app.route("/api/portal/me")
    @client_only
    def portal_me():
        cl = qry("SELECT id, name, pan, gstin, contact_person, contact_email, contact_phone, entity_type "
                 "FROM clients WHERE id=%s AND firm_id=%s",
                 (g.user["client_id"], g.firm_id), one=True)
        firm = qry("SELECT name, reg_no FROM firms WHERE id=%s", (g.firm_id,), one=True)
        return jsonify({
            "user": {
                "id": g.user["id"],
                "full_name": g.user["full_name"],
                "username": g.user["username"],
                "email": g.user.get("email"),
                "role": g.user["role"],
                "client_id": g.user["client_id"],
            },
            "client": cl,
            "firm": firm,
        })

    @app.route("/api/portal/dashboard")
    @client_only
    def portal_dashboard():
        cid = g.user["client_id"]
        fid = g.firm_id
        def cnt(sql, params):
            r = qry(sql, params, one=True)
            return (r or {}).get("count", 0)
        open_queries = cnt(
            "SELECT COUNT(*) as count FROM queries q "
            "JOIN engagements e ON q.engagement_id=e.id "
            "WHERE q.firm_id=%s AND e.client_id=%s AND q.status='Open'", (fid, cid))
        engagements = cnt(
            "SELECT COUNT(*) as count FROM engagements WHERE firm_id=%s AND client_id=%s", (fid, cid))
        open_reqs = cnt(
            "SELECT COUNT(*) as count FROM portal_doc_requests "
            "WHERE firm_id=%s AND client_id=%s AND status='Open'", (fid, cid))
        invoices_due = cnt(
            "SELECT COUNT(*) as count FROM invoices "
            "WHERE firm_id=%s AND client_id=%s AND status IN ('Sent','Overdue','Partial')", (fid, cid))
        return jsonify({
            "engagements": engagements,
            "open_queries": open_queries,
            "open_doc_requests": open_reqs,
            "invoices_pending": invoices_due,
        })

    @app.route("/api/portal/engagements")
    @client_only
    def portal_engagements():
        rows = qry(
            "SELECT e.id, e.title, e.engagement_type, e.financial_year, e.status, "
            "e.period_from, e.period_to, e.due_date "
            "FROM engagements e WHERE e.firm_id=%s AND e.client_id=%s ORDER BY e.id DESC",
            (g.firm_id, g.user["client_id"]))
        return jsonify(rows or [])

    @app.route("/api/portal/queries")
    @client_only
    def portal_queries():
        rows = qry(
            "SELECT q.id, q.sr_no, q.query_text, q.response, q.status, q.raised_date, "
            "q.responded_date, q.task_reference, e.title as engagement_title, e.id as engagement_id "
            "FROM queries q JOIN engagements e ON q.engagement_id=e.id "
            "WHERE q.firm_id=%s AND e.client_id=%s ORDER BY q.status='Open' DESC, q.id DESC",
            (g.firm_id, g.user["client_id"]))
        return jsonify(rows or [])

    @app.route("/api/portal/queries/<int:qid>/respond", methods=["POST"])
    @client_only
    def portal_query_respond(qid):
        d = request.get_json() or {}
        response = (d.get("response") or "").strip()
        if not response:
            return jsonify({"detail": "Response text required"}), 400
        q = qry(
            "SELECT q.* FROM queries q JOIN engagements e ON q.engagement_id=e.id "
            "WHERE q.id=%s AND q.firm_id=%s AND e.client_id=%s",
            (qid, g.firm_id, g.user["client_id"]), one=True)
        if not q:
            return jsonify({"detail": "Query not found"}), 404
        execute(
            "UPDATE queries SET response=%s, status='Responded', "
            "responded_by_id=%s, responded_date=NOW() WHERE id=%s",
            (response, g.user["id"], qid))
        log_action(g.firm_id, g.user["id"], "PORTAL_QUERY_RESPONSE", "Query", qid)
        return jsonify({"ok": True})

    @app.route("/api/portal/invoices")
    @client_only
    def portal_invoices():
        rows = qry(
            "SELECT id, invoice_no, invoice_date, due_date, total_amount, amount_paid, "
            "status, financial_year FROM invoices "
            "WHERE firm_id=%s AND client_id=%s ORDER BY invoice_date DESC NULLS LAST, id DESC",
            (g.firm_id, g.user["client_id"]))
        return jsonify(rows or [])

    @app.route("/api/portal/documents")
    @client_only
    def portal_documents():
        rows = qry(
            "SELECT id, doc_type, doc_name, doc_category, doc_date, status, reference_no, remarks "
            "FROM doc_register WHERE firm_id=%s AND client_id=%s "
            "ORDER BY doc_date DESC NULLS LAST, id DESC LIMIT 200",
            (g.firm_id, g.user["client_id"]))
        return jsonify(rows or [])

    @app.route("/api/portal/doc-requests")
    @client_only
    def portal_my_requests():
        rows = qry(
            "SELECT r.*, "
            "(SELECT COUNT(*) FROM portal_files f WHERE f.request_id=r.id) as file_count "
            "FROM portal_doc_requests r "
            "WHERE r.firm_id=%s AND r.client_id=%s ORDER BY r.status='Open' DESC, r.id DESC",
            (g.firm_id, g.user["client_id"]))
        return jsonify(rows or [])

    @app.route("/api/portal/doc-requests/<int:rid>/files")
    @client_only
    def portal_request_files(rid):
        req = qry(
            "SELECT * FROM portal_doc_requests WHERE id=%s AND firm_id=%s AND client_id=%s",
            (rid, g.firm_id, g.user["client_id"]), one=True)
        if not req:
            return jsonify({"detail": "Not found"}), 404
        files = qry(
            "SELECT id, original_filename, file_size, mime_type, note, uploaded_at "
            "FROM portal_files WHERE request_id=%s AND firm_id=%s ORDER BY id DESC",
            (rid, g.firm_id))
        return jsonify(files or [])

    @app.route("/api/portal/upload", methods=["POST"])
    @client_only
    def portal_upload():
        rid = request.form.get("request_id")
        note = (request.form.get("note") or "").strip()
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"detail": "No file"}), 400
        request_id = int(rid) if rid else None
        if request_id:
            req = qry(
                "SELECT * FROM portal_doc_requests WHERE id=%s AND firm_id=%s AND client_id=%s",
                (request_id, g.firm_id, g.user["client_id"]), one=True)
            if not req:
                return jsonify({"detail": "Request not found"}), 404
        raw = f.read()
        key = f"portal/{g.firm_id}/{g.user['client_id']}/{uuid.uuid4().hex}_{f.filename}"
        if upload_to_r2:
            try:
                upload_to_r2(raw, key, f.content_type or "application/octet-stream")
            except Exception:
                up = Path("static/uploads/portal")
                up.mkdir(parents=True, exist_ok=True)
                local = up / f"{uuid.uuid4().hex}_{f.filename}"
                local.write_bytes(raw)
                key = str(local)
        else:
            up = Path("static/uploads/portal")
            up.mkdir(parents=True, exist_ok=True)
            local = up / f"{uuid.uuid4().hex}_{f.filename}"
            local.write_bytes(raw)
            key = str(local)
        execute(
            "INSERT INTO portal_files (firm_id, client_id, request_id, original_filename, "
            "file_key, file_size, mime_type, note, uploaded_by_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (g.firm_id, g.user["client_id"], request_id, f.filename, key,
             len(raw), f.content_type, note, g.user["id"]))
        if request_id:
            execute(
                "UPDATE portal_doc_requests SET status='Submitted' WHERE id=%s AND status='Open'",
                (request_id,))
        log_action(g.firm_id, g.user["id"], "PORTAL_UPLOAD", "PortalFile", request_id)
        return jsonify({"ok": True})

    @app.route("/api/portal/admin/doc-requests")
    @staff_only
    def admin_list_requests():
        client_id = request.args.get("client_id")
        sql = (
            "SELECT r.*, c.name as client_name, u.full_name as created_by_name, "
            "(SELECT COUNT(*) FROM portal_files f WHERE f.request_id=r.id) as file_count "
            "FROM portal_doc_requests r "
            "JOIN clients c ON r.client_id=c.id "
            "LEFT JOIN users u ON r.created_by_id=u.id "
            "WHERE r.firm_id=%s"
        )
        params = [g.firm_id]
        if client_id:
            sql += " AND r.client_id=%s"
            params.append(int(client_id))
        sql += " ORDER BY r.id DESC LIMIT 200"
        return jsonify(qry(sql, tuple(params)) or [])

    @app.route("/api/portal/admin/doc-requests", methods=["POST"])
    @staff_only
    def admin_create_request():
        d = request.get_json() or {}
        client_id = d.get("client_id")
        title = (d.get("title") or "").strip()
        if not client_id or not title:
            return jsonify({"detail": "client_id and title required"}), 400
        cl = qry("SELECT id FROM clients WHERE id=%s AND firm_id=%s",
                 (client_id, g.firm_id), one=True)
        if not cl:
            return jsonify({"detail": "Client not found"}), 404
        execute(
            "INSERT INTO portal_doc_requests (firm_id, client_id, title, description, "
            "due_date, created_by_id) VALUES (%s,%s,%s,%s,%s,%s)",
            (g.firm_id, client_id, title, d.get("description"), d.get("due_date"),
             g.user["id"]))
        return jsonify({"ok": True}), 201

    @app.route("/api/portal/admin/doc-requests/<int:rid>", methods=["PUT"])
    @staff_only
    def admin_update_request(rid):
        d = request.get_json() or {}
        req = qry("SELECT * FROM portal_doc_requests WHERE id=%s AND firm_id=%s",
                  (rid, g.firm_id), one=True)
        if not req:
            return jsonify({"detail": "Not found"}), 404
        status = d.get("status")
        if status and status in ("Open", "Submitted", "Closed"):
            execute("UPDATE portal_doc_requests SET status=%s WHERE id=%s", (status, rid))
        return jsonify({"ok": True})

    @app.route("/api/portal/admin/doc-requests/<int:rid>/files")
    @staff_only
    def admin_request_files(rid):
        req = qry("SELECT * FROM portal_doc_requests WHERE id=%s AND firm_id=%s",
                  (rid, g.firm_id), one=True)
        if not req:
            return jsonify({"detail": "Not found"}), 404
        files = qry(
            "SELECT id, original_filename, file_size, mime_type, note, uploaded_at, file_key "
            "FROM portal_files WHERE request_id=%s AND firm_id=%s ORDER BY id DESC",
            (rid, g.firm_id))
        return jsonify(files or [])

    print("[portal] Client Portal routes registered")
