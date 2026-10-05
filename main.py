"""
CA FirmHub — self-healing bootstrap.
Injects mobile/PWA, Client Portal, Compliance, Staff UI, Ops UI, Notify.
"""
import urllib.request
from pathlib import Path

GOOD_COMMIT = "541da698cfbf70657b298f7ed30073c5355ffeda"
RAW_URL = f"https://raw.githubusercontent.com/harshpala0/cafh/{GOOD_COMMIT}/main.py"
CACHE = Path(__file__).resolve().parent / "static" / "_main_chunks" / "full_main_cache.py"

ASSETLINKS_SNIPPET = '''
@app.route("/.well-known/assetlinks.json")
def assetlinks():
    import json as _json
    data = [{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "com.cafirmhub.app",
            "sha256_cert_fingerprints": ["REPLACE_WITH_YOUR_KEYSTORE_SHA256"]
        }
    }]
    return Response(_json.dumps(data), mimetype="application/json")
'''


def _load_source():
    chunks_dir = Path(__file__).resolve().parent / "static" / "_main_chunks"
    parts = sorted(chunks_dir.glob("part_*.txt"))
    if parts and sum(p.stat().st_size for p in parts) > 100000:
        return "".join(p.read_text(encoding="utf-8") for p in parts)
    if CACHE.exists() and CACHE.stat().st_size > 100000:
        return CACHE.read_text(encoding="utf-8")
    print("[CA FirmHub] Downloading application source from GitHub…")
    with urllib.request.urlopen(RAW_URL, timeout=60) as r:
        src = r.read().decode("utf-8")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(src, encoding="utf-8")
    return src


def _inject_assetlinks(src: str) -> str:
    if "assetlinks" in src:
        return src
    marker = 'def static_files(fn):\n    return send_from_directory("static", fn)\n'
    if marker in src:
        return src.replace(marker, marker + "\n" + ASSETLINKS_SNIPPET + "\n", 1)
    return src


_src = _inject_assetlinks(_load_source())
_ns = {"__name__": "main", "__file__": str(Path(__file__).resolve())}
exec(compile(_src, str(Path(__file__).resolve()), "exec"), _ns)
app = _ns["app"]

from flask import Response as _Response

_MOBILE_HEAD = """
<meta name="theme-color" content="#003366">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="CA FirmHub">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="/static/app_logo.png">
<link rel="manifest" href="/static/manifest.json">
<link rel="stylesheet" href="/static/mobile-enhancements.css">
"""
_MOBILE_BODY = (
    '<script src="/static/mobile-enhancements.js" defer></script>\n'
    '<script src="/static/compliance-ui.js" defer></script>\n'
    '<script src="/static/staff-ui.js" defer></script>\n'
    '<script src="/static/ops-ui.js" defer></script>\n'
    '<script src="/static/notify-ui.js" defer></script>\n'
)


def _serve_index_with_mobile():
    path = Path(__file__).resolve().parent / "static" / "index.html"
    html = path.read_text(encoding="utf-8")
    if "mobile-enhancements.css" not in html:
        if "</head>" in html:
            html = html.replace("</head>", _MOBILE_HEAD + "</head>", 1)
        html = html.replace(
            'content="width=device-width, initial-scale=1.0"',
            'content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1"',
            1,
        )
    if "mobile-enhancements.js" not in html:
        idx = html.rfind("</body>")
        if idx != -1:
            html = html[:idx] + _MOBILE_BODY + html[idx:]
    else:
        for script in ("staff-ui.js", "ops-ui.js", "compliance-ui.js", "notify-ui.js"):
            tag = f'<script src="/static/{script}" defer></script>'
            if script not in html and "</body>" in html:
                idx = html.rfind("</body>")
                html = html[:idx] + tag + "\n" + html[idx:]
    return _Response(html, mimetype="text/html")


try:
    app.view_functions["index"] = lambda: _serve_index_with_mobile()
except Exception:
    @app.route("/", endpoint="index_mobile_override")
    def _index_mobile_override():
        return _serve_index_with_mobile()


try:
    from portal import register_portal
    register_portal(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
        "upload_to_r2": _ns.get("_upload_to_r2"),
        "hash_pw": _ns.get("hash_pw"),
    })
except Exception as _portal_err:
    print("[CA FirmHub] Portal module not loaded:", _portal_err)


try:
    from compliance_enhance import register_compliance_enhance
    register_compliance_enhance(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
        "qry_id": _ns.get("qry_id"),
    })
except Exception as _comp_err:
    print("[CA FirmHub] Compliance enhance not loaded:", _comp_err)


try:
    from ops_enhance import register_ops_enhance
    register_ops_enhance(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
    })
except Exception as _ops_err:
    print("[CA FirmHub] Ops enhance not loaded:", _ops_err)


try:
    from notify_enhance import register_notify_enhance
    register_notify_enhance(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
    })
except Exception as _notify_err:
    print("[CA FirmHub] Notify enhance not loaded:", _notify_err)
