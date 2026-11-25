"""CA FirmHub — Excel import with Compliance Packs.
Loads last known-good body and applies auth + column-alias fixes.
Designed & Built by Harsh Pala.
"""
import urllib.request

# Pre-placeholder, known-good import body (packs + contact fields)
_BODY_URL = (
    "https://raw.githubusercontent.com/harshpala0/cafh/"
    "72cc50aab88dea2a7beed577b259000808d362b2/import_packs_enhance.py"
)


def register_import_packs_enhance(app, helpers):
    with urllib.request.urlopen(_BODY_URL, timeout=60) as r:
        src = r.read().decode("utf-8")

    # Restore JWT gate (view_functions override had dropped @login_required)
    src = src.replace(
        "def clients_import_template():\n            return enhanced_template()",
        "@login_required\n        def clients_import_template():\n            return enhanced_template()",
        1,
    )
    src = src.replace(
        "def clients_import_excel():\n            return enhanced_import()",
        "@login_required\n        def clients_import_excel():\n            return enhanced_import()",
        1,
    )

    # Prefer "Clients Import" sheet + case-insensitive header aliases
    old_read = (
        "        try:\n"
        "            raw = f.read()\n"
        "            df = pd.read_csv(io.BytesIO(raw)) if f.filename.lower().endswith(\".csv\") else pd.read_excel(io.BytesIO(raw))\n"
        "        except Exception as e:\n"
        "            return jsonify({\"detail\": f\"Could not read file: {e}\"}), 400\n"
        "        df.columns = [str(c).strip() for c in df.columns]\n"
        "        if \"Name of Client\" not in df.columns:\n"
        "            return jsonify({\"detail\": \"Missing required column: Name of Client\"}), 400\n"
    )
    new_read = (
        "        try:\n"
        "            raw = f.read()\n"
        "            if f.filename.lower().endswith(\".csv\"):\n"
        "                df = pd.read_csv(io.BytesIO(raw))\n"
        "            else:\n"
        "                try:\n"
        "                    df = pd.read_excel(io.BytesIO(raw), sheet_name=\"Clients Import\")\n"
        "                except Exception:\n"
        "                    df = pd.read_excel(io.BytesIO(raw), sheet_name=0)\n"
        "        except Exception as e:\n"
        "            return jsonify({\"detail\": f\"Could not read file: {e}\"}), 400\n"
        "        df.columns = [\" \".join(str(c).split()) for c in df.columns]\n"
        "        _alias = {\n"
        "            \"name of client\": \"Name of Client\",\n"
        "            \"client name\": \"Name of Client\",\n"
        "            \"client\": \"Name of Client\",\n"
        "            \"type of entity\": \"Type of Entity\",\n"
        "            \"entity type\": \"Type of Entity\",\n"
        "            \"entity\": \"Type of Entity\",\n"
        "            \"pan\": \"PAN\",\n"
        "            \"contact person\": \"Contact Person\",\n"
        "            \"contact number\": \"Contact Number\",\n"
        "            \"phone\": \"Contact Number\",\n"
        "            \"mobile\": \"Contact Number\",\n"
        "            \"contact email\": \"Contact Email\",\n"
        "            \"email\": \"Contact Email\",\n"
        "            \"e-mail\": \"Contact Email\",\n"
        "            \"address\": \"Address\",\n"
        "            \"type of engagement\": \"Type of Engagement\",\n"
        "            \"engagement\": \"Type of Engagement\",\n"
        "            \"engagement type\": \"Type of Engagement\",\n"
        "            \"compliance packs\": \"Compliance Packs\",\n"
        "            \"packs\": \"Compliance Packs\",\n"
        "            \"tax audit applicable\": \"Tax Audit Applicable\",\n"
        "            \"tax audit\": \"Tax Audit Applicable\",\n"
        "        }\n"
        "        rename = {}\n"
        "        for c in list(df.columns):\n"
        "            key = c.strip().lower()\n"
        "            if key in _alias and _alias[key] not in df.columns and _alias[key] not in rename.values():\n"
        "                rename[c] = _alias[key]\n"
        "        if rename:\n"
        "            df = df.rename(columns=rename)\n"
        "        if \"Name of Client\" not in df.columns:\n"
        "            return jsonify({\n"
        "                \"detail\": \"Missing required column: Name of Client. \"\n"
        "                          \"Download the sample template and keep the header row.\"\n"
        "            }), 400\n"
    )
    if old_read in src:
        src = src.replace(old_read, new_read, 1)

    ns = {"__name__": "import_packs_enhance"}
    exec(compile(src, "import_packs_enhance_body.py", "exec"), ns)
    return ns["register_import_packs_enhance"](app, helpers)
