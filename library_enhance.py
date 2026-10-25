"""
CA FirmHub — Study Material / Library.
Designed & Built by Harsh Pala.

- Global curated official links (all firms, staff only)
- Firm-specific materials (SuperAdmin adds per firm; visible only to that firm)
"""
import os
from flask import request, jsonify, g

LIBRARY_CATALOG = [
    {
        "id": "income_tax",
        "title": "Income Tax & CBDT",
        "icon": "📋",
        "description": "Income-tax Act, rules, circulars, notifications and forms from official portals.",
        "items": [
            {"title": "Income Tax Department (Home)", "url": "https://www.incometax.gov.in/iec/foportal/", "source": "Income Tax Dept", "type": "Portal"},
            {"title": "Income Tax India (incometaxindia.gov.in)", "url": "https://incometaxindia.gov.in/", "source": "CBDT / ITD", "type": "Portal"},
            {"title": "Income-tax Act / Rules / Forms (Acts)", "url": "https://incometaxindia.gov.in/pages/acts/index.aspx", "source": "ITD", "type": "Act / Rules"},
            {"title": "Circulars & Notifications", "url": "https://incometaxindia.gov.in/Pages/communications/index.aspx", "source": "CBDT", "type": "Circulars"},
            {"title": "CBDT Press Releases / Updates", "url": "https://incometaxindia.gov.in/Pages/press-releases.aspx", "source": "CBDT", "type": "Updates"},
            {"title": "e-Filing portal", "url": "https://www.incometax.gov.in/iec/foportal", "source": "ITD", "type": "Portal"},
            {"title": "Tax Laws & Rules (India Code)", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Statute"},
        ],
    },
    {
        "id": "dtaa",
        "title": "DTAA & International Taxation (CBDT)",
        "icon": "🌍",
        "description": "Double Taxation Avoidance Agreements and EOI relationships (CBDT / ITD).",
        "items": [
            {"title": "India EOI / DTAA relationships (official list)", "url": "https://incometaxindia.gov.in/Pages/eoi/india-eoi-relationship.aspx", "source": "CBDT / ITD", "type": "DTAA list"},
            {"title": "International Taxation (ITD section)", "url": "https://incometaxindia.gov.in/Pages/international-taxation/index.aspx", "source": "ITD", "type": "Guide"},
            {"title": "Tax Treaties / DTAA documents hub", "url": "https://incometaxindia.gov.in/Pages/international-taxation/dtaa.aspx", "source": "ITD", "type": "DTAA"},
            {"title": "OECD Model Tax Convention (reference)", "url": "https://www.oecd.org/tax/treaties/", "source": "OECD", "type": "Reference"},
            {"title": "Income Tax notifications", "url": "https://incometaxindia.gov.in/Pages/communications/notifications.aspx", "source": "CBDT", "type": "Notifications"},
        ],
    },
    {
        "id": "gst",
        "title": "GST (Goods & Services Tax)",
        "icon": "🧾",
        "description": "GST portal, law, notifications, circulars and GST Council updates.",
        "items": [
            {"title": "GST Portal (Home)", "url": "https://www.gst.gov.in/", "source": "GSTN", "type": "Portal"},
            {"title": "GST News & Updates", "url": "https://www.gst.gov.in/newsandupdates", "source": "GSTN", "type": "Updates"},
            {"title": "CBIC GST", "url": "https://www.cbic.gov.in/entities/gst", "source": "CBIC", "type": "Portal"},
            {"title": "CGST / IGST / UTGST Acts & Rules", "url": "https://cbic-gst.gov.in/gst-acts.html", "source": "CBIC", "type": "Act / Rules"},
            {"title": "GST Notifications (CBIC)", "url": "https://cbic-gst.gov.in/central-tax-notifications.html", "source": "CBIC", "type": "Notifications"},
            {"title": "GST Circulars (CBIC)", "url": "https://cbic-gst.gov.in/circulars.html", "source": "CBIC", "type": "Circulars"},
            {"title": "GST Council", "url": "https://gstcouncil.gov.in/", "source": "GST Council", "type": "Council"},
            {"title": "e-Invoice portal", "url": "https://einvoice1.gst.gov.in/", "source": "GSTN", "type": "Portal"},
            {"title": "e-Way Bill portal", "url": "https://ewaybillgst.gov.in/", "source": "GSTN", "type": "Portal"},
        ],
    },
    {
        "id": "companies",
        "title": "Companies Act & MCA",
        "icon": "🏢",
        "description": "Companies Act, 2013, rules, circulars and MCA services.",
        "items": [
            {"title": "Ministry of Corporate Affairs (Home)", "url": "https://www.mca.gov.in/", "source": "MCA", "type": "Portal"},
            {"title": "Companies Act, 2013 (India Code)", "url": "https://www.indiacode.nic.in/handle/123456789/2114", "source": "India Code", "type": "Act"},
            {"title": "MCA Acts & Rules", "url": "https://www.mca.gov.in/content/mca/global/en/acts-rules.html", "source": "MCA", "type": "Act / Rules"},
            {"title": "MCA Circulars & Notifications", "url": "https://www.mca.gov.in/content/mca/global/en/data-and-reports/reports/circulars.html", "source": "MCA", "type": "Circulars"},
            {"title": "MCA V3 / e-Filing", "url": "https://www.mca.gov.in/content/mca/global/en/home.html", "source": "MCA", "type": "Portal"},
        ],
    },
    {
        "id": "llp",
        "title": "LLP Act",
        "icon": "🤝",
        "description": "Limited Liability Partnership Act and MCA resources.",
        "items": [
            {"title": "LLP Act, 2008 (India Code)", "url": "https://www.indiacode.nic.in/handle/123456789/2044", "source": "India Code", "type": "Act"},
            {"title": "MCA Home", "url": "https://www.mca.gov.in/", "source": "MCA", "type": "Portal"},
        ],
    },
    {
        "id": "partnership",
        "title": "Partnership Act",
        "icon": "👥",
        "description": "Indian Partnership Act, 1932.",
        "items": [
            {"title": "Indian Partnership Act, 1932 (India Code)", "url": "https://www.indiacode.nic.in/handle/123456789/2327", "source": "India Code", "type": "Act"},
        ],
    },
    {
        "id": "gujarat_trust",
        "title": "Gujarat Public Trust Act",
        "icon": "🏛️",
        "description": "Gujarat public trusts legislation and state resources.",
        "items": [
            {"title": "India Code (search Gujarat Trust)", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Act"},
            {"title": "Gujarat state portal", "url": "https://gujaratindia.gov.in/", "source": "Govt of Gujarat", "type": "Portal"},
        ],
    },
    {
        "id": "other",
        "title": "Other useful official sources",
        "icon": "📚",
        "description": "ICAI, RBI, SEBI and general statute references.",
        "items": [
            {"title": "ICAI", "url": "https://www.icai.org/", "source": "ICAI", "type": "Portal"},
            {"title": "ICAI Knowledge resources", "url": "https://www.icai.org/post/knowledge-resources", "source": "ICAI", "type": "Library"},
            {"title": "RBI Notifications", "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx", "source": "RBI", "type": "Notifications"},
            {"title": "SEBI", "url": "https://www.sebi.gov.in/", "source": "SEBI", "type": "Circulars"},
            {"title": "India Code", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Statute"},
            {"title": "eGazette", "url": "https://egazette.gov.in/", "source": "Govt of India", "type": "Gazette"},
        ],
    },
]


def register_library_enhance(app, helpers):
    qry = helpers["qry"]
    execute = helpers["execute"]
    login_required = helpers["login_required"]

    SUPERADMIN_KEY = os.environ.get("SUPERADMIN_KEY", "superadmin-secret-key")

    def staff_only():
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "Team Leader", "Member", "SuperAdmin")

    def sa_ok():
        return request.headers.get("X-SuperAdmin-Key", "") == SUPERADMIN_KEY

    def _ensure():
        execute(
            """
            CREATE TABLE IF NOT EXISTS firm_library_items (
                id SERIAL PRIMARY KEY,
                firm_id INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT DEFAULT 'Firm material',
                description TEXT,
                source TEXT,
                item_type TEXT DEFAULT 'Link',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        try:
            execute("CREATE INDEX IF NOT EXISTS idx_firm_library_firm ON firm_library_items(firm_id)")
        except Exception:
            pass

    try:
        _ensure()
    except Exception as e:
        print("[library] ensure table:", e)

    def firm_items(firm_id, active_only=True):
        sql = (
            "SELECT id, firm_id, title, url, category, description, source, item_type, is_active, created_at "
            "FROM firm_library_items WHERE firm_id=%s"
        )
        if active_only:
            sql += " AND COALESCE(is_active, TRUE)=TRUE"
        sql += " ORDER BY category, title"
        rows = qry(sql, (firm_id,)) or []
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "firm_id": r["firm_id"],
                "title": r["title"],
                "url": r["url"],
                "category": r.get("category") or "Firm material",
                "description": r.get("description") or "",
                "source": r.get("source") or "Firm library",
                "type": r.get("item_type") or "Link",
                "is_active": bool(r.get("is_active", True)),
                "created_at": str(r.get("created_at") or ""),
            })
        return out

    @app.route("/api/library/catalog")
    @login_required
    def library_catalog():
        if not staff_only():
            return jsonify({"detail": "Study Material is available to firm staff only (not Client users)."}), 403
        firm_mats = []
        try:
            if getattr(g, "firm_id", None):
                firm_mats = firm_items(g.firm_id, active_only=True)
        except Exception as e:
            print("[library] firm items:", e)

        firm_categories = {}
        for it in firm_mats:
            cat = it["category"] or "Firm material"
            firm_categories.setdefault(cat, []).append({
                "title": it["title"],
                "url": it["url"],
                "source": it["source"],
                "type": it["type"],
                "description": it.get("description") or "",
            })
        firm_section = [
            {
                "id": "firm_" + str(i),
                "title": cat,
                "icon": "📎",
                "description": "Firm-specific material (added by platform admin for your firm only).",
                "items": items,
                "firm_specific": True,
            }
            for i, (cat, items) in enumerate(firm_categories.items())
        ]

        return jsonify({
            "title": "Study Material / Library",
            "subtitle": "Official reading materials + firm-specific resources",
            "builder": "Designed & Built by Harsh Pala",
            "note": "Global links open official websites. Firm materials are visible only to your firm.",
            "categories": LIBRARY_CATALOG,
            "firm_categories": firm_section,
            "firm_item_count": len(firm_mats),
        })

    @app.route("/api/superadmin/library", methods=["GET"])
    def sa_library_list():
        if not sa_ok():
            return jsonify({"detail": "Super-admin access required"}), 403
        try:
            _ensure()
        except Exception:
            pass
        firm_id = request.args.get("firm_id")
        if firm_id:
            try:
                firm_id = int(firm_id)
            except Exception:
                return jsonify({"detail": "Invalid firm_id"}), 400
            return jsonify(firm_items(firm_id, active_only=False))
        rows = qry(
            "SELECT fli.*, f.name AS firm_name FROM firm_library_items fli "
            "JOIN firms f ON f.id = fli.firm_id ORDER BY f.name, fli.category, fli.title"
        ) or []
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "firm_id": r["firm_id"],
                "firm_name": r.get("firm_name") or "",
                "title": r["title"],
                "url": r["url"],
                "category": r.get("category") or "Firm material",
                "description": r.get("description") or "",
                "source": r.get("source") or "",
                "type": r.get("item_type") or "Link",
                "is_active": bool(r.get("is_active", True)),
                "created_at": str(r.get("created_at") or ""),
            })
        return jsonify(out)

    @app.route("/api/superadmin/library", methods=["POST"])
    def sa_library_create():
        if not sa_ok():
            return jsonify({"detail": "Super-admin access required"}), 403
        try:
            _ensure()
        except Exception:
            pass
        d = request.get_json(silent=True) or {}
        firm_id = d.get("firm_id")
        title = (d.get("title") or "").strip()
        url = (d.get("url") or "").strip()
        if not firm_id or not title or not url:
            return jsonify({"detail": "firm_id, title and url are required"}), 400
        try:
            firm_id = int(firm_id)
        except Exception:
            return jsonify({"detail": "Invalid firm_id"}), 400
        firm = qry("SELECT id, name FROM firms WHERE id=%s", (firm_id,), one=True)
        if not firm:
            return jsonify({"detail": "Firm not found"}), 404
        if not (url.startswith("http://") or url.startswith("https://")):
            return jsonify({"detail": "url must start with http:// or https://"}), 400
        category = (d.get("category") or "Firm material").strip() or "Firm material"
        description = (d.get("description") or "").strip()
        source = (d.get("source") or firm.get("name") or "Firm library").strip()
        item_type = (d.get("type") or d.get("item_type") or "Link").strip() or "Link"
        is_active = d.get("is_active", True)
        execute(
            "INSERT INTO firm_library_items (firm_id, title, url, category, description, source, item_type, is_active) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (firm_id, title, url, category, description or None, source, item_type, bool(is_active)),
        )
        rows = firm_items(firm_id, active_only=False)
        created = next((x for x in rows if x["title"] == title and x["url"] == url), rows[-1] if rows else {})
        return jsonify({"ok": True, "item": created}), 201

    @app.route("/api/superadmin/library/<int:item_id>", methods=["PUT"])
    def sa_library_update(item_id):
        if not sa_ok():
            return jsonify({"detail": "Super-admin access required"}), 403
        d = request.get_json(silent=True) or {}
        existing = qry("SELECT * FROM firm_library_items WHERE id=%s", (item_id,), one=True)
        if not existing:
            return jsonify({"detail": "Item not found"}), 404
        fields, vals = [], []
        mapping = {
            "title": "title",
            "url": "url",
            "category": "category",
            "description": "description",
            "source": "source",
        }
        for k, col in mapping.items():
            if k in d and d[k] is not None:
                val = str(d[k]).strip() if isinstance(d[k], str) else d[k]
                if col == "url" and val and not (str(val).startswith("http://") or str(val).startswith("https://")):
                    return jsonify({"detail": "url must start with http:// or https://"}), 400
                fields.append(f"{col}=%s")
                vals.append(val)
        if "type" in d or "item_type" in d:
            fields.append("item_type=%s")
            vals.append(str(d.get("type") or d.get("item_type") or "Link").strip())
        if "is_active" in d:
            fields.append("is_active=%s")
            vals.append(bool(d["is_active"]))
        if "firm_id" in d and d["firm_id"]:
            fields.append("firm_id=%s")
            vals.append(int(d["firm_id"]))
        if not fields:
            return jsonify({"detail": "No fields to update"}), 400
        vals.append(item_id)
        execute(f"UPDATE firm_library_items SET {', '.join(fields)} WHERE id=%s", tuple(vals))
        row = qry(
            "SELECT fli.*, f.name AS firm_name FROM firm_library_items fli "
            "JOIN firms f ON f.id = fli.firm_id WHERE fli.id=%s",
            (item_id,), one=True)
        return jsonify({"ok": True, "item": row})

    @app.route("/api/superadmin/library/<int:item_id>", methods=["DELETE"])
    def sa_library_delete(item_id):
        if not sa_ok():
            return jsonify({"detail": "Super-admin access required"}), 403
        existing = qry("SELECT id FROM firm_library_items WHERE id=%s", (item_id,), one=True)
        if not existing:
            return jsonify({"detail": "Item not found"}), 404
        execute("DELETE FROM firm_library_items WHERE id=%s", (item_id,))
        return jsonify({"ok": True})

    print("[library] Study Material + firm library routes registered")
