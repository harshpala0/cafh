"""
CA FirmHub — Client messaging (additive).
Flow:
1) Firm admin saves own email & phone (firm sender settings)
2) Select clients → send email/WhatsApp to each client's contact_email / contact_phone
"""
import os
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import request, jsonify, g


def register_messaging_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    login_required = helpers["login_required"]
    require_role = helpers["require_role"]
    log_action = helpers.get("log_action", lambda *a, **k: None)

    def j():
        return request.get_json(silent=True) or {}

    def staff_admin():
        return g.user.get("role") in ("Admin", "Team Leader")

    def _ensure():
        execute("ALTER TABLE firms ADD COLUMN IF NOT EXISTS notify_email TEXT")
        execute("ALTER TABLE firms ADD COLUMN IF NOT EXISTS notify_phone TEXT")
        execute("ALTER TABLE firms ADD COLUMN IF NOT EXISTS notify_from_name TEXT")

    try:
        _ensure()
    except Exception as e:
        print("[messaging] ensure:", e)

    def _firm_settings(firm_id):
        row = qry(
            "SELECT id, name, notify_email, notify_phone, notify_from_name FROM firms WHERE id=%s",
            (firm_id,), one=True) or {}
        return row

    def _send_email(to_addr, subject, body, reply_to=None, from_name=None):
        host = os.environ.get("SMTP_HOST", "")
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ.get("SMTP_USER", "")
        password = os.environ.get("SMTP_PASS", "")
        from_addr = os.environ.get("SMTP_FROM") or user
        if not host or not from_addr:
            return False, "Email server not configured (set SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM on Render)"
        if not to_addr or "@" not in str(to_addr):
            return False, "Invalid recipient email"
        msg = MIMEMultipart()
        display = from_name or from_addr
        msg["From"] = f"{display} <{from_addr}>" if from_name else from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(body, "plain", "utf-8"))
        try:
            server = smtplib.SMTP(host, port, timeout=30)
            if os.environ.get("SMTP_TLS", "1") != "0":
                server.starttls()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            server.quit()
            return True, "sent"
        except Exception as e:
            return False, str(e)

    def _send_whatsapp(phone, message):
        url = os.environ.get("WHATSAPP_WEBHOOK_URL", "")
        if not url:
            return False, "WhatsApp not configured (set WHATSAPP_WEBHOOK_URL on Render)"
        phone = "".join(ch for ch in str(phone) if ch.isdigit() or ch == "+")
        if not phone:
            return False, "Invalid phone"
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

    @app.route("/api/ops/messaging/settings", methods=["GET"])
    @login_required
    def msg_get_settings():
        if not staff_admin():
            return jsonify({"detail": "Admin / Team Leader only"}), 403
        s = _firm_settings(g.firm_id)
        return jsonify({
            "notify_email": s.get("notify_email") or "",
            "notify_phone": s.get("notify_phone") or "",
            "notify_from_name": s.get("notify_from_name") or s.get("name") or "",
            "firm_name": s.get("name") or "",
            "smtp_ready": bool(os.environ.get("SMTP_HOST") and (os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER"))),
            "whatsapp_ready": bool(os.environ.get("WHATSAPP_WEBHOOK_URL")),
        })

    @app.route("/api/ops/messaging/settings", methods=["PUT"])
    @require_role("Admin", "Team Leader")
    def msg_put_settings():
        d = j()
        email = (d.get("notify_email") or "").strip()
        phone = (d.get("notify_phone") or "").strip()
        name = (d.get("notify_from_name") or "").strip()
        if email and "@" not in email:
            return jsonify({"detail": "Invalid email address"}), 400
        execute(
            "UPDATE firms SET notify_email=%s, notify_phone=%s, notify_from_name=%s WHERE id=%s",
            (email or None, phone or None, name or None, g.firm_id))
        log_action(g.firm_id, g.user["id"], "MSG_SETTINGS", "Firm", g.firm_id,
                   details=f"email={email};phone={phone}")
        return jsonify({"ok": True, "notify_email": email, "notify_phone": phone, "notify_from_name": name})

    @app.route("/api/ops/messaging/clients")
    @login_required
    def msg_clients():
        if g.user.get("role") not in ("Admin", "Team Leader", "Member"):
            return jsonify({"detail": "Staff only"}), 403
        rows = qry(
            "SELECT id, name, contact_person, contact_email, contact_phone "
            "FROM clients WHERE firm_id=%s AND is_active=TRUE ORDER BY name",
            (g.firm_id,)) or []
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "name": r["name"],
                "contact_person": r.get("contact_person") or "",
                "contact_email": (r.get("contact_email") or "").strip(),
                "contact_phone": (r.get("contact_phone") or "").strip(),
                "can_email": bool((r.get("contact_email") or "").strip()),
                "can_whatsapp": bool((r.get("contact_phone") or "").strip()),
            })
        return jsonify(out)

    @app.route("/api/ops/messaging/send", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def msg_send():
        d = j()
        ids = d.get("client_ids") or []
        channel = (d.get("channel") or "email").lower()
        message = (d.get("message") or "").strip()
        subject = (d.get("subject") or "").strip() or f"Message from {g.user.get('full_name') or 'CA FirmHub'}"

        if not ids:
            return jsonify({"detail": "Select at least one client"}), 400
        if not message:
            return jsonify({"detail": "Message text is required"}), 400
        if channel not in ("email", "whatsapp", "both"):
            return jsonify({"detail": "channel must be email, whatsapp, or both"}), 400

        firm = _firm_settings(g.firm_id)
        reply_to = (firm.get("notify_email") or g.user.get("email") or "").strip() or None
        from_name = (firm.get("notify_from_name") or firm.get("name") or "CA FirmHub").strip()

        footer_bits = []
        if firm.get("notify_email"):
            footer_bits.append(f"Email: {firm['notify_email']}")
        if firm.get("notify_phone"):
            footer_bits.append(f"Phone: {firm['notify_phone']}")
        full_body = message
        if footer_bits:
            full_body = message + "\n\n—\n" + from_name + "\n" + "\n".join(footer_bits)

        results = []
        for cid in ids:
            try:
                cid = int(cid)
            except Exception:
                continue
            cl = qry(
                "SELECT id, name, contact_email, contact_phone FROM clients "
                "WHERE id=%s AND firm_id=%s AND is_active=TRUE",
                (cid, g.firm_id), one=True)
            if not cl:
                results.append({"client_id": cid, "ok": False, "detail": "Client not found"})
                continue

            entry = {
                "client_id": cl["id"],
                "client_name": cl["name"],
                "email": None,
                "whatsapp": None,
            }
            em = (cl.get("contact_email") or "").strip()
            ph = (cl.get("contact_phone") or "").strip()

            if channel in ("email", "both"):
                if not em:
                    entry["email"] = {"ok": False, "detail": "No contact_email on client"}
                else:
                    ok, info = _send_email(em, subject, full_body, reply_to=reply_to, from_name=from_name)
                    entry["email"] = {"ok": ok, "detail": info, "to": em}

            if channel in ("whatsapp", "both"):
                if not ph:
                    entry["whatsapp"] = {"ok": False, "detail": "No contact_phone on client"}
                else:
                    ok, info = _send_whatsapp(ph, full_body)
                    entry["whatsapp"] = {"ok": ok, "detail": info, "to": ph}

            results.append(entry)

        log_action(
            g.firm_id, g.user["id"], "MSG_SEND", "Messaging", None,
            details=f"channel={channel};clients={len(ids)}")
        sent_ok = sum(
            1 for r in results
            if (r.get("email") or {}).get("ok") or (r.get("whatsapp") or {}).get("ok")
        )
        return jsonify({
            "ok": True,
            "sent_ok": sent_ok,
            "total": len(results),
            "results": results,
            "from_name": from_name,
            "reply_to": reply_to,
        })

    print("[messaging] Client messaging routes registered")
