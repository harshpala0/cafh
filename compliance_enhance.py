"""CA FirmHub compliance enhance.
Designed & Built by Harsh Pala.
Separate ITR / TAX_AUDIT packs; correct statutory due dates; CBDT/ICAI overrides.
"""
from datetime import date, timedelta
from flask import request, jsonify, g


def register_compliance_enhance(app, helpers):
    qry, execute = helpers["qry"], helpers["execute"]
    login_required, require_role = helpers["login_required"], helpers["require_role"]

    def _col_names(table):
        try:
            rows = qry(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                (table,),
            ) or []
            return {str(r.get("column_name") or r.get("COLUMN_NAME") or "").lower() for r in rows}
        except Exception:
            return set()

    def _ensure():
        cols = _col_names("compliance_calendar")
        if cols:
            if "client_id" not in cols:
                try:
                    execute("ALTER TABLE compliance_calendar ADD COLUMN client_id INTEGER")
                except Exception as e:
                    print("[compliance] add client_id:", e)
            if "source" not in cols:
                try:
                    execute("ALTER TABLE compliance_calendar ADD COLUMN source TEXT DEFAULT 'manual'")
                except Exception as e:
                    print("[compliance] add source:", e)
        else:
            for sql in (
                "ALTER TABLE compliance_calendar ADD COLUMN IF NOT EXISTS client_id INTEGER",
                "ALTER TABLE compliance_calendar ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual'",
            ):
                try:
                    execute(sql)
                except Exception as e:
                    print("[compliance]", e)
        ccols = _col_names("clients")
        if ccols and "compliance_packs" not in ccols:
            try:
                execute("ALTER TABLE clients ADD COLUMN compliance_packs TEXT DEFAULT ''")
            except Exception as e:
                print("[compliance] add compliance_packs:", e)
        else:
            try:
                execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS compliance_packs TEXT DEFAULT ''")
            except Exception as e:
                print("[compliance] compliance_packs:", e)
        try:
            execute("CREATE INDEX IF NOT EXISTS idx_comp_client ON compliance_calendar(client_id)")
        except Exception:
            pass

    try:
        _ensure()
    except Exception as e:
        print("[compliance] ensure:", e)

    def _parse_fy(fy):
        fy = (fy or "").strip()
        parts = fy.replace("/", "-").split("-")
        if not parts or not parts[0].isdigit():
            raise ValueError("bad fy")
        sy = int(parts[0])
        if len(parts) > 1 and parts[1].isdigit():
            ey = int(parts[1])
            if ey < 100:
                ey = sy // 100 * 100 + ey if ey > (sy % 100) else (sy // 100 + 1) * 100 + ey
            if ey == sy:
                ey = sy + 1
        else:
            ey = sy + 1
        return sy, ey

    ALLOWED_PACKS = ("GST_MONTHLY", "GST_QRMP", "TDS", "ITR", "TAX_AUDIT", "ROC", "PF_ESI")

    def _ensure_overrides():
        try:
            execute(
                """CREATE TABLE IF NOT EXISTS compliance_due_overrides (
                    id SERIAL PRIMARY KEY,
                    financial_year TEXT NOT NULL,
                    event_key TEXT NOT NULL,
                    due_date DATE NOT NULL,
                    notification_ref TEXT DEFAULT '',
                    source TEXT DEFAULT 'CBDT',
                    notes TEXT DEFAULT '',
                    firm_id INTEGER,
                    updated_at TIMESTAMP DEFAULT NOW()
                )"""
            )
        except Exception as e:
            print("[compliance] overrides table:", e)

    def _default_event_dates(sy, ey):
        return {
            "ITR_NON_AUDIT": f"{ey}-07-31",
            "TAX_AUDIT_REPORT": f"{ey}-09-30",
            "ITR_AUDIT": f"{ey}-10-31",
            "ITR_COMPANY": f"{ey}-10-31",
            "ADV_TAX_Q1": f"{sy}-06-15",
            "ADV_TAX_Q2": f"{sy}-09-15",
            "ADV_TAX_Q3": f"{sy}-12-15",
            "ADV_TAX_Q4": f"{ey}-03-15",
            "TDS_Q1": f"{sy}-07-31",
            "TDS_Q2": f"{sy}-10-31",
            "TDS_Q3": f"{ey}-01-31",
            "TDS_Q4": f"{ey}-05-31",
            "FORM_16": f"{ey}-06-15",
            "GSTR9": f"{ey}-12-31",
            "AGM": f"{ey}-09-30",
            "AOC4": f"{ey}-10-29",
            "MGT7": f"{ey}-11-29",
        }

    def _resolve_due(fy, event_key, sy, ey, firm_id=None):
        defaults = _default_event_dates(sy, ey)
        base = defaults.get(event_key)
        if not base:
            return None
        try:
            _ensure_overrides()
            row = None
            if firm_id is not None:
                row = qry(
                    "SELECT due_date FROM compliance_due_overrides "
                    "WHERE financial_year=%s AND event_key=%s AND firm_id=%s ORDER BY id DESC LIMIT 1",
                    (fy, event_key, firm_id), one=True,
                )
            if not row:
                row = qry(
                    "SELECT due_date FROM compliance_due_overrides "
                    "WHERE financial_year=%s AND event_key=%s AND firm_id IS NULL ORDER BY id DESC LIMIT 1",
                    (fy, event_key), one=True,
                )
            if row and row.get("due_date"):
                d = row["due_date"]
                return d.isoformat() if hasattr(d, "isoformat") else str(d)[:10]
        except Exception as e:
            print("[compliance] resolve_due:", e)
        return base

    def _firm_deadlines(sy, ey, fy=None, firm_id=None):
        fy = fy or f"{sy}-{str(ey)[-2:]}"
        items = []
        for y, m in [(sy, m) for m in range(4, 13)] + [(ey, m) for m in range(1, 4)]:
            dy, dm = (y + 1, 1) if m == 12 else (y, m + 1)
            mon = date(y, m, 1).strftime("%b %Y")
            items.append((f"GSTR-1 — {mon}", "GST", date(dy, dm, 11).isoformat()))
            items.append((f"GSTR-3B — {mon}", "GST", date(dy, dm, 20).isoformat()))
        R = lambda k: _resolve_due(fy, k, sy, ey, firm_id)
        items += [
            ("GSTR-9 Annual Return", "GST", R("GSTR9")),
            ("TDS Return Q1", "TDS", R("TDS_Q1")),
            ("TDS Return Q2", "TDS", R("TDS_Q2")),
            ("TDS Return Q3", "TDS", R("TDS_Q3")),
            ("TDS Return Q4", "TDS", R("TDS_Q4")),
            ("Form 16 / 16A", "TDS", R("FORM_16")),
            ("Advance Tax 15 Jun", "ITR", R("ADV_TAX_Q1")),
            ("Advance Tax 15 Sep", "ITR", R("ADV_TAX_Q2")),
            ("Advance Tax 15 Dec", "ITR", R("ADV_TAX_Q3")),
            ("Advance Tax 15 Mar", "ITR", R("ADV_TAX_Q4")),
            ("ITR filing (non-audit)", "ITR", R("ITR_NON_AUDIT")),
            ("Tax audit report u/s 44AB", "Tax Audit", R("TAX_AUDIT_REPORT")),
            ("ITR filing (tax audit / company)", "ITR", R("ITR_AUDIT")),
            ("AGM deadline", "ROC", R("AGM")),
            ("AOC-4", "ROC", R("AOC4")),
            ("MGT-7", "ROC", R("MGT7")),
        ]
        return items

    def _client_deadlines(packs, name, sy, ey, fy=None, firm_id=None, tax_audit_applicable=None):
        packs = set((packs or "").upper().replace(" ", "").split(","))
        packs.discard("")
        items, name = [], name or "Client"
        fy = fy or f"{sy}-{str(ey)[-2:]}"
        R = lambda k: _resolve_due(fy, k, sy, ey, firm_id)
        if "GST_MONTHLY" in packs:
            for y, m in [(sy, m) for m in range(4, 13)] + [(ey, m) for m in range(1, 4)]:
                dy, dm = (y + 1, 1) if m == 12 else (y, m + 1)
                mon = date(y, m, 1).strftime("%b %Y")
                items += [
                    (f"{name}: GSTR-1 {mon}", "GST", date(dy, dm, 11).isoformat()),
                    (f"{name}: GSTR-3B {mon}", "GST", date(dy, dm, 20).isoformat()),
                ]
        if "GST_QRMP" in packs:
            items += [
                (f"{name}: GSTR-1 QRMP Q1", "GST", f"{sy}-07-13"),
                (f"{name}: GSTR-1 QRMP Q2", "GST", f"{sy}-10-13"),
                (f"{name}: GSTR-1 QRMP Q3", "GST", f"{ey}-01-13"),
                (f"{name}: GSTR-1 QRMP Q4", "GST", f"{ey}-04-13"),
            ]
        if "TDS" in packs:
            items += [
                (f"{name}: TDS Q1", "TDS", R("TDS_Q1")),
                (f"{name}: TDS Q2", "TDS", R("TDS_Q2")),
                (f"{name}: TDS Q3", "TDS", R("TDS_Q3")),
                (f"{name}: TDS Q4", "TDS", R("TDS_Q4")),
                (f"{name}: Form 16/16A", "TDS", R("FORM_16")),
            ]
        has_itr = "ITR" in packs
        has_ta = "TAX_AUDIT" in packs or "TAXAUDIT" in packs
        if tax_audit_applicable is True:
            has_ta = True
            has_itr = False
        elif tax_audit_applicable is False:
            has_ta = False
        if has_itr and not has_ta:
            items.append((f"{name}: ITR filing (non-audit)", "ITR", R("ITR_NON_AUDIT")))
        if has_ta:
            items += [
                (f"{name}: Tax audit report u/s 44AB", "Tax Audit", R("TAX_AUDIT_REPORT")),
                (f"{name}: ITR filing (tax audit)", "ITR", R("ITR_AUDIT")),
            ]
        if "ROC" in packs:
            items += [
                (f"{name}: AOC-4", "ROC", R("AOC4")),
                (f"{name}: MGT-7", "ROC", R("MGT7")),
            ]
        if "PF_ESI" in packs:
            for y, m in [(sy, m) for m in range(4, 13)] + [(ey, m) for m in range(1, 4)]:
                dy, dm = (y + 1, 1) if m == 12 else (y, m + 1)
                mon = date(y, m, 1).strftime("%b %Y")
                items.append((f"{name}: PF/ESI {mon}", "Other", date(dy, dm, 15).isoformat()))
        return items

    def j():
        return request.get_json(silent=True) or {}

    def _uid():
        u = g.user or {}
        return u.get("id") or u.get("user_id")

    def _insert_compliance(title, cat, due, fy, client_id=None, source="manual"):
        cols = _col_names("compliance_calendar")
        has_client = "client_id" in cols or not cols
        has_source = "source" in cols or not cols
        uid = _uid()
        if has_client and has_source and client_id is not None:
            execute(
                "INSERT INTO compliance_calendar "
                "(firm_id,title,category,due_date,financial_year,is_recurring,status,created_by_id,client_id,source) "
                "VALUES (%s,%s,%s,%s,%s,TRUE,'Upcoming',%s,%s,%s)",
                (g.firm_id, title, cat, due, fy, uid, client_id, source),
            )
        elif has_client and client_id is not None:
            execute(
                "INSERT INTO compliance_calendar "
                "(firm_id,title,category,due_date,financial_year,is_recurring,status,created_by_id,client_id) "
                "VALUES (%s,%s,%s,%s,%s,TRUE,'Upcoming',%s,%s)",
                (g.firm_id, title, cat, due, fy, uid, client_id),
            )
        else:
            execute(
                "INSERT INTO compliance_calendar "
                "(firm_id,title,category,due_date,financial_year,is_recurring,status,created_by_id) "
                "VALUES (%s,%s,%s,%s,%s,TRUE,'Upcoming',%s)",
                (g.firm_id, title, cat, due, fy, uid),
            )

    def _fy_parts(fy):
        fy = (fy or "").strip()
        parts = fy.replace("/", "-").split("-")
        if not parts or not parts[0].isdigit():
            raise ValueError("bad fy")
        sy = int(parts[0])
        return sy, sy + 1

    def _prev_fy_label(fy):
        sy, _ = _fy_parts(fy)
        return f"{sy - 1}-{str(sy)[-2:]}"

    def _fy_window_dates(fy):
        sy, ey = _fy_parts(fy)
        return f"{sy}-04-01", f"{ey}-03-31"

    @app.route("/api/compliance-calendar/seed-fy-enhanced", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def seed_fy_enhanced():
        try:
            _ensure()
            fy = (j().get("financial_year") or "").strip()
            if not fy:
                return jsonify({"detail": "financial_year required"}), 400
            try:
                sy, ey = _parse_fy(fy)
            except Exception:
                return jsonify({"detail": "Use format YYYY-YY e.g. 2026-27"}), 400
            added = 0
            for title, cat, due in _firm_deadlines(sy, ey, fy=fy, firm_id=g.firm_id):
                if not qry(
                    "SELECT id FROM compliance_calendar WHERE firm_id=%s AND title=%s AND financial_year=%s",
                    (g.firm_id, title, fy), one=True,
                ):
                    _insert_compliance(title, cat, due, fy, client_id=None, source="firm_seed")
                    added += 1
            return jsonify({"message": f"Added {added} firm deadlines for {fy}", "added": added})
        except Exception as e:
            return jsonify({"detail": f"Seed failed: {e}"}), 500

    @app.route("/api/compliance-calendar/client-packs/<int:client_id>", methods=["GET"])
    @login_required
    def get_client_packs(client_id):
        try:
            _ensure()
            try:
                cl = qry("SELECT id,name,compliance_packs FROM clients WHERE id=%s AND firm_id=%s", (client_id, g.firm_id), one=True)
            except Exception:
                cl = qry("SELECT id,name FROM clients WHERE id=%s AND firm_id=%s", (client_id, g.firm_id), one=True)
                if cl:
                    cl = dict(cl); cl["compliance_packs"] = ""
            if not cl:
                return jsonify({"detail": "Client not found"}), 404
            packs = [p for p in (cl.get("compliance_packs") or "").split(",") if p]
            return jsonify({"client_id": client_id, "name": cl.get("name"), "packs": packs})
        except Exception as e:
            return jsonify({"detail": f"Could not load packs: {e}"}), 500

    @app.route("/api/compliance-calendar/client-packs/<int:client_id>", methods=["PUT"])
    @require_role("Admin", "Team Leader")
    def set_client_packs(client_id):
        try:
            _ensure()
            allowed = {"GST_MONTHLY", "GST_QRMP", "TDS", "ITR", "TAX_AUDIT", "ROC", "PF_ESI"}
            packs = []
            for p in (j().get("packs") or []):
                p = str(p).upper().strip()
                if p in allowed and p not in packs:
                    packs.append(p)
            if not qry("SELECT id FROM clients WHERE id=%s AND firm_id=%s", (client_id, g.firm_id), one=True):
                return jsonify({"detail": "Client not found"}), 404
            try:
                execute("UPDATE clients SET compliance_packs=%s WHERE id=%s AND firm_id=%s", (",".join(packs), client_id, g.firm_id))
            except Exception:
                try:
                    execute("ALTER TABLE clients ADD COLUMN compliance_packs TEXT DEFAULT ''")
                except Exception:
                    pass
                try:
                    execute("UPDATE clients SET compliance_packs=%s WHERE id=%s AND firm_id=%s", (",".join(packs), client_id, g.firm_id))
                except Exception as e2:
                    return jsonify({"detail": f"Could not save packs: {e2}"}), 500
            return jsonify({"ok": True, "packs": packs})
        except Exception as e:
            return jsonify({"detail": f"Save packs failed: {e}"}), 500

    @app.route("/api/compliance-calendar/generate-for-client", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def generate_for_client():
        try:
            _ensure()
            d = j()
            cid, fy = d.get("client_id"), (d.get("financial_year") or "").strip()
            if not cid or not fy:
                return jsonify({"detail": "client_id and financial_year required"}), 400
            try:
                cid = int(cid)
            except Exception:
                return jsonify({"detail": "Invalid client_id"}), 400
            try:
                sy, ey = _parse_fy(fy)
            except Exception:
                return jsonify({"detail": "Use format YYYY-YY e.g. 2026-27"}), 400
            try:
                cl = qry("SELECT id,name,compliance_packs FROM clients WHERE id=%s AND firm_id=%s", (cid, g.firm_id), one=True)
            except Exception as e:
                return jsonify({"detail": f"Client query failed: {e}"}), 500
            if not cl:
                return jsonify({"detail": "Client not found"}), 404
            body_packs = d.get("packs")
            if body_packs and isinstance(body_packs, list):
                packs = ",".join(str(p).upper().strip() for p in body_packs)
            else:
                packs = cl.get("compliance_packs") or ""
            items = _client_deadlines(packs, cl["name"], sy, ey, fy=fy, firm_id=g.firm_id)
            if not items:
                return jsonify({"detail": "No deadline templates for selected packs.", "packs": packs}), 400
            added, errors = 0, []
            for title, cat, due in items:
                if qry("SELECT id FROM compliance_calendar WHERE firm_id=%s AND title=%s AND financial_year=%s", (g.firm_id, title, fy), one=True):
                    continue
                try:
                    _insert_compliance(title, cat, due, fy, client_id=cid, source="client_pack")
                    added += 1
                except Exception as e:
                    errors.append(str(e))
            if added == 0 and errors:
                return jsonify({"detail": "Generate failed: " + errors[0]}), 500
            return jsonify({"message": f"Added {added} items for {cl['name']}", "added": added, "skipped": len(items) - added})
        except Exception as e:
            return jsonify({"detail": f"Generate failed: {e}"}), 500

    @app.route("/api/compliance-calendar/generate-all-clients", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def generate_all_clients():
        try:
            _ensure()
            fy = (j().get("financial_year") or "").strip()
            if not fy:
                return jsonify({"detail": "financial_year required"}), 400
            try:
                sy, ey = _parse_fy(fy)
            except Exception:
                return jsonify({"detail": "Use YYYY-YY"}), 400
            clients = qry(
                "SELECT id,name,compliance_packs FROM clients WHERE firm_id=%s AND COALESCE(is_active,TRUE)=TRUE "
                "AND compliance_packs IS NOT NULL AND compliance_packs<>''", (g.firm_id,),
            ) or []
            total = 0
            for cl in clients:
                for title, cat, due in _client_deadlines(cl.get("compliance_packs") or "", cl["name"], sy, ey, fy=fy, firm_id=g.firm_id):
                    if not qry("SELECT id FROM compliance_calendar WHERE firm_id=%s AND title=%s AND financial_year=%s", (g.firm_id, title, fy), one=True):
                        try:
                            _insert_compliance(title, cat, due, fy, client_id=cl["id"], source="client_pack")
                            total += 1
                        except Exception:
                            pass
            return jsonify({"message": f"Added {total} items across {len(clients)} clients", "added": total})
        except Exception as e:
            return jsonify({"detail": f"Generate-all failed: {e}"}), 500

    @app.route("/api/compliance-calendar/due-overrides", methods=["GET"])
    @login_required
    def list_due_overrides():
        try:
            _ensure_overrides()
            fy = (request.args.get("financial_year") or "").strip()
            q = "SELECT id, financial_year, event_key, due_date, notification_ref, source, notes, firm_id FROM compliance_due_overrides WHERE (firm_id IS NULL OR firm_id=%s)"
            args = [g.firm_id]
            if fy:
                q += " AND financial_year=%s"
                args.append(fy)
            q += " ORDER BY event_key"
            rows = qry(q, tuple(args)) or []
            defaults = {}
            if fy:
                try:
                    sy, ey = _parse_fy(fy)
                    defaults = _default_event_dates(sy, ey)
                except Exception:
                    pass
            return jsonify({"overrides": rows, "defaults": defaults, "event_keys": list(_default_event_dates(2025, 2026).keys())})
        except Exception as e:
            return jsonify({"detail": str(e)}), 500

    @app.route("/api/compliance-calendar/due-overrides", methods=["POST"])
    @require_role("Admin", "SuperAdmin")
    def upsert_due_override():
        try:
            _ensure_overrides()
            d = j()
            fy = (d.get("financial_year") or "").strip()
            key = (d.get("event_key") or "").strip().upper()
            due = (d.get("due_date") or "").strip()
            if not fy or not key or not due:
                return jsonify({"detail": "financial_year, event_key, due_date required"}), 400
            ref = (d.get("notification_ref") or "").strip()
            source = (d.get("source") or "CBDT").strip() or "CBDT"
            notes = (d.get("notes") or "").strip()
            firm_id = g.firm_id
            existing = qry(
                "SELECT id FROM compliance_due_overrides WHERE financial_year=%s AND event_key=%s AND firm_id=%s",
                (fy, key, firm_id), one=True,
            )
            if existing:
                execute(
                    "UPDATE compliance_due_overrides SET due_date=%s, notification_ref=%s, source=%s, notes=%s, updated_at=NOW() WHERE id=%s",
                    (due, ref, source, notes, existing["id"]),
                )
            else:
                execute(
                    "INSERT INTO compliance_due_overrides (financial_year, event_key, due_date, notification_ref, source, notes, firm_id) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (fy, key, due, ref, source, notes, firm_id),
                )
            return jsonify({"message": "Override saved", "event_key": key, "due_date": due, "notification_ref": ref})
        except Exception as e:
            return jsonify({"detail": str(e)}), 500

    @app.route("/api/compliance-calendar/due-overrides/<int:oid>", methods=["DELETE"])
    @require_role("Admin", "SuperAdmin")
    def delete_due_override(oid):
        try:
            _ensure_overrides()
            execute("DELETE FROM compliance_due_overrides WHERE id=%s AND firm_id=%s", (oid, g.firm_id))
            return jsonify({"message": "Deleted"})
        except Exception as e:
            return jsonify({"detail": str(e)}), 500

    print("[compliance] Enhanced compliance calendar routes registered")
