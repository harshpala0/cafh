"""Extra compliance routes: board, bifurcated, tasks — merge into app after compliance_enhance."""
from datetime import date, timedelta
from flask import request, jsonify, g

def register_compliance_board_extra(app, helpers):
    qry, execute = helpers["qry"], helpers["execute"]
    login_required, require_role = helpers["login_required"], helpers["require_role"]

    def _uid():
        u = g.user or {}
        return u.get("id") or u.get("user_id")

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

    @app.route("/api/compliance-calendar/board")
    @login_required
    def compliance_board():
        try:
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
                    "WHERE firm_id=%s AND status='Missed' ORDER BY due_date DESC LIMIT 50", (fid,)) or [],
                "this_week": qry(
                    "SELECT id,title,category,due_date,status,client_id FROM compliance_calendar "
                    "WHERE firm_id=%s AND status='Upcoming' AND due_date BETWEEN %s AND %s ORDER BY due_date LIMIT 50",
                    (fid, today.isoformat(), week.isoformat())) or [],
                "this_month": qry(
                    "SELECT id,title,category,due_date,status,client_id FROM compliance_calendar "
                    "WHERE firm_id=%s AND status='Upcoming' AND due_date BETWEEN %s AND %s ORDER BY due_date LIMIT 80",
                    (fid, today.isoformat(), month.isoformat())) or [],
            })
        except Exception as e:
            return jsonify({"detail": str(e)}), 500

    @app.route("/api/compliance-calendar/bifurcated")
    @login_required
    def compliance_bifurcated():
        try:
            fy = (request.args.get("fy") or request.args.get("financial_year") or "").strip()
            if not fy:
                return jsonify({"detail": "fy required e.g. 2026-27"}), 400
            try:
                window_start, window_end = _fy_window_dates(fy)
                prior_fy = _prev_fy_label(fy)
            except Exception:
                return jsonify({"detail": "Use format YYYY-YY e.g. 2026-27"}), 400
            rows = qry(
                "SELECT * FROM compliance_calendar WHERE firm_id=%s AND due_date >= %s AND due_date <= %s ORDER BY due_date, title",
                (g.firm_id, window_start, window_end),
            ) or []
            prior, current, other = [], [], []
            for r in rows:
                item = dict(r)
                if item.get("due_date") is not None:
                    item["due_date"] = str(item["due_date"])[:10]
                if item.get("created_at") is not None:
                    item["created_at"] = str(item["created_at"])
                fy_tag = (item.get("financial_year") or "").strip()
                if fy_tag == prior_fy:
                    item["bucket"] = "prior_fy_due_in_window"
                    prior.append(item)
                elif fy_tag == fy or not fy_tag:
                    item["bucket"] = "current_fy"
                    if not fy_tag:
                        item["financial_year"] = fy
                    current.append(item)
                else:
                    item["bucket"] = "other"
                    other.append(item)
            return jsonify({
                "selected_fy": fy,
                "prior_fy": prior_fy,
                "window_start": window_start,
                "window_end": window_end,
                "prior_fy_items": prior,
                "current_fy_items": current,
                "other_items": other,
                "counts": {"prior": len(prior), "current": len(current), "other": len(other), "total": len(rows)},
            })
        except Exception as e:
            return jsonify({"detail": str(e)}), 500

    @app.route("/api/compliance-calendar/create-tasks", methods=["POST"])
    @require_role("Admin", "Team Leader")
    def create_tasks_from_compliance():
        try:
            d = request.get_json(silent=True) or {}
            ids = d.get("ids") or []
            if not ids:
                return jsonify({"detail": "ids required"}), 400
            created = 0
            for cid in ids:
                row = qry("SELECT * FROM compliance_calendar WHERE id=%s AND firm_id=%s", (cid, g.firm_id), one=True)
                if not row or row.get("status") == "Completed":
                    continue
                if qry("SELECT id FROM tasks WHERE firm_id=%s AND title=%s AND due_date=%s",
                       (g.firm_id, row["title"], row["due_date"]), one=True):
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

    print("[compliance] Board / bifurcated extra routes registered")
