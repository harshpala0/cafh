"""CA FirmHub — email-based subscription gate.
Designed & Built by Harsh Pala.

Subscription remains time-based (expires_at).
Gate uses owner email instead of requiring Subscription ID every time.
Email unlocks the firm only; username/password stay firm-scoped.
"""
from datetime import datetime, timedelta
from flask import request, jsonify
import jwt
import os
import re
import uuid

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register_subscription_email_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    qry_id = helpers.get("qry_id")
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

    def _parse_date(val):
        if not val:
            return None
        s = str(val).strip()
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(s[:10], fmt).date().isoformat()
            except Exception:
                continue
        if hasattr(val, "isoformat"):
            return val.isoformat()
        return s[:10]

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

    def subscription_verify_email():
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

    app.view_functions["subscription_verify"] = subscription_verify_email
    app.view_functions["subscription_check"] = subscription_check_email

    def _create_firm_core():
        _ensure()
        d = request.get_json(silent=True) or {}
        name = (d.get("name") or "").strip()
        reg_no = (d.get("reg_no") or "").strip()
        expires = _parse_date(d.get("expires_at"))
        email = _norm_email(d.get("owner_email") or d.get("email") or "")

        if not name:
            return jsonify({"detail": "Firm name required"}), 400
        if email and not EMAIL_RE.match(email):
            return jsonify({"detail": "Invalid subscription email"}), 400
        if email:
            exists = qry(
                "SELECT id, name FROM firms WHERE LOWER(TRIM(owner_email))=%s",
                (email,), one=True,
            )
            if exists:
                return jsonify({
                    "detail": f"Email already linked to firm '{exists.get('name')}' (id {exists['id']}). "
                              f"Use a different email or edit that firm."
                }), 400

        sub_id = "SUB-" + uuid.uuid4().hex[:12].upper()
        fid = None
        try:
            if qry_id:
                fid = qry_id(
                    "INSERT INTO firms (name,reg_no,sub_id,is_active,expires_at,owner_email) "
                    "VALUES (%s,%s,%s,TRUE,%s,%s)",
                    (name, reg_no, sub_id, expires, email or None),
                )
            else:
                execute(
                    "INSERT INTO firms (name,reg_no,sub_id,is_active,expires_at,owner_email) "
                    "VALUES (%s,%s,%s,TRUE,%s,%s)",
                    (name, reg_no, sub_id, expires, email or None),
                )
                row = qry("SELECT id FROM firms WHERE sub_id=%s", (sub_id,), one=True)
                fid = row["id"] if row else None
        except Exception as e:
            msg = str(e)
            if "owner_email" in msg.lower():
                try:
                    if qry_id:
                        fid = qry_id(
                            "INSERT INTO firms (name,reg_no,sub_id,is_active,expires_at) "
                            "VALUES (%s,%s,%s,TRUE,%s)",
                            (name, reg_no, sub_id, expires),
                        )
                    else:
                        execute(
                            "INSERT INTO firms (name,reg_no,sub_id,is_active,expires_at) "
                            "VALUES (%s,%s,%s,TRUE,%s)",
                            (name, reg_no, sub_id, expires),
                        )
                        row = qry("SELECT id FROM firms WHERE sub_id=%s", (sub_id,), one=True)
                        fid = row["id"] if row else None
                    if fid and email:
                        try:
                            execute("UPDATE firms SET owner_email=%s WHERE id=%s", (email, fid))
                        except Exception as e2:
                            return jsonify({"detail": f"Firm created but email not saved: {e2}"}), 500
                except Exception as e3:
                    return jsonify({"detail": f"Could not create firm: {e3}"}), 500
            else:
                return jsonify({"detail": f"Could not create firm: {msg}"}), 500

        programs_seeded = 0
        try:
            seed = helpers.get("seed_all_templates_to_firm")
            if seed and fid:
                programs_seeded = seed(fid) or 0
        except Exception as e:
            print("[sub-email] seed:", e)

        return jsonify({
            "id": fid,
            "name": name,
            "sub_id": sub_id,
            "reg_no": reg_no,
            "expires_at": expires,
            "owner_email": email or "",
            "programs_seeded": programs_seeded,
        }), 201

    def _update_firm_core(fid):
        _ensure()
        d = request.get_json(silent=True) or {}
        fields, vals = [], []
        for col in ["name", "reg_no", "is_active"]:
            if col in d:
                fields.append(f"{col}=%s")
                vals.append(d[col])
        if "expires_at" in d:
            fields.append("expires_at=%s")
            vals.append(_parse_date(d.get("expires_at")))
        if "owner_email" in d or "email" in d:
            email = _norm_email(d.get("owner_email") if "owner_email" in d else d.get("email"))
            if email and not EMAIL_RE.match(email):
                return jsonify({"detail": "Invalid subscription email"}), 400
            if email:
                exists = qry(
                    "SELECT id, name FROM firms WHERE LOWER(TRIM(owner_email))=%s AND id<>%s",
                    (email, fid), one=True,
                )
                if exists:
                    return jsonify({
                        "detail": f"Email already linked to firm '{exists.get('name')}'"
                    }), 400
            fields.append("owner_email=%s")
            vals.append(email or None)
        if not fields:
            return jsonify({"detail": "Nothing to update"}), 400
        vals.append(fid)
        try:
            execute(f"UPDATE firms SET {','.join(fields)} WHERE id=%s", vals)
        except Exception as e:
            return jsonify({"detail": f"Update failed: {e}"}), 500
        row = qry("SELECT * FROM firms WHERE id=%s", (fid,), one=True)
        return jsonify(row)

    if superadmin_required:
        app.view_functions["sa_create_firm"] = superadmin_required(_create_firm_core)
        app.view_functions["sa_update_firm"] = superadmin_required(_update_firm_core)
    else:
        print("[sub-email] WARNING: superadmin_required not found")
        app.view_functions["sa_create_firm"] = _create_firm_core
        app.view_functions["sa_update_firm"] = _update_firm_core

    print("[sub-email] Email-based subscription gate registered")
