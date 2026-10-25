"""
CA FirmHub — Study Material / Library (platform-wide).
Designed & Built by Harsh Pala.

Curated official reading links: Income Tax, GST, Companies Act,
Partnership Act, LLP Act, Gujarat Public Trust Act, DTAA (CBDT), etc.
Available to every firm user except Client role.
"""
from flask import jsonify, g


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
            {"title": "e-Filing portal (services & utilities)", "url": "https://www.incometax.gov.in/iec/foportal", "source": "ITD", "type": "Portal"},
            {"title": "Tax Laws & Rules (India Code)", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Statute"},
        ],
    },
    {
        "id": "dtaa",
        "title": "DTAA & International Taxation (CBDT)",
        "icon": "🌍",
        "description": "Double Taxation Avoidance Agreements and exchange-of-information relationships as listed by CBDT / Income Tax Department.",
        "items": [
            {"title": "India EOI / DTAA relationships (official list)", "url": "https://incometaxindia.gov.in/Pages/eoi/india-eoi-relationship.aspx", "source": "CBDT / ITD", "type": "DTAA list"},
            {"title": "International Taxation (ITD section)", "url": "https://incometaxindia.gov.in/Pages/international-taxation/index.aspx", "source": "ITD", "type": "Guide"},
            {"title": "Tax Treaties / DTAA documents hub", "url": "https://incometaxindia.gov.in/Pages/international-taxation/dtaa.aspx", "source": "ITD", "type": "DTAA"},
            {"title": "OECD Model Tax Convention (reference)", "url": "https://www.oecd.org/tax/treaties/", "source": "OECD", "type": "Reference"},
            {"title": "Income Tax notifications (search treaties)", "url": "https://incometaxindia.gov.in/Pages/communications/notifications.aspx", "source": "CBDT", "type": "Notifications"},
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
            {"title": "CBIC GST (Central Board of Indirect Taxes)", "url": "https://www.cbic.gov.in/entities/gst", "source": "CBIC", "type": "Portal"},
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
            {"title": "Company LLP Master Data search", "url": "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do", "source": "MCA", "type": "Search"},
        ],
    },
    {
        "id": "llp",
        "title": "LLP Act",
        "icon": "🤝",
        "description": "Limited Liability Partnership Act, rules and MCA LLP resources.",
        "items": [
            {"title": "Limited Liability Partnership Act, 2008 (India Code)", "url": "https://www.indiacode.nic.in/handle/123456789/2044", "source": "India Code", "type": "Act"},
            {"title": "MCA – LLP related pages", "url": "https://www.mca.gov.in/", "source": "MCA", "type": "Portal"},
            {"title": "India Code – search LLP", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Statute"},
        ],
    },
    {
        "id": "partnership",
        "title": "Partnership Act",
        "icon": "👥",
        "description": "Indian Partnership Act, 1932 and related materials.",
        "items": [
            {"title": "Indian Partnership Act, 1932 (India Code)", "url": "https://www.indiacode.nic.in/handle/123456789/2327", "source": "India Code", "type": "Act"},
            {"title": "India Code (search Partnership)", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Statute"},
        ],
    },
    {
        "id": "gujarat_trust",
        "title": "Gujarat Public Trust Act",
        "icon": "🏛️",
        "description": "Gujarat public trusts legislation and state resources.",
        "items": [
            {"title": "Gujarat Public Trusts Act materials (India Code / State)", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Act"},
            {"title": "Charity Commissioner / Gujarat state portal", "url": "https://gujaratindia.gov.in/", "source": "Govt of Gujarat", "type": "Portal"},
            {"title": "Gujarat Acts (official state laws hub)", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Statute"},
        ],
    },
    {
        "id": "other",
        "title": "Other useful official sources",
        "icon": "📚",
        "description": "ICAI, RBI, SEBI, labour and general statute references useful for practice.",
        "items": [
            {"title": "ICAI (Institute of Chartered Accountants of India)", "url": "https://www.icai.org/", "source": "ICAI", "type": "Portal"},
            {"title": "ICAI Knowledge / publications", "url": "https://www.icai.org/post/knowledge-resources", "source": "ICAI", "type": "Library"},
            {"title": "RBI Notifications", "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx", "source": "RBI", "type": "Notifications"},
            {"title": "SEBI Legal / Circulars", "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=3&smid=0", "source": "SEBI", "type": "Circulars"},
            {"title": "India Code (all Central Acts)", "url": "https://www.indiacode.nic.in/", "source": "India Code", "type": "Statute"},
            {"title": "eGazette (official notifications)", "url": "https://egazette.gov.in/", "source": "Govt of India", "type": "Gazette"},
        ],
    },
]


def register_library_enhance(app, helpers):
    login_required = helpers["login_required"]

    def staff_only():
        role = (g.user or {}).get("role") or ""
        return role in ("Admin", "Team Leader", "Member", "SuperAdmin")

    @app.route("/api/library/catalog")
    @login_required
    def library_catalog():
        if not staff_only():
            return jsonify({"detail": "Study Material is available to firm staff only (not Client users)."}), 403
        return jsonify({
            "title": "Study Material / Library",
            "subtitle": "Official reading materials — Income Tax, GST, Companies Act, Partnership, LLP, Gujarat Public Trust, DTAA & more",
            "builder": "Designed & Built by Harsh Pala",
            "note": "Links open official government / regulator websites. Always verify the latest notification on the source site.",
            "categories": LIBRARY_CATALOG,
        })

    print("[library] Study Material / Library routes registered")
