"""CA FirmHub — Client mail (SMTP). Designed & Built by Harsh Pala.

Admin stores from-name / from-email for the firm.
Staff select clients; mail goes to contact_email on client records.
SMTP transport uses env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TLS.
"""
import os
import smtplib
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
                """
                CREATE TABLE IF NOT EXISTS firm_mail_settings (
                    firm_id INTEGER PRIMARY KEY,
                    from_name TEXT,
                    from_email TEXT,
                    reply_to TEXT,
                    signature TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        except Exception as e:
            print("[mail] ensure:", e)

    try:
        _ensure()
    except Exception as e:
        print("[mail] ensure fail:", e)

    def staff_ok():
        return g.user.get("role") in ("Admin", "TeamLeader", "Member", "SuperAdmin")

    def admin_ok():
        return g.user.get("role") in ("Admin", "SuperAdmin")

    def _smtp_configured():
        return bool(os.environ.get("SMTP_HOST") and (
            os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER")
        ))

    def _get_settings(firm_id):
        row = qry(
            "SELECT * FROM firm_mail_settings WHERE firm_id=%s",
            (firm_id,), one=True,
        ) or {}
        return {
            "from_name": row.get("from_name") or "",
            "from_email": row.get("from_email") or "",
            "reply_to": row.get("reply_to") or "",
            "signature": row.get("signature") or "",
            "smtp_configured": _smtp_configured(),
        }

    def _send(to_list, subject, body, from_name="", from_email="", reply_to=""):
        host = os.environ.get("SMTP_HOST", "")
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ.get("SMTP_USER", "")
        password = os.environ.get("SMTP_PASS", "")
        env_from = os.environ.get("SMTP_FROM") or user
        use_tls = os.environ.get("SMTP_TLS", "1") != "0"
        if not host or not env_from:
            return False, "SMTP not configured on server (SMTP_HOST / SMTP_FROM)"
        if isinstance(to_list, str):
            to_list = [a.strip() for a in to_list.split(",") if a.strip()]
        to_list = [a for a in to_list if a and "@" in a]
        if not to_list:
            return False, "No valid recipient addresses"
        display_from = env_from
        if from_name:
            display_from = f"{from_name} <{env_from}>"
        msg = MIMEMultipart()
        msg["From"] = display_from
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = subject
        if reply_to and "@" in reply_to:
            msg["Reply-To"] = reply_to
        elif from_email and "@" in from_email:
            msg["Reply-To"] = from_email
        msg.attach(MIMEText(body, "plain", "utf-8"))
        try:
            if use_tls:
                server = smtplib.SMTP(host, port, timeout=45)
                server.starttls()
            else:
                server = smtplib.SMTP(host, port, timeout=45)
            if user and password:
                server.login(user, password)
            server.sendmail(env_from, to_list, msg.as_string())
            server.quit()
            return True, "sent"
        except Exception as e:
            return False, str(e)

    @app.route("/api/mail/settings")
    @login_required
    def mail_settings_get():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        return jsonify(_get_settings(g.firm_id))

    @app.route("/api/mail/settings", methods=["PUT", "POST"])
    @login_required
    def mail_settings_save():
        if not admin_ok():
            return jsonify({"detail": "Admin only"}), 403
        d = request.get_json(silent=True) or {}
        from_name = (d.get("from_name") or "").strip()
        from_email = (d.get("from_email") or "").strip().lower()
        reply_to = (d.get("reply_to") or "").strip().lower()
        signature = (d.get("signature") or "").strip()
        if from_email and "@" not in from_email:
            return jsonify({"detail": "Invalid from email"}), 400
        if reply_to and "@" not in reply_to:
            return jsonify({"detail": "Invalid reply-to email"}), 400
        exists = qry(
            "SELECT firm_id FROM firm_mail_settings WHERE firm_id=%s",
            (g.firm_id,), one=True,
        )
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

    @app.route("/api/mail/recipients")
    @login_required
    def mail_recipients():
        if not staff_ok():
            return jsonify({"detail": "Staff only"}), 403
        rows = qry(
            "SELECT id, name, contact_person, contact_email, contact_phone, entity_type "
            "FROM clients WHERE firm_id=%s AND is_active=TRUE ORDER BY name",
            (g.firm_id,),
        ) or []
        out = []
        for r in rows:
            em = (r.get("contact_email") or "").strip()
            out.append({
                "id": r["id"],
                "name": r["name"],
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

    @app.route("/api/mail/send", methods=["POST"])
    @login_required
    def mail_send():
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
                [em],
                subject,
                text,
                from_name=settings.get("from_name") or "",
                from_email=settings.get("from_email") or "",
                reply_to=settings.get("reply_to") or settings.get("from_email") or "",
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
            "smtp_configured": _smtp_configured(),
            "detail": (
                f"Sent {len(sent)}"
                + (f", skipped {len(skipped)}" if skipped else "")
                + (f", failed {len(errors)}" if errors else "")
            ),
        }), status

    print("[mail] Client mail module registered")
