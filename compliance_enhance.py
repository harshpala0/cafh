"""CA FirmHub compliance enhance (lean)."""
from datetime import date, timedelta
from calendar import monthrange
from flask import request, jsonify, g

def register_compliance_enhance(app, helpers):
    qry, execute = helpers["qry"], helpers["execute"]
    login_required, require_role = helpers["login_required"], helpers["require_role"]
    log_action = helpers.get("log_action", lambda *a, **k: None)
    qry_id = helpers.get("qry_id")

    def _ensure():
        execute("ALTER TABLE compliance_calendar ADD COLUMN IF NOT EXISTS client_id INTEGER REFERENCES clients(id)")
        execute("ALTER TABLE compliance_calendar ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual'")
        execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS compliance_packs TEXT DEFAULT ''")
        execute("CREATE INDEX IF NOT EXISTS idx_comp_client ON compliance_calendar(client_id)")
    try: _ensure()
    except Exception as e: print("[compliance]", e)

    def _parse_fy(fy):
        s = int(fy.split("-")[0]); return s, s+1

    def _firm_deadlines(sy, ey):
        items = []
        for y, m in [(sy, m) for m in range(4,13)] + [(ey, m) for m in range(1,4)]:
            dy, dm = (y+1, 1) if m==12 else (y, m+1)
            mon = date(y,m,1).strftime("%b %Y")
            items.append((f"GSTR-1 — {mon}", "GST", date(dy,dm,11).isoformat()))
            items.append((f"GSTR-3B — {mon}", "GST", date(dy,dm,20).isoformat()))
        items += [
            ("GSTR-9 Annual Return","GST",f"{ey}-12-31"),
            ("TDS Return Q1","TDS",f"{sy}-07-31"),("TDS Return Q2","TDS",f"{sy}-10-31"),
            ("TDS Return Q3","TDS",f"{ey}-01-31"),("TDS Return Q4","TDS",f"{ey}-05-31"),
            ("Form 16 / 16A","TDS",f"{ey}-06-15"),
            ("Advance Tax 15 Jun","ITR",f"{sy}-06-15"),("Advance Tax 15 Sep","ITR",f"{sy}-09-15"),
            ("Advance Tax 15 Dec","ITR",f"{sy}-12-15"),("Advance Tax 15 Mar","ITR",f"{ey}-03-15"),
            ("ITR Non-audit","ITR",f"{ey}-07-31"),("ITR Tax audit / Cos","ITR",f"{ey}-10-31"),
            ("AGM deadline","ROC",f"{ey}-09-30"),("AOC-4","ROC",f"{ey}-10-29"),("MGT-7","ROC",f"{ey}-11-29"),
        ]
        return items

    def _client_deadlines(packs, name, sy, ey):
        packs = set((packs or "").upper().replace(" ","").split(",")); packs.discard("")
        items, name = [], name or "Client"
        if "GST_MONTHLY" in packs:
            for y,m in [(sy,m) for m in range(4,13)]+[(ey,m) for m in range(1,4)]:
                dy,dm = (y+1,1) if m==12 else (y,m+1)
                mon = date(y,m,1).strftime("%b %Y")
                items += [(f"{name}: GSTR-1 {mon}","GST",date(dy,dm,11).isoformat()),
                          (f"{name}: GSTR-3B {mon}","GST",date(dy,dm,20).isoformat())]
        if "GST_QRMP" in packs:
            items += [(f"{name}: GSTR-1 QRMP Q1","GST",f"{sy}-07-13"),(f"{name}: GSTR-1 QRMP Q2","GST",f"{sy}-10-13"),
                      (f"{name}: GSTR-1 QRMP Q3","GST",f"{ey}-01-13"),(f"{name}: GSTR-1 QRMP Q4","GST",f"{ey}-04-13")]
        if "TDS" in packs:
            items += [(f"{name}: TDS Q1","TDS",f"{sy}-07-31"),(f"{name}: TDS Q2","TDS",f"{sy}-10-31"),
                      (f"{name}: TDS Q3","TDS",f"{ey}-01-31"),(f"{name}: TDS Q4","TDS",f"{ey}-05-31")]
        if "ITR" in packs:
            items += [(f"{name}: ITR filing","ITR",f"{ey}-07-31"),(f"{name}: Tax audit","ITR",f"{ey}-10-31")]
        if "ROC" in packs:
            items += [(f"{name}: AOC-4","ROC",f"{ey}-10-29"),(f"{name}: MGT-7","ROC",f"{ey}-11-29")]
        if "PF_ESI" in packs:
            for y,m in [(sy,m) for m in range(4,13)]+[(ey,m) for m in range(1,4)]:
                dy,dm = (y+1,1) if m==12 else (y,m+1)
                mon = date(y,m,1).strftime("%b %Y")
                items.append((f"{name}: PF/ESI {mon}","Other",date(dy,dm,15).isoformat()))
        return items

    def j(): return request.get_json(silent=True) or {}

    @app.route("/api/compliance-calendar/seed-fy-enhanced", methods=["POST"])
    @require_role("Admin","Team Leader")
    def seed_fy_enhanced():
        d=j(); fy=(d.get("financial_year") or "").strip()
        if not fy: return jsonify({"detail":"financial_year required"}),400
        try: sy,ey=_parse_fy(fy)
        except Exception: return jsonify({"detail":"Use YYYY-YY"}),400
        added=0
        for title,cat,due in _firm_deadlines(sy,ey):
            if not qry("SELECT id FROM compliance_calendar WHERE firm_id=%s AND title=%s AND financial_year=%s",(g.firm_id,title,fy),one=True):
                execute("INSERT INTO compliance_calendar (firm_id,title,category,due_date,financial_year,is_recurring,status,created_by_id,source) VALUES (%s,%s,%s,%s,%s,TRUE,'Upcoming',%s,'seed')",(g.firm_id,title,cat,due,fy,g.user["id"]))
                added+=1
        execute("UPDATE compliance_calendar SET status='Missed' WHERE firm_id=%s AND status='Upcoming' AND due_date < %s",(g.firm_id,date.today().isoformat()))
        return jsonify({"message":f"Seeded {added} dates for FY {fy}","added":added})

    @app.route("/api/compliance-calendar/client-packs/<int:client_id>", methods=["GET"])
    @login_required
    def get_client_packs(client_id):
        cl=qry("SELECT id,name,compliance_packs FROM clients WHERE id=%s AND firm_id=%s",(client_id,g.firm_id),one=True)
        if not cl: return jsonify({"detail":"Not found"}),404
        return jsonify({"client_id":client_id,"name":cl["name"],"packs":[p for p in (cl.get("compliance_packs") or "").split(",") if p]})

    @app.route("/api/compliance-calendar/client-packs/<int:client_id>", methods=["PUT"])
    @require_role("Admin","Team Leader")
    def set_client_packs(client_id):
        allowed={"GST_MONTHLY","GST_QRMP","TDS","ITR","ROC","PF_ESI"}
        packs=[p.upper().strip() for p in (j().get("packs") or []) if p.upper().strip() in allowed]
        if not qry("SELECT id FROM clients WHERE id=%s AND firm_id=%s",(client_id,g.firm_id),one=True):
            return jsonify({"detail":"Not found"}),404
        execute("UPDATE clients SET compliance_packs=%s WHERE id=%s",(",".join(packs),client_id))
        return jsonify({"ok":True,"packs":packs})

    @app.route("/api/compliance-calendar/generate-for-client", methods=["POST"])
    @require_role("Admin","Team Leader")
    def generate_for_client():
        d=j(); cid,fy=d.get("client_id"),(d.get("financial_year") or "").strip()
        if not cid or not fy: return jsonify({"detail":"client_id and financial_year required"}),400
        try: sy,ey=_parse_fy(fy)
        except Exception: return jsonify({"detail":"Use YYYY-YY"}),400
        cl=qry("SELECT id,name,compliance_packs FROM clients WHERE id=%s AND firm_id=%s",(cid,g.firm_id),one=True)
        if not cl: return jsonify({"detail":"Not found"}),404
        packs=cl.get("compliance_packs") or ""
        items=_client_deadlines(packs,cl["name"],sy,ey)
        if not items: return jsonify({"detail":"No packs on client"}),400
        added=0
        for title,cat,due in items:
            if not qry("SELECT id FROM compliance_calendar WHERE firm_id=%s AND client_id=%s AND title=%s AND financial_year=%s",(g.firm_id,cid,title,fy),one=True):
                execute("INSERT INTO compliance_calendar (firm_id,title,category,due_date,financial_year,is_recurring,status,created_by_id,client_id,source) VALUES (%s,%s,%s,%s,%s,TRUE,'Upcoming',%s,%s,'client_pack')",(g.firm_id,title,cat,due,fy,g.user["id"],cid))
                added+=1
        return jsonify({"message":f"Added {added} items for {cl['name']}","added":added})

    @app.route("/api/compliance-calendar/generate-all-clients", methods=["POST"])
    @require_role("Admin","Team Leader")
    def generate_all_clients():
        d=j(); fy=(d.get("financial_year") or "").strip()
        if not fy: return jsonify({"detail":"financial_year required"}),400
        try: sy,ey=_parse_fy(fy)
        except Exception: return jsonify({"detail":"Use YYYY-YY"}),400
        clients=qry("SELECT id,name,compliance_packs FROM clients WHERE firm_id=%s AND is_active=TRUE AND compliance_packs IS NOT NULL AND compliance_packs<>''",(g.firm_id,)) or []
        total=0
        for cl in clients:
            for title,cat,due in _client_deadlines(cl.get("compliance_packs"),cl["name"],sy,ey):
                if not qry("SELECT id FROM compliance_calendar WHERE firm_id=%s AND client_id=%s AND title=%s AND financial_year=%s",(g.firm_id,cl["id"],title,fy),one=True):
                    execute("INSERT INTO compliance_calendar (firm_id,title,category,due_date,financial_year,is_recurring,status,created_by_id,client_id,source) VALUES (%s,%s,%s,%s,%s,TRUE,'Upcoming',%s,%s,'client_pack')",(g.firm_id,title,cat,due,fy,g.user["id"],cl["id"]))
                    total+=1
        return jsonify({"message":f"Generated {total} items","added":total})

    @app.route("/api/compliance-calendar/create-tasks", methods=["POST"])
    @require_role("Admin","Team Leader")
    def create_tasks_from_compliance():
        d=j(); ids=d.get("ids") or []
        if not ids: return jsonify({"detail":"ids required"}),400
        created=0
        for cid in ids:
            row=qry("SELECT * FROM compliance_calendar WHERE id=%s AND firm_id=%s",(cid,g.firm_id),one=True)
            if not row or row.get("status")=="Completed": continue
            if qry("SELECT id FROM tasks WHERE firm_id=%s AND title=%s AND due_date=%s",(g.firm_id,row["title"],row["due_date"]),one=True): continue
            execute("INSERT INTO tasks (firm_id,engagement_id,title,description,status,priority,due_date,created_by_id) VALUES (%s,%s,%s,%s,'Pending','High',%s,%s)",
                    (g.firm_id,row.get("engagement_id"),row["title"],f"From compliance ({row.get('category')})",row["due_date"],g.user["id"]))
            created+=1
        return jsonify({"message":f"Created {created} tasks","created":created})

    @app.route("/api/compliance-calendar/auto-missed", methods=["POST"])
    @require_role("Admin","Team Leader")
    def auto_missed():
        execute("UPDATE compliance_calendar SET status='Missed' WHERE firm_id=%s AND status='Upcoming' AND due_date < %s",(g.firm_id,date.today().isoformat()))
        return jsonify({"message":"Updated missed items"})

    @app.route("/api/compliance-calendar/board")
    @login_required
    def compliance_board():
        today=date.today(); week=today+timedelta(days=7); month=today+timedelta(days=30); fid=g.firm_id
        try: execute("UPDATE compliance_calendar SET status='Missed' WHERE firm_id=%s AND status='Upcoming' AND due_date < %s",(fid,today.isoformat()))
        except Exception: pass
        return jsonify({
            "overdue": qry("SELECT id,title,category,due_date,status,client_id FROM compliance_calendar WHERE firm_id=%s AND status='Missed' ORDER BY due_date DESC LIMIT 50",(fid,)) or [],
            "this_week": qry("SELECT id,title,category,due_date,status,client_id FROM compliance_calendar WHERE firm_id=%s AND status='Upcoming' AND due_date BETWEEN %s AND %s ORDER BY due_date LIMIT 50",(fid,today.isoformat(),week.isoformat())) or [],
            "this_month": qry("SELECT id,title,category,due_date,status,client_id FROM compliance_calendar WHERE firm_id=%s AND status='Upcoming' AND due_date BETWEEN %s AND %s ORDER BY due_date LIMIT 100",(fid,today.isoformat(),month.isoformat())) or [],
            "by_category": qry("SELECT category,status,COUNT(*) as count FROM compliance_calendar WHERE firm_id=%s GROUP BY category,status",(fid,)) or [],
        })

    print("[compliance] Enhanced compliance calendar routes registered")
