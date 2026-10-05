"""
CA FirmHub — Cron + system health (additive).
- Secured daily digest cron for Render Cron Jobs / external schedulers
- Module health endpoint
"""
import os
import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from flask import request, jsonify, g


def register_cron_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    login_required = helpers["login_required"]
    require_role = helpers["require_role"]
    log_action = helpers.get("log_action", lambda *a, **k: None)

    def j():
        return request.get_json(silent=True) or {}

    def _cron_secret_ok():
        secret = os.environ.get("CRON_SECRET", "")
        if not secret:
            return False
        h = request.headers.get("X-Cron-Secret") or request.headers.get("Authorization", "").replace("Bearer ", "")
        q = request.args.get("secret") or ""
        body = j().get("secret") if request.method == "POST" else ""
        return secret and secret in (h, q, body)

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
            "ORDER BY due_date LIMIT 40",
            (firm_id, week.isoformat())) or []
        docs = qry(
            "SELECT r.title, r.status, c.name as client_name FROM portal_doc_requests r "
            "JOIN clients c ON r.client_id=c.id "
            "WHERE r.firm_id=%s AND r.status IN ('Open','Submitted') LIMIT 30",
            (firm_id,)) or []
        fees = qry(
            "SELECT i.invoice_no, i.total_amount, c.name as client_name FROM invoices i "
            "JOIN clients c ON i.client_id=c.id "
            "WHERE i.firm_id=%s AND i.payment_status IN ('Unpaid','Partial') LIMIT 30",
            (firm_id,)) or []
        firm = qry("SELECT id, name FROM firms WHERE id=%s", (firm_id,), one=True) or {}
        lines = [
            f"CA FirmHub digest — {firm.get('name') or 'Firm'} — {today.isoformat()}",
            "",
            f"COMPLIANCE ({len(compliance)})",
        ]
        for c in compliance:
            lines.append(f"  • [{c.get('status')}] {c.get('due_date')} — {c.get('title')}")
        lines += ["", f"DOC REQUESTS ({len(docs)})"]
        for d in docs:
            lines.append(f"  • [{d.get('status')}] {d.get('client_name')}: {d.get('title')}")
        lines += ["", f"OUTSTANDING FEES ({len(fees)})"]
        for f in fees:
            lines.append(f"  • {f.get('client_name')}: {f.get('invoice_no')} — ₹{f.get('total_amount')}")
        return {
            "text": "\n".join(lines),
            "counts": {
                "compliance": len(compliance),
                "docs": len(docs),
                "fees": len(fees),
                "total": len(compliance) + len(docs) + len(fees),
            },
            "firm_name": firm.get("name"),
        }

    def _send_email(to_addrs, subject, body):
        host = os.environ.get("SMTP_HOST", "")
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ.get("SMTP_USER", "")
        password = os.environ.get("SMTP_PASS", "")
        from_addr = os.environ.get("SMTP_FROM") or user
        if not host or not from_addr:
            return False, "SMTP not configured"
        if isinstance(to_addrs, str):
            to_addrs = [a.strip() for a in to_addrs.split(",") if a.strip()]
        if not to_addrs:
            return False, "no recipients"
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        try:
            server = smtplib.SMTP(host, port, timeout=30)
            if os.environ.get("SMTP_TLS", "1") != "0":
                server.starttls()
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
            return False, "WhatsApp webhook not configured"
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

    def _admin_emails(firm_id):
        rows = qry(
            "SELECT email FROM users WHERE firm_id=%s AND role IN ('Admin','Team Leader') "
            "AND is_active=TRUE AND email IS NOT NULL AND email <> ''",
            (firm_id,)) or []
        return [r["email"] for r in rows if r.get("email")]

    @app.route("/api/ops/notify/cron", methods=["GET", "POST"])
    def notify_cron():
        if not os.environ.get("CRON_SECRET"):
            return jsonify({"detail": "Set CRON_SECRET env to enable cron"}), 503
        if not _cron_secret_ok():
            return jsonify({"detail": "Unauthorized"}), 401

        channel = (request.args.get("channel") or j().get("channel") or "email").lower()
        only_firm = request.args.get("firm_id") or j().get("firm_id")
        firms = qry("SELECT id, name FROM firms WHERE is_active=TRUE") or []
        if only_firm:
            firms = [f for f in firms if str(f["id"]) == str(only_firm)]

        results = []
        for firm in firms:
            fid = firm["id"]
            digest = _build_digest(fid)
            if digest["counts"]["total"] == 0 and os.environ.get("CRON_FORCE", "") != "1":
                results.append({"firm_id": fid, "name": firm["name"], "skipped": True, "reason": "nothing due"})
                continue

            entry = {"firm_id": fid, "name": firm["name"], "counts": digest["counts"]}
            if channel in ("email", "both"):
                to = os.environ.get("DIGEST_EMAIL_TO") or ",".join(_admin_emails(fid))
                ok, info = _send_email(
                    to,
                    f"CA FirmHub digest — {firm['name']} — {date.today().isoformat()}",
                    digest["text"],
                )
                entry["email"] = {"ok": ok, "info": info, "to": to}
                try:
                    log_action(fid, None, "CRON_EMAIL", "Notify", None, details=str(info)[:200])
                except Exception:
                    pass
            if channel in ("whatsapp", "both"):
                phone = os.environ.get("DIGEST_WHATSAPP_TO", "")
                if phone:
                    ok, info = _send_whatsapp(phone, digest["text"])
                    entry["whatsapp"] = {"ok": ok, "info": info}
                else:
                    entry["whatsapp"] = {"ok": False, "info": "DIGEST_WHATSAPP_TO not set"}
            results.append(entry)

        return jsonify({
            "ok": True,
            "ran_at": datetime.utcnow().isoformat() + "Z",
            "channel": channel,
            "results": results,
        })

    @app.route("/api/ops/health")
    def ops_health():
        import sys
        modules = {
            "portal": "portal" in sys.modules or "portal" in str(app.view_functions),
            "compliance": any("compliance" in r.rule for r in app.url_map.iter_rules()),
            "ops": any("/api/ops/" in r.rule for r in app.url_map.iter_rules()),
            "notify": any("notify" in r.rule for r in app.url_map.iter_rules()),
            "cron": any("cron" in r.rule for r in app.url_map.iter_rules()),
        }
        routes = sorted({r.rule for r in app.url_map.iter_rules() if r.rule.startswith("/api/ops")})
        return jsonify({
            "status": "ok",
            "time": datetime.utcnow().isoformat() + "Z",
            "modules": modules,
            "ops_routes": routes,
            "cron_enabled": bool(os.environ.get("CRON_SECRET")),
            "smtp_configured": bool(os.environ.get("SMTP_HOST")),
            "whatsapp_configured": bool(os.environ.get("WHATSAPP_WEBHOOK_URL")),
        })

    @app.route("/api/ops/notify/cron-help")
    @login_required
    def cron_help():
        if g.user.get("role") not in ("Admin", "Team Leader"):
            return jsonify({"detail": "Admin only"}), 403
        base = request.host_url.rstrip("/")
        secret = os.environ.get("CRON_SECRET")
        return jsonify({
            "enabled": bool(secret),
            "example_curl": (
                f'curl -X POST "{base}/api/ops/notify/cron?channel=email" '
                f'-H "X-Cron-Secret: YOUR_SECRET"'
            ),
            "render_cron": {
                "schedule": "0 3 * * *",
                "note": "03:00 UTC daily — adjust for IST (use 21:30 UTC for 3:00 AM IST)",
                "url": f"{base}/api/ops/notify/cron?channel=both",
                "header": "X-Cron-Secret: <CRON_SECRET>",
            },
        })

    print("[cron] Cron + health routes registered")
