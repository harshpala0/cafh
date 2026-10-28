"""CA FirmHub compliance enhance.
Designed & Built by Harsh Pala.
Hardened pack save + generate for clients.
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

    def _firm_deadlines(sy, ey):
        items = []
        for y, m in [(sy, m) for m in range(4, 13)] + [(ey, m) for m in range(1, 4)]:
            dy, dm = (y + 1, 1) if m == 12 else (y, m + 1)
            mon = date(y, m, 1).strftime("%b %Y")
            items.append((f"GSTR-1 — {mon}", "GST", date(dy, dm, 11).isoformat()))
            items.append((f"GSTR-3B — {mon}", "GST", date(dy, dm, 20).isoformat()))
        items += [
            ("GSTR-9 Annual Return", "GST", f"{ey}-12-31"),
            ("TDS Return Q1", "TDS", f"{sy}-07-31"),
            ("TDS Return Q2", "TDS", f"{sy}-10-31"),
            ("TDS Return Q3", "TDS", f"{ey}-01-31"),
            ("TDS Return Q4", "TDS", f"{ey}-05-31"),
            ("Form 16 / 16A", "TDS", f"{ey}-06-15"),
            ("Advance Tax 15 Jun", "ITR", f"{sy}-06-15"),
            ("Advance Tax 15 Sep", "ITR", f"{sy}-09-15"),
            ("Advance Tax 15 Dec", "ITR", f"{sy}-12-15"),
            ("Advance Tax 15 Mar", "ITR", f"{ey}-03-15"),
            ("ITR Non-audit", "ITR", f"{ey}-07-31"),
            ("ITR Tax audit / Cos", "ITR", f"{ey}-10-31"),
            ("AGM deadline", "ROC", f"{ey}-09-30"),
            ("AOC-4", "ROC", f"{ey}-10-29"),
            ("MGT-7", "ROC", f"{ey}-11-29"),
        ]
        return items

    def _client_deadlines(packs, name, sy, ey):
        packs = set((packs or "").upper().replace(" ", "").split(","))
        packs.discard("")
        items, name = [], name or "Client"
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
                (f"{name}: TDS Q1", "TDS", f"{sy}-07-31"),
                (f"{name}: TDS Q2", "TDS", f"{sy}-10-31"),
                (f"{name}: TDS Q3", "TDS", f"{ey}-01-31"),
                (f"{name}: TDS Q4", "TDS", f"{ey}-05-31"),
            ]
        if "ITR" in packs:
            items += [
                (f"{name}: ITR filing", "ITR", f"{ey}-07-31"),
                (f"{name}: Tax audit", "ITR", f"{ey}-10-31"),
            ]
        if "ROC" in packs:
            items += [
                (f"{name}: AOC-4", "ROC", f"{ey}-10-29"),
                (f"{name}: MGT-7", "ROC", f"{ey}-11-29"),
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
        return True

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
            for title, cat, due in _firm_deadlines(sy, ey):
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
                cl = qry(
                    "SELECT id,name,compliance_packs FROM clients WHERE id=%s AND firm_id=%s",
                    (client_id, g.firm_id), one=True,
                )
            except Exception:
                cl = qry(
                    "SELECT id,name FROM clients WHERE id=%s AND firm_id=%s",
                    (client_id, g.firm_id), one=True,
                )
                if cl:
                    cl = dict(cl)
                    cl["compliance_packs"] = ""
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
            allowed = {"GST_MONTHLY", "GST_QRMP", "TDS", "ITR", "ROC", "PF_ESI"}
            packs = []
            for p in (j().get("packs") or []):
                p = str(p).upper().strip()
                if p in allowed and p not in packs:
                    packs.append(p)
            if not qry("SELECT id FROM clients WHERE id=%s AND firm_id=%s", (client_id, g.firm_id), one=True):
                return jsonify({"detail": "Client not found"}), 404
            try:
                execute(
                    "UPDATE clients SET compliance_packs=%s WHERE id=%s AND firm_id=%s",
                    (",".join(packs), client_id, g.firm_id),
                )
            except Exception:
                try:
                    execute("ALTER TABLE clients ADD COLUMN compliance_packs TEXT DEFAULT ''")
                except Exception:
                    pass
                try:
                    execute(
                        "UPDATE clients SET compliance_packs=%s WHERE id=%s AND firm_id=%s",
                        (",".join(packs), client_id, g.firm_id),
                    )
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
            cid = d.get("client_id")
            fy = (d.get("financial_year") or "").strip()
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
                cl = qry(
                    "SELECT id,name,compliance_packs FROM clients WHERE id=%s AND firm_id=%s",
                    (cid, g.firm_id), one=True,
                )
            except Exception as e:
                return jsonify({"detail": f"Client query failed: {e}"}), 500
            if not cl:
                return jsonify({"detail": "Client not found"}), 404

            body_packs = d.get("packs")
            if body_packs and isinstance(body_packs, list):
                packs = ",".join(str(p).upper().strip() for p in body_packs)
            else:
                packs = cl.get("compliance_packs") or ""

            items = _client_deadlines(packs, cl["name"], sy, ey)
            if not items:
                return jsonify({
                    "detail": "No deadline templates for selected packs. Select at least one service.",
                    "packs": packs,
                }), 400

            added = 0
            errors = []
            for title, cat, due in items:
                if qry(
                    "SELECT id FROM compliance_calendar WHERE firm_id=%s AND title=%s AND financial_year=%s",
                    (g.firm_id, title, fy), one=True,
                ):
                    continue
                try:
                    _insert_compliance(title, cat, due, fy, client_id=cid, source="client_pack")
                    added += 1
                except Exception as e:
                    errors.append(str(e))
            if added == 0 and errors:
                return jsonify({"detail": "Generate failed: " + errors[0], "errors": errors[:3]}), 500
            return jsonify({
                "message": f"Added {added} items for {cl['name']}",
                "added": added,
                "skipped": len(items) - added,
            })
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
            try:
                clients = qry(
                    "SELECT id,name,compliance_packs FROM clients WHERE firm_id=%s AND COALESCE(is_active,TRUE)=TRUE "
                    "AND compliance_packs IS NOT NULL AND compliance_packs<>''",
                    (g.firm_id,),
                ) or []
            except Exception as e:
                return jsonify({"detail": f"Query clients failed: {e}"}), 500
            total = 0
            for cl in clients:
                items = _client_deadlines(cl.get("compliance_packs") or "", cl["name"], sy, ey)
                for title, cat, due in items:
                    if not qry(
                        "SELECT id FROM compliance_calendar WHERE firm_id=%s AND title=%s AND financial_year=%s",
                        (g.firm_id, title, fy), one=True,
                    ):
                        try:
                            _insert_compliance(title, cat, due, fy, client_id=cl["id"], source="client_pack")
                            total += 1
                        except Exception:
                            pass
            return jsonify({"message": f"Added {total} items across {len(clients)} clients", "added": total})
        except Exception as e:
            return jsonify({"detail": f"Generate-all failed: {e}"}), 500

    @app.route("/api/compliance-calendar/create-tasks", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def create_tasks_from_compliance():
        try:
            ids = j().get("ids") or []
            if not ids:
                return jsonify({"detail": "ids required"}), 400
            created = 0
            for cid in ids:
                row = qry("SELECT * FROM compliance_calendar WHERE id=%s AND firm_id=%s", (cid, g.firm_id), one=True)
                if not row or row.get("status") == "Completed":
                    continue
                if qry(
                    "SELECT id FROM tasks WHERE firm_id=%s AND title=%s AND due_date=%s",
                    (g.firm_id, row["title"], row["due_date"]), one=True,
                ):
                    continue
                execute(
                    "INSERT INTO tasks (firm_id,engagement_id,title,description,status,priority,due_date,created_by_id) "
                    "VALUES (%s,%s,%s,%s,'Pending','High',%s,%s)",
                    (g.firm_id, row.get("engagement_id"), row["title"],
                     f"From compliance ({row.get('category')})", row["due_date"], _uid()),
                )
                created += 1
            return jsonify({"message": f"Created {created} tasks", "created": created})
        except Exception as e:
            return jsonify({"detail": f"Create tasks failed: {e}"}), 500

    @app.route("/api/compliance-calendar/auto-missed", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def auto_missed():
        try:
            execute(
                "UPDATE compliance_calendar SET status='Missed' WHERE firm_id=%s AND status='Upcoming' AND due_date < %s",
                (g.firm_id, date.today().isoformat()),
            )
            return jsonify({"message": "Updated missed items"})
        except Exception as e:
            return jsonify({"detail": str(e)}), 500

    @app.route("/api/compliance-calendar/board")
    @login_required
    def compliance_board():
        try:
            _ensure()
            today = date.today()
            week = today + timedelta(days=7)
            month = today + timedelta(days=30)
            fid = g.firm_id
            try:
                execute(
                    "UPDATE compliance_calendar SET status='Missed' WHERE firm_id=%s AND status='Upcoming' AND due_date < %s",
                    (fid, today.isoformat()),
                )
            except Exception:
                pass
            return jsonify({
                "overdue": qry(
                    "SELECT id,title,category,due_date,status,client_id FROM compliance_calendar "
                    "WHERE firm_id=%s AND status='Missed' ORDER BY due_date DESC LIMIT 50", (fid,),
                ) or [],
                "this_week": qry(
                    "SELECT id,title,category,due_date,status,client_id FROM compliance_calendar "
                    "WHERE firm_id=%s AND status='Upcoming' AND due_date BETWEEN %s AND %s ORDER BY due_date LIMIT 50",
                    (fid, today.isoformat(), week.isoformat()),
                ) or [],
                "this_month": qry(
                    "SELECT id,title,category,due_date,status,client_id FROM compliance_calendar "
                    "WHERE firm_id=%s AND status='Upcoming' AND due_date BETWEEN %s AND %s ORDER BY due_date LIMIT 100",
                    (fid, today.isoformat(), month.isoformat()),
                ) or [],
                "by_category": qry(
                    "SELECT category,status,COUNT(*) as count FROM compliance_calendar WHERE firm_id=%s GROUP BY category,status",
                    (fid,),
                ) or [],
            })
        except Exception as e:
            try:
                return jsonify({
                    "overdue": qry(
                        "SELECT id,title,category,due_date,status FROM compliance_calendar "
                        "WHERE firm_id=%s AND status='Missed' ORDER BY due_date DESC LIMIT 50", (g.firm_id,),
                    ) or [],
                    "this_week": [], "this_month": [], "by_category": [], "warning": str(e),
                })
            except Exception as e2:
                return jsonify({"detail": str(e2), "overdue": [], "this_week": [], "this_month": [], "by_category": []}), 500

    print("[compliance] Enhanced compliance calendar routes registered")
