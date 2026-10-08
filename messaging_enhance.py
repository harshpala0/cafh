"""
CA FirmHub — Client messaging (additive).
1) Save firm admin email & phone
2) Select clients → send to contact_email / contact_phone

Email delivery (in order):
  1) RESEND_API_KEY  → HTTPS (works on Render free tier)
  2) SMTP with SSL on 465 or STARTTLS on 587
"""
import os
import json
import smtplib
import ssl
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "Team Leader", "SuperAdmin")

    def _ensure_cols():
        for sql in (
            "ALTER TABLE firms ADD COLUMN IF NOT EXISTS notify_email TEXT",
            "ALTER TABLE firms ADD COLUMN IF NOT EXISTS notify_phone TEXT",
            "ALTER TABLE firms ADD COLUMN IF NOT EXISTS notify_from_name TEXT",
        ):
            try:
                execute(sql)
            except Exception as e:
                print("[messaging] alter:", e)

    def _firm_settings(firm_id):
        _ensure_cols()
        try:
            row = qry(
                "SELECT id, name, notify_email, notify_phone, notify_from_name "
                "FROM firms WHERE id=%s",
                (firm_id,), one=True)
        except Exception as e:
            print("[messaging] select fallback:", e)
            row = qry("SELECT id, name FROM firms WHERE id=%s", (firm_id,), one=True) or {}
            row = dict(row)
            row.setdefault("notify_email", "")
            row.setdefault("notify_phone", "")
            row.setdefault("notify_from_name", "")
        return row or {}

    def _email_ready():
        if os.environ.get("RESEND_API_KEY"):
            return True
        return bool(os.environ.get("SMTP_HOST") and (os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER")))

    def _send_via_resend(to_addr, subject, body, from_name=None, reply_to=None):
        key = os.environ.get("RESEND_API_KEY", "").strip()
        if not key:
            return False, "RESEND_API_KEY not set"
        from_addr = os.environ.get("SMTP_FROM") or os.environ.get("RESEND_FROM") or "onboarding@resend.dev"
        if from_name:
            from_header = f"{from_name} <{from_addr}>"
        else:
            from_header = from_addr
        payload = {
            "from": from_header,
            "to": [to_addr],
            "subject": subject,
            "text": body,
        }
        if reply_to:
            payload["reply_to"] = reply_to
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return True, resp.read().decode()[:200]
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()[:300] if e.fp else str(e)
            return False, f"Resend HTTP {e.code}: {err_body}"
        except Exception as e:
            return False, str(e)

    def _send_via_smtp(to_addr, subject, body, reply_to=None, from_name=None):
        host = (os.environ.get("SMTP_HOST") or "").strip()
        port = int(os.environ.get("SMTP_PORT") or "587")
        user = (os.environ.get("SMTP_USER") or "").strip()
        password = (os.environ.get("SMTP_PASS") or "").strip()
        from_addr = (os.environ.get("SMTP_FROM") or user).strip()
        if not host or not from_addr:
            return False, "Email server not configured (set SMTP_* or RESEND_API_KEY on Render)"
        if not to_addr or "@" not in str(to_addr):
            return False, "Invalid recipient email"

        msg = MIMEMultipart()
        msg["From"] = f"{from_name} <{from_addr}>" if from_name else from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            ctx = ssl.create_default_context()
            # Port 465 = implicit SSL; 587 = STARTTLS
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=30, context=ctx)
            else:
                server = smtplib.SMTP(host, port, timeout=30)
                if os.environ.get("SMTP_TLS", "1") != "0":
                    server.starttls(context=ctx)
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            server.quit()
            return True, "sent"
        except OSError as e:
            # Errno 101 = Network unreachable — common on Render free tier for SMTP ports
            err = str(e)
            if "101" in err or "unreachable" in err.lower():
                return False, (
                    "Network unreachable to SMTP host. Render free tier often blocks port 587/465. "
                    "Fix: add RESEND_API_KEY (free at resend.com) — uses HTTPS and works on Render. "
                    "Or try SMTP_PORT=465."
                )
            return False, err
        except Exception as e:
            return False, str(e)

    def _send_email(to_addr, subject, body, reply_to=None, from_name=None):
        # Prefer Resend (HTTPS) — reliable on Render free
        if os.environ.get("RESEND_API_KEY"):
            return _send_via_resend(to_addr, subject, body, from_name=from_name, reply_to=reply_to)
        return _send_via_smtp(to_addr, subject, body, reply_to=reply_to, from_name=from_name)

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
        try:
            if not staff_admin():
                return jsonify({"detail": "Admin / Team Leader only"}), 403
            if not getattr(g, "firm_id", None):
                return jsonify({"detail": "No firm linked to this user"}), 400
            s = _firm_settings(g.firm_id)
            return jsonify({
                "notify_email": s.get("notify_email") or "",
                "notify_phone": s.get("notify_phone") or "",
                "notify_from_name": s.get("notify_from_name") or s.get("name") or "",
                "firm_name": s.get("name") or "",
                "smtp_ready": _email_ready(),
                "resend_ready": bool(os.environ.get("RESEND_API_KEY")),
                "whatsapp_ready": bool(os.environ.get("WHATSAPP_WEBHOOK_URL")),
            })
        except Exception as e:
            print("[messaging] GET settings error:", e)
            return jsonify({"detail": f"Settings load failed: {e}"}), 500

    @app.route("/api/ops/messaging/settings", methods=["PUT"])
    @login_required
    def msg_put_settings():
        try:
            if not staff_admin():
                return jsonify({"detail": "Admin / Team Leader only"}), 403
            if not getattr(g, "firm_id", None):
                return jsonify({"detail": "No firm linked to this user"}), 400
            _ensure_cols()
            d = j()
            email = (d.get("notify_email") or "").strip()
            phone = (d.get("notify_phone") or "").strip()
            name = (d.get("notify_from_name") or "").strip()
            if email and "@" not in email:
                return jsonify({"detail": "Invalid email address"}), 400
            execute(
                "UPDATE firms SET notify_email=%s, notify_phone=%s, notify_from_name=%s WHERE id=%s",
                (email or None, phone or None, name or None, g.firm_id))
            try:
                log_action(g.firm_id, g.user["id"], "MSG_SETTINGS", "Firm", g.firm_id,
                           details=f"email={email};phone={phone}")
            except Exception:
                pass
            return jsonify({"ok": True, "notify_email": email, "notify_phone": phone, "notify_from_name": name})
        except Exception as e:
            print("[messaging] PUT settings error:", e)
            return jsonify({"detail": f"Save failed: {e}"}), 500

    @app.route("/api/ops/messaging/clients")
    @login_required
    def msg_clients():
        try:
            if g.user.get("role") not in ("Admin", "Team Leader", "Member", "SuperAdmin"):
                return jsonify({"detail": "Staff only"}), 403
            rows = qry(
                "SELECT id, name, contact_person, contact_email, contact_phone "
                "FROM clients WHERE firm_id=%s AND COALESCE(is_active, TRUE)=TRUE ORDER BY name",
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
        except Exception as e:
            print("[messaging] clients error:", e)
            return jsonify({"detail": f"Could not load clients: {e}"}), 500

    @app.route("/api/ops/messaging/send", methods=["POST"])
    @login_required
    def msg_send():
        try:
            if not staff_admin():
                return jsonify({"detail": "Admin / Team Leader only"}), 403
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
                    "WHERE id=%s AND firm_id=%s",
                    (cid, g.firm_id), one=True)
                if not cl:
                    results.append({"client_id": cid, "ok": False, "detail": "Client not found"})
                    continue

                entry = {"client_id": cl["id"], "client_name": cl["name"], "email": None, "whatsapp": None}
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
        except Exception as e:
            print("[messaging] send error:", e)
            return jsonify({"detail": f"Send failed: {e}"}), 500

    try:
        _ensure_cols()
    except Exception as e:
        print("[messaging] startup ensure:", e)

    print("[messaging] Client messaging routes registered")
