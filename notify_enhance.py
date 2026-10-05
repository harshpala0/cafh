"""
CA FirmHub — Notifications & secure downloads (additive).
- Portal file download (local or R2 presigned URL)
- Optional email digest (SMTP_*)
- Optional WhatsApp via webhook (WHATSAPP_WEBHOOK_URL)
"""
import os
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from pathlib import Path
from flask import request, jsonify, g, send_file, redirect, Response


def register_notify_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    login_required = helpers["login_required"]
    require_role = helpers["require_role"]
    log_action = helpers.get("log_action", lambda *a, **k: None)

    def staff_ok():
        return g.user.get("role") in ("Admin", "Team Leader", "Member")

    def j():
        return request.get_json(silent=True) or {}

    def _r2_client():
        account = os.environ.get("R2_ACCOUNT_ID", "")
        key = os.environ.get("R2_ACCESS_KEY", "")
        secret = os.environ.get("R2_SECRET_KEY", "")
        bucket = os.environ.get("R2_BUCKET", "cafirmhub-files")
        if not key or not account:
            return None, bucket
        import boto3
        from botocore.config import Config
        endpoint = f"https://{account}.r2.cloudflarestorage.com"
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=key,
            aws_secret_access_key=secret,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )
        return s3, bucket

    def _presign(key, expires=3600):
        s3, bucket = _r2_client()
        if not s3:
            return None
        try:
            return s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires,
            )
        except Exception as e:
            print("[notify] presign error:", e)
            return None

    @app.route("/api/ops/portal-files/<int:fid>/download")
    @login_required
    def ops_download_portal_file(fid):
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        f = qry(
            "SELECT * FROM portal_files WHERE id=%s AND firm_id=%s",
            (fid, g.firm_id), one=True)
        if not f:
            return jsonify({"detail": "Not found"}), 404
        key = f.get("file_key") or ""
        name = f.get("original_filename") or "download"

        if key.startswith("static/"):
            path = Path(key)
            if path.exists():
                return send_file(path, as_attachment=True, download_name=name)
            alt = Path(__file__).resolve().parent / key
            if alt.exists():
                return send_file(alt, as_attachment=True, download_name=name)
            return jsonify({"detail": "File missing on server"}), 404

        url = _presign(key)
        if url:
            return redirect(url)
        return jsonify({
            "detail": "Cloud file — configure R2_* env vars for download, or key not local",
            "file_key": key,
        }), 503

    @app.route("/api/ops/portal-inbox/<int:rid>/files-v2")
    @login_required
    def ops_portal_files_v2(rid):
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
        out = []
        for f in files:
            item = dict(f)
            item["download_url"] = f"/api/ops/portal-files/{f['id']}/download"
            out.append(item)
        return jsonify({"request": req, "files": out})

    def _build_digest(firm_id):
        today = date.today()
        week = today + timedelta(days=7)
        try:
            execute(
                "UPDATE compliance_calendar SET status='Missed' "
                "WHERE firm_id=%s AND status='Upcoming' AND due_date < %s",
                (firm_id, today.isoformat()))
        except Exception:
            pass

        compliance = qry(
            "SELECT title, category, due_date, status FROM compliance_calendar "
            "WHERE firm_id=%s AND status IN ('Upcoming','Missed') AND due_date <= %s "
            "ORDER BY due_date LIMIT 30",
            (firm_id, week.isoformat())) or []
        docs = qry(
            "SELECT r.title, r.status, c.name as client_name FROM portal_doc_requests r "
            "JOIN clients c ON r.client_id=c.id "
            "WHERE r.firm_id=%s AND r.status IN ('Open','Submitted') LIMIT 20",
            (firm_id,)) or []
        fees = qry(
            "SELECT i.invoice_no, i.total_amount, c.name as client_name FROM invoices i "
            "JOIN clients c ON i.client_id=c.id "
            "WHERE i.firm_id=%s AND i.payment_status IN ('Unpaid','Partial') LIMIT 20",
            (firm_id,)) or []

        lines = [f"CA FirmHub daily digest — {today.isoformat()}", ""]
        lines.append(f"COMPLIANCE ({len(compliance)})")
        for c in compliance:
            lines.append(f"  • [{c.get('status')}] {c.get('due_date')} — {c.get('title')} ({c.get('category')})")
        lines.append("")
        lines.append(f"DOC REQUESTS ({len(docs)})")
        for d in docs:
            lines.append(f"  • [{d.get('status')}] {d.get('client_name')}: {d.get('title')}")
        lines.append("")
        lines.append(f"OUTSTANDING FEES ({len(fees)})")
        for f in fees:
            lines.append(f"  • {f.get('client_name')}: {f.get('invoice_no')} — ₹{f.get('total_amount')}")
        text = "\n".join(lines)
        return {
            "text": text,
            "counts": {
                "compliance": len(compliance),
                "docs": len(docs),
                "fees": len(fees),
            },
        }

    def _send_email(to_addrs, subject, body):
        host = os.environ.get("SMTP_HOST", "")
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ.get("SMTP_USER", "")
        password = os.environ.get("SMTP_PASS", "")
        from_addr = os.environ.get("SMTP_FROM") or user
        use_tls = os.environ.get("SMTP_TLS", "1") != "0"
        if not host or not from_addr:
            return False, "SMTP_HOST / SMTP_FROM not configured"
        if isinstance(to_addrs, str):
            to_addrs = [a.strip() for a in to_addrs.split(",") if a.strip()]
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        try:
            if use_tls:
                server = smtplib.SMTP(host, port, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP(host, port, timeout=30)
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
            server.quit()
            return True, "sent"
        except Exception as e:
            return False, str(e)

    def _send_whatsapp(phone, message):
        url = os.environ.get("WHATSAPP_WEBHOOK_URL", "")
        if not url:
            return False, "WHATSAPP_WEBHOOK_URL not configured"
        token = os.environ.get("WHATSAPP_WEBHOOK_TOKEN", "")
        payload = json.dumps({"phone": phone, "message": message}).encode()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=20) as resp:
                return True, resp.read().decode()[:200]
        except Exception as e:
            return False, str(e)

    @app.route("/api/ops/notify/preview")
    @login_required
    def notify_preview():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        digest = _build_digest(g.firm_id)
        return jsonify({
            **digest,
            "email_configured": bool(os.environ.get("SMTP_HOST")),
            "whatsapp_configured": bool(os.environ.get("WHATSAPP_WEBHOOK_URL")),
        })

    @app.route("/api/ops/notify/email-digest", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def notify_email_digest():
        d = j()
        to = d.get("to") or os.environ.get("DIGEST_EMAIL_TO") or g.user.get("email")
        if not to:
            return jsonify({"detail": "No recipient. Pass {to} or set DIGEST_EMAIL_TO / user email."}), 400
        digest = _build_digest(g.firm_id)
        ok, info = _send_email(to, f"CA FirmHub digest — {date.today().isoformat()}", digest["text"])
        log_action(g.firm_id, g.user["id"], "EMAIL_DIGEST", "Notify", None, details=str(info)[:200])
        if not ok:
            return jsonify({"detail": info}), 502
        return jsonify({"ok": True, "to": to, "counts": digest["counts"]})

    @app.route("/api/ops/notify/whatsapp", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def notify_whatsapp():
        d = j()
        phone = (d.get("phone") or os.environ.get("DIGEST_WHATSAPP_TO") or "").strip()
        message = d.get("message")
        if not message:
            message = _build_digest(g.firm_id)["text"]
        if not phone:
            return jsonify({"detail": "phone required (or DIGEST_WHATSAPP_TO env)"}), 400
        ok, info = _send_whatsapp(phone, message)
        log_action(g.firm_id, g.user["id"], "WHATSAPP_NOTIFY", "Notify", None, details=str(info)[:200])
        if not ok:
            return jsonify({"detail": info}), 502
        return jsonify({"ok": True, "phone": phone})

    @app.route("/api/ops/notify/status")
    @login_required
    def notify_status():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        return jsonify({
            "smtp": {
                "host": bool(os.environ.get("SMTP_HOST")),
                "from": bool(os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER")),
                "digest_to": os.environ.get("DIGEST_EMAIL_TO") or None,
            },
            "whatsapp": {
                "webhook": bool(os.environ.get("WHATSAPP_WEBHOOK_URL")),
                "digest_to": os.environ.get("DIGEST_WHATSAPP_TO") or None,
            },
            "r2": {
                "configured": bool(os.environ.get("R2_ACCESS_KEY") and os.environ.get("R2_ACCOUNT_ID")),
            },
        })

    print("[notify] Notify / download routes registered")
