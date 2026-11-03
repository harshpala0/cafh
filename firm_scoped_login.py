"""Firm-scoped login lock — Designed & Built by Harsh Pala."""
from datetime import datetime, timedelta
from flask import request, jsonify
import jwt
import os

def register_firm_scoped_login(app, helpers):
    qry = helpers["qry"]
    SECRET_KEY = helpers.get("SECRET_KEY") or os.environ.get("SECRET_KEY", "cafirmhub-secret")

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

    def login_firm_scoped():
        d = request.get_json(silent=True) or {}
        username = (d.get("username") or "").strip()
        password = d.get("password") or ""
        firm_token = (d.get("subscription_token") or "").strip()

        if not username or not password:
            return jsonify({"detail": "Username and password required"}), 400
        if not firm_token:
            return jsonify({
                "detail": "Subscription not verified. "
                          "Enter your firm subscription email first, then sign in."
            }), 401
        try:
            payload = jwt.decode(firm_token, SECRET_KEY, algorithms=["HS256"])
            firm_id = payload.get("firm_id")
        except Exception:
            return jsonify({
                "detail": "Subscription session invalid or expired. "
                          "Please re-enter your subscription email on the first screen."
            }), 401

        firm = qry("SELECT * FROM firms WHERE id=%s AND is_active=TRUE", (firm_id,), one=True)
        if not firm:
            return jsonify({"detail": "Firm account is inactive"}), 403
        reason = _check_expiry(firm)
        if reason:
            return jsonify({"detail": reason}), 403

        # STRICT: only users of THIS firm — never search other firms
        user = qry(
            "SELECT * FROM users WHERE firm_id=%s AND username=%s",
            (firm_id, username), one=True,
        )
        if not user:
            return jsonify({
                "detail": "Invalid credentials for this firm. "
                          "Username/password must belong to the firm linked to your subscription email."
            }), 401

        check_pw = helpers.get("check_pw")
        if check_pw:
            ok = check_pw(password, user["password_hash"])
        else:
            from werkzeug.security import check_password_hash
            ok = check_password_hash(user["password_hash"], password)
        if not ok:
            return jsonify({
                "detail": "Invalid credentials for this firm. "
                          "Username/password must belong to the firm linked to your subscription email."
            }), 401
        if not user.get("is_active", True):
            return jsonify({"detail": "Account deactivated"}), 403

        make_token = helpers.get("make_token")
        if make_token:
            token = make_token(user["id"], user["firm_id"], user["role"])
        else:
            token = jwt.encode(
                {
                    "sub": str(user["id"]),
                    "firm": user["firm_id"],
                    "role": user["role"],
                    "exp": datetime.utcnow() + timedelta(hours=12),
                },
                SECRET_KEY,
                algorithm="HS256",
            )
        try:
            log_action = helpers.get("log_action")
            if log_action:
                log_action(user["firm_id"], user["id"], "LOGIN", ip=request.remote_addr)
        except Exception:
            pass

        return jsonify({
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "role": user["role"],
                "is_active": user.get("is_active", True),
                "client_id": user.get("client_id"),
                "firm_id": user["firm_id"],
                "can_switch_fy": user.get("can_switch_fy", False),
            },
            "firm": {
                "name": firm["name"],
                "reg_no": firm.get("reg_no") or "",
                "owner_email": firm.get("owner_email") or "",
            },
        })

    app.view_functions["login"] = login_firm_scoped
    print("[sub-email] Firm-scoped login locked")
