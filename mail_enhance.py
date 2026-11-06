"""CA FirmHub — Client mail. Designed & Built by Harsh Pala.

Preferred: Google Apps Script bridge (GMAIL_SCRIPT_URL + GMAIL_SCRIPT_SECRET)
  — uses your noreply Gmail over HTTPS (works on Render free tier).
Fallback: RESEND_API_KEY, then SMTP_*.

Staff select clients; mail goes to contact_email on client records.
Reply-To uses firm mail settings / owner email.
"""
import json
import os
import socket
import smtplib
import urllib.error
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request, jsonify, g


def register_mail_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    login_required = helpers["login_required"]
    require_role = helpers["require_role"]
    log_action = helpers.get("log_action", lambda *a, **k: None)

    def _ensure():
        try:
            execute(
                "CREATE TABLE IF NOT EXISTS firm_mail_settings ("
                "firm_id INTEGER PRIMARY KEY, "
                "from_name TEXT, "
                "from_email TEXT, "
                "reply_to TEXT, "
                "signature TEXT, "
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            return True
        except Exception as e:
            print("[mail] ensure:", e)
            return False

    def staff_ok():
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "TeamLeader", "Member", "SuperAdmin")

    def admin_ok():
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "SuperAdmin")

    def _script_configured():
        return bool(
            (os.environ.get("GMAIL_SCRIPT_URL") or "").strip()
            and (os.environ.get("GMAIL_SCRIPT_SECRET") or "").strip()
        )

    def _resend_configured():
        return bool((os.environ.get("RESEND_API_KEY") or "").strip())

    def _smtp_configured():
        return bool(os.environ.get("SMTP_HOST") and (
            os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER")
        ))

    def _mail_configured():
        return _script_configured() or _resend_configured() or _smtp_configured()

    def _get_settings(firm_id):
        _ensure()
        row = None
        try:
            row = qry(
                "SELECT * FROM firm_mail_settings WHERE firm_id=%s",
                (firm_id,), one=True,
            )
        except Exception as e:
            print("[mail] get_settings:", e)
            row = None
        if not row or not isinstance(row, dict):
            row = {}
        mode = "none"
        if _script_configured():
            mode = "gmail_script"
        elif _resend_configured():
            mode = "resend"
        elif _smtp_configured():
            mode = "smtp"
        return {
            "from_name": row.get("from_name") or "",
            "from_email": row.get("from_email") or "",
            "reply_to": row.get("reply_to") or "",
            "signature": row.get("signature") or "",
            "smtp_configured": _mail_configured(),
            "mail_mode": mode,
        }

    def _send_gmail_script(to_list, subject, body, from_name="", from_email="", reply_to=""):
        url = (os.environ.get("GMAIL_SCRIPT_URL") or "").strip()
        secret = (os.environ.get("GMAIL_SCRIPT_SECRET") or "").strip()
        if not url or not secret:
            return False, "GMAIL_SCRIPT_URL / GMAIL_SCRIPT_SECRET not set"

        default_reply = (os.environ.get("GMAIL_REPLY_TO") or "").strip()
        rt = reply_to or from_email or default_reply
        name = from_name or (os.environ.get("GMAIL_FROM_NAME") or "CA FirmHub")

        errors = []
        sent_n = 0
        for to in to_list:
            payload = {
                "secret": secret,
                "to": to,
                "subject": subject,
                "body": body,
                "replyTo": rt,
                "fromName": name,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CA-FirmHub/1.0 (Harsh Pala)",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                    try:
                        out = json.loads(raw)
                    except Exception:
                        out = {"ok": True, "raw": raw[:200]}
                    if out.get("ok") is False:
                        errors.append(f"{to}: {out.get('error') or raw[:200]}")
                    else:
                        sent_n += 1
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")[:400]
                errors.append(f"{to}: HTTP {e.code} {err_body}")
            except Exception as e:
                errors.append(f"{to}: {e}")

        if sent_n and not errors:
            return True, "sent"
        if sent_n and errors:
            return True, f"partial: {'; '.join(errors)}"
        return False, "; ".join(errors) if errors else "script send failed"

    def _send_resend(to_list, subject, body, from_name="", from_email="", reply_to=""):
        api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
        if not api_key:
            return False, "RESEND_API_KEY not set"
        resend_from = (os.environ.get("RESEND_FROM") or "").strip()
        if not resend_from:
            name = from_name or "CA FirmHub"
            resend_from = f"{name} <onboarding@resend.dev>"
        elif from_name and "<" not in resend_from:
            resend_from = f"{from_name} <{resend_from}>"

        payload = {
            "from": resend_from,
            "to": to_list,
            "subject": subject,
            "text": body,
        }
        rt = reply_to or from_email
        if rt and "@" in rt:
            payload["reply_to"] = rt

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "CA-FirmHub/1.0 (Harsh Pala)",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    out = json.loads(raw)
                except Exception:
                    out = {}
                if resp.status in (200, 201):
                    return True, out.get("id") or "sent"
                return False, raw[:400]
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
            try:
                ej = json.loads(err_body)
                msg = ej.get("message") or err_body
            except Exception:
                msg = err_body
            return False, f"Resend HTTP {e.code}: {msg}"
        except Exception as e:
            return False, str(e)

    def _send_smtp(to_list, subject, body, from_name="", from_email="", reply_to=""):
        host = (os.environ.get("SMTP_HOST") or "").strip()
        port = int(os.environ.get("SMTP_PORT") or "587")
        user = (os.environ.get("SMTP_USER") or "").strip()
        password = (os.environ.get("SMTP_PASS") or "").strip()
        env_from = (os.environ.get("SMTP_FROM") or user or "").strip()
        use_ssl = (os.environ.get("SMTP_SSL") or "").strip() in ("1", "true", "True", "yes")
        use_tls = os.environ.get("SMTP_TLS", "1") != "0"
        if not host or not env_from:
            return False, "SMTP not configured"
        display_from = f"{from_name} <{env_from}>" if from_name else env_from
        msg = MIMEMultipart()
        msg["From"] = display_from
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = subject
        if reply_to and "@" in reply_to:
            msg["Reply-To"] = reply_to
        elif from_email and "@" in from_email:
            msg["Reply-To"] = from_email
        msg.attach(MIMEText(body, "plain", "utf-8"))

        def _ipv4_host(h, p):
            try:
                infos = socket.getaddrinfo(h, p, socket.AF_INET, socket.SOCK_STREAM)
                if infos:
                    return infos[0][4][0]
            except Exception as ex:
                print("[mail] ipv4 resolve:", ex)
            return h

        target = _ipv4_host(host, port)
        try:
            if use_ssl or port == 465:
                import ssl as _ssl
                context = _ssl.create_default_context()
                server = smtplib.SMTP_SSL(target, port, timeout=30, context=context)
            else:
                server = smtplib.SMTP(target, port, timeout=30)
                if use_tls:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
            if user and password:
                server.login(user, password)
            server.sendmail(env_from, to_list, msg.as_string())
            server.quit()
            return True, "sent"
        except Exception as e:
            return False, str(e)

    def _send(to_list, subject, body, from_name="", from_email="", reply_to=""):
        if isinstance(to_list, str):
            to_list = [a.strip() for a in to_list.split(",") if a.strip()]
        to_list = [a for a in to_list if a and "@" in a]
        if not to_list:
            return False, "No valid recipient addresses"
        if _script_configured():
            return _send_gmail_script(to_list, subject, body, from_name, from_email, reply_to)
        if _resend_configured():
            return _send_resend(to_list, subject, body, from_name, from_email, reply_to)
        if _smtp_configured():
            return _send_smtp(to_list, subject, body, from_name, from_email, reply_to)
        return False, (
            "No mail provider configured. Set GMAIL_SCRIPT_URL + GMAIL_SCRIPT_SECRET "
            "(recommended), or RESEND_API_KEY, or SMTP_*."
        )

    @app.route("/api/mail/settings")
    @login_required
    def mail_settings_get():
        try:
            if not staff_ok():
                return jsonify({"detail": "Staff only"}), 403
            return jsonify(_get_settings(g.firm_id))
        except Exception as e:
            print("[mail] settings_get:", e)
            return jsonify({
                "from_name": "", "from_email": "", "reply_to": "", "signature": "",
                "smtp_configured": _mail_configured(), "mail_mode": "none",
            })

    @app.route("/api/mail/settings", methods=["PUT", "POST"])
    @login_required
    def mail_settings_save():
        try:
            if not admin_ok():
                return jsonify({"detail": "Admin only"}), 403
            _ensure()
            d = request.get_json(silent=True) or {}
            from_name = (d.get("from_name") or "").strip()
            from_email = (d.get("from_email") or "").strip().lower()
            reply_to = (d.get("reply_to") or "").strip().lower()
            signature = (d.get("signature") or "").strip()
            if from_email and "@" not in from_email:
                return jsonify({"detail": "Invalid from email"}), 400
            if reply_to and "@" not in reply_to:
                return jsonify({"detail": "Invalid reply-to email"}), 400
            exists = None
            try:
                exists = qry(
                    "SELECT firm_id FROM firm_mail_settings WHERE firm_id=%s",
                    (g.firm_id,), one=True,
                )
            except Exception:
                _ensure()
                exists = None
            if exists:
                execute(
                    "UPDATE firm_mail_settings SET from_name=%s, from_email=%s, reply_to=%s, "
                    "signature=%s, updated_at=CURRENT_TIMESTAMP WHERE firm_id=%s",
                    (from_name, from_email or None, reply_to or None, signature or None, g.firm_id),
                )
            else:
                execute(
                    "INSERT INTO firm_mail_settings (firm_id, from_name, from_email, reply_to, signature) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (g.firm_id, from_name, from_email or None, reply_to or None, signature or None),
                )
            try:
                log_action(g.firm_id, g.user["id"], "MAIL_SETTINGS_UPDATE")
            except Exception:
                pass
            return jsonify(_get_settings(g.firm_id))
        except Exception as e:
            print("[mail] settings_save:", e)
            return jsonify({"detail": f"Could not save: {e}"}), 500

    @app.route("/api/mail/recipients")
    @login_required
    def mail_recipients():
        try:
            if not staff_ok():
                return jsonify({"detail": "Staff only"}), 403
            _ensure()
            rows = []
            try:
                rows = qry(
                    "SELECT id, name, contact_person, contact_email, contact_phone, entity_type "
                    "FROM clients WHERE firm_id=%s AND COALESCE(is_active, TRUE)=TRUE ORDER BY name",
                    (g.firm_id,),
                ) or []
            except Exception:
                rows = qry(
                    "SELECT id, name, contact_person, contact_email, contact_phone, entity_type "
                    "FROM clients WHERE firm_id=%s ORDER BY name",
                    (g.firm_id,),
                ) or []
            out = []
            for r in rows:
                if not isinstance(r, dict):
                    continue
                em = (r.get("contact_email") or "").strip()
                out.append({
                    "id": r.get("id"),
                    "name": r.get("name") or "",
                    "contact_person": r.get("contact_person") or "",
                    "contact_email": em,
                    "contact_phone": r.get("contact_phone") or "",
                    "entity_type": r.get("entity_type") or "",
                    "has_email": bool(em and "@" in em),
                })
            return jsonify({
                "clients": out,
                "with_email": sum(1 for c in out if c["has_email"]),
                "without_email": sum(1 for c in out if not c["has_email"]),
                "settings": _get_settings(g.firm_id),
            })
        except Exception as e:
            print("[mail] recipients:", e)
            return jsonify({"detail": f"Mail recipients failed: {e}"}), 500

    @app.route("/api/mail/send", methods=["POST"])
    @login_required
    def mail_send():
        try:
            if not staff_ok():
                return jsonify({"detail": "Staff only"}), 403
            d = request.get_json(silent=True) or {}
            subject = (d.get("subject") or "").strip()
            body = (d.get("body") or "").strip()
            client_ids = d.get("client_ids") or []
            if not subject:
                return jsonify({"detail": "Subject is required"}), 400
            if not body:
                return jsonify({"detail": "Message body is required"}), 400
            if not client_ids:
                return jsonify({"detail": "Select at least one client"}), 400
            try:
                client_ids = [int(x) for x in client_ids]
            except Exception:
                return jsonify({"detail": "Invalid client_ids"}), 400

            settings = _get_settings(g.firm_id)
            if settings.get("signature"):
                body = body.rstrip() + "\n\n" + settings["signature"]

            reply_to = (
                settings.get("reply_to")
                or settings.get("from_email")
                or (os.environ.get("GMAIL_REPLY_TO") or "").strip()
                or "harshnpala0@gmail.com"
            )
            from_name = settings.get("from_name") or (os.environ.get("GMAIL_FROM_NAME") or "CA FirmHub")

            placeholders = ",".join(["%s"] * len(client_ids))
            rows = qry(
                f"SELECT id, name, contact_email FROM clients "
                f"WHERE firm_id=%s AND id IN ({placeholders})",
                tuple([g.firm_id] + client_ids),
            ) or []

            sent, skipped, errors = [], [], []
            for r in rows:
                em = (r.get("contact_email") or "").strip()
                if not em or "@" not in em:
                    skipped.append({"id": r["id"], "name": r["name"], "reason": "No contact email"})
                    continue
                text = body.replace("{{client_name}}", r["name"] or "")
                text = text.replace("{{name}}", r["name"] or "")
                ok, info = _send(
                    [em], subject, text,
                    from_name=from_name,
                    from_email=settings.get("from_email") or "",
                    reply_to=reply_to,
                )
                if ok:
                    sent.append({"id": r["id"], "name": r["name"], "email": em})
                else:
                    errors.append({"id": r["id"], "name": r["name"], "email": em, "error": info})

            try:
                log_action(
                    g.firm_id, g.user["id"], "MAIL_SEND",
                    details=f"sent={len(sent)} skipped={len(skipped)} errors={len(errors)} subj={subject[:80]}",
                )
            except Exception:
                pass

            status = 200 if sent and not errors else (207 if sent else 400)
            return jsonify({
                "sent_count": len(sent),
                "skipped_count": len(skipped),
                "error_count": len(errors),
                "sent": sent,
                "skipped": skipped,
                "errors": errors,
                "smtp_configured": _mail_configured(),
                "mail_mode": settings.get("mail_mode"),
                "detail": (
                    f"Sent {len(sent)}"
                    + (f", skipped {len(skipped)}" if skipped else "")
                    + (f", failed {len(errors)}" if errors else "")
                ),
            }), status
        except Exception as e:
            print("[mail] send:", e)
            return jsonify({"detail": f"Send failed: {e}"}), 500

    print("[mail] Client mail module registered (Gmail Script + Resend + SMTP)")
