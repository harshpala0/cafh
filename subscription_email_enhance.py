"""CA FirmHub — email-based subscription gate.
Designed & Built by Harsh Pala.

Subscription remains time-based (expires_at).
Gate uses owner email instead of requiring Subscription ID every time.
Email unlocks the firm only; username/password stay firm-scoped.
"""
from datetime import datetime, timedelta
from flask import request, jsonify, g
import jwt
import os
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register_subscription_email_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    superadmin_required = helpers.get("superadmin_required")
    SECRET_KEY = helpers.get("SECRET_KEY") or os.environ.get("SECRET_KEY", "cafirmhub-secret")

    def _ensure():
        try:
            execute("ALTER TABLE firms ADD COLUMN IF NOT EXISTS owner_email TEXT")
        except Exception:
            try:
                cols = qry(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='firms'"
                ) or []
                names = {str(r.get("column_name") or "").lower() for r in cols}
                if "owner_email" not in names:
                    execute("ALTER TABLE firms ADD COLUMN owner_email TEXT")
            except Exception as e:
                print("[sub-email] owner_email col:", e)
        try:
            execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_firms_owner_email_lower "
                "ON firms (LOWER(owner_email)) WHERE owner_email IS NOT NULL AND owner_email <> ''"
            )
        except Exception as e:
            print("[sub-email] unique index:", e)

    try:
        _ensure()
    except Exception as e:
        print("[sub-email] ensure:", e)

    def _norm_email(e):
        return (e or "").strip().lower()

    def _firm_from_email(email):
        em = _norm_email(email)
        if not em or not EMAIL_RE.match(em):
            return None
        return qry(
            "SELECT * FROM firms WHERE LOWER(TRIM(owner_email))=%s AND is_active=TRUE",
            (em,), one=True,
        )

    def _firm_from_sub(sub_id):
        sid = (sub_id or "").strip()
        if not sid:
            return None
        return qry("SELECT * FROM firms WHERE sub_id=%s AND is_active=TRUE", (sid,), one=True)

    def _issue_token(firm):
        token = jwt.encode(
            {
                "sub_verified": True,
                "firm_id": firm["id"],
                "owner_email": (firm.get("owner_email") or ""),
                "exp": datetime.utcnow() + timedelta(days=365),
            },
            SECRET_KEY,
            algorithm="HS256",
        )
        try:
            execute("UPDATE firms SET activated=TRUE WHERE id=%s", (firm["id"],))
        except Exception:
            pass
        return token

    def _check_expiry(firm):
        exp = firm.get("expires_at")
        if not exp:
            return None
        if hasattr(exp, "isoformat"):
            d = exp
        else:
            try:
                d = datetime.strptime(str(exp)[:10], "%Y-%m-%d").date()
            except Exception:
                return None
        if datetime.now().date() > d:
            return f"Subscription expired on {d}"
        return None

    @app.route("/api/subscription/verify", methods=["POST"])
    def subscription_verify_email():
        """Accept email (preferred) or subscription_id. Time-based expiry unchanged."""
        d = request.get_json(silent=True) or {}
        email = _norm_email(d.get("email") or d.get("owner_email") or "")
        sub_id = str(d.get("subscription_id") or d.get("sub_id") or "").strip()

        firm = None
        if email:
            if not EMAIL_RE.match(email):
                return jsonify({"detail": "Enter a valid email address"}), 400
            firm = _firm_from_email(email)
            if not firm:
                return jsonify({
                    "detail": "No active subscription found for this email. "
                              "Use the email registered with your firm subscription."
                }), 403
        elif sub_id:
            firm = _firm_from_sub(sub_id)
            if not firm:
                return jsonify({"detail": "Invalid or inactive Subscription ID"}), 403
        else:
            return jsonify({"detail": "Email or Subscription ID required"}), 400

        reason = _check_expiry(firm)
        if reason:
            return jsonify({"detail": reason}), 403

        token = _issue_token(firm)
        return jsonify({
            "subscription_token": token,
            "firm_name": firm["name"],
            "firm_reg_no": firm.get("reg_no") or "",
            "owner_email": firm.get("owner_email") or email or "",
            "activated": True,
            "expires_at": str(firm["expires_at"])[:10] if firm.get("expires_at") else None,
        })

    @app.route("/api/subscription/check", methods=["POST"])
    def subscription_check_email():
        d = request.get_json(silent=True) or {}
        token = str(d.get("subscription_token") or "").strip()
        if not token:
            return jsonify({"valid": False})
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            firm = qry(
                "SELECT * FROM firms WHERE id=%s AND is_active=TRUE",
                (payload.get("firm_id"),), one=True,
            )
            if not firm:
                return jsonify({"valid": False})
            if _check_expiry(firm):
                return jsonify({"valid": False, "reason": "expired"})
            return jsonify({
                "valid": True,
                "firm_name": firm["name"],
                "owner_email": firm.get("owner_email") or "",
            })
        except Exception:
            return jsonify({"valid": False})

    if superadmin_required:
        _orig_create = app.view_functions.get("sa_create_firm")
        _orig_update = app.view_functions.get("sa_update_firm")

        @superadmin_required
        def sa_create_firm_email():
            d = request.get_json(silent=True) or {}
            email = _norm_email(d.get("owner_email") or d.get("email") or "")
            if email and not EMAIL_RE.match(email):
                return jsonify({"detail": "Invalid owner email"}), 400
            if email:
                exists = qry(
                    "SELECT id, name FROM firms WHERE LOWER(TRIM(owner_email))=%s",
                    (email,), one=True,
                )
                if exists:
                    return jsonify({
                        "detail": f"Email already linked to firm '{exists.get('name')}' (id {exists['id']})"
                    }), 400
            if _orig_create:
                resp = _orig_create()
                if email and hasattr(resp, "status_code") and resp.status_code in (200, 201):
                    try:
                        data = resp.get_json() or {}
                        fid = data.get("id")
                        if fid:
                            execute("UPDATE firms SET owner_email=%s WHERE id=%s", (email, fid))
                            data["owner_email"] = email
                            return jsonify(data), resp.status_code
                    except Exception as e:
                        print("[sub-email] attach email:", e)
                return resp
            return jsonify({"detail": "Create firm unavailable"}), 500

        @superadmin_required
        def sa_update_firm_email(fid):
            d = request.get_json(silent=True) or {}
            if "owner_email" in d or "email" in d:
                email = _norm_email(d.get("owner_email") if "owner_email" in d else d.get("email"))
                if email and not EMAIL_RE.match(email):
                    return jsonify({"detail": "Invalid owner email"}), 400
                if email:
                    exists = qry(
                        "SELECT id, name FROM firms WHERE LOWER(TRIM(owner_email))=%s AND id<>%s",
                        (email, fid), one=True,
                    )
                    if exists:
                        return jsonify({
                            "detail": f"Email already linked to firm '{exists.get('name')}'"
                        }), 400
                try:
                    execute("UPDATE firms SET owner_email=%s WHERE id=%s", (email or None, fid))
                except Exception as e:
                    return jsonify({"detail": str(e)}), 500
            if _orig_update:
                return _orig_update(fid)
            return jsonify(qry("SELECT * FROM firms WHERE id=%s", (fid,), one=True))

        app.view_functions["sa_create_firm"] = sa_create_firm_email
        app.view_functions["sa_update_firm"] = sa_update_firm_email

    print("[sub-email] Email-based subscription gate registered")
