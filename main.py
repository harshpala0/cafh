"""
CA FirmHub — self-healing bootstrap.
Injects mobile/PWA, Portal, Compliance, Ops, Notify, Cron, Verify, Library, Import Packs, MRL Maker.
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
    import os as _os
    data = [{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": _os.environ.get("TWA_PACKAGE", "com.cafirmhub.app"),
            "sha256_cert_fingerprints": [
                _os.environ.get("TWA_SHA256", "REPLACE_WITH_YOUR_KEYSTORE_SHA256")
            ]
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
<link rel="manifest" href="/static/manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/icons/icon-192.png">
"""

_MOBILE_BODY = (
    '<script src="/static/mobile.js" defer></script>\n'
    '<script src="/static/staff-ui.js" defer></script>\n'
    '<script src="/static/compliance-ui.js" defer></script>\n'
    '<script src="/static/ops-ui.js" defer></script>\n'
    '<script src="/static/notify-ui.js" defer></script>\n'
    '<script src="/static/verify-ui.js" defer></script>\n'
    '<script src="/static/library-ui.js" defer></script>\n'
    '<script src="/static/mrl-ui.js" defer></script>\n'
    '<script>if ("serviceWorker" in navigator) { navigator.serviceWorker.register("/static/sw.js").catch(function(){}); }</script>\n'
)


def _serve_index_with_mobile():
    try:
        path = Path(__file__).resolve().parent / "static" / "index.html"
        html = path.read_text(encoding="utf-8")
        if "manifest.webmanifest" not in html:
            html = html.replace("</head>", _MOBILE_HEAD + "</head>", 1)
        if "staff-ui.js" not in html and "library-ui.js" not in html:
            idx = html.rfind("</body>")
            if idx != -1:
                html = html[:idx] + _MOBILE_BODY + html[idx:]
        if "mrl-ui.js" not in html and "</body>" in html:
            html = html.replace("</body>", '<script src="/static/mrl-ui.js" defer></script>\n</body>', 1)
        return _Response(html, mimetype="text/html")
    except Exception as e:
        return _Response(f"Error loading app: {e}", status=500, mimetype="text/plain")


try:
    app.view_functions["index"] = lambda: _serve_index_with_mobile()
except Exception:
    try:
        @app.route("/")
        def index():
            return _serve_index_with_mobile()
    except Exception as e:
        print("[CA FirmHub] index inject:", e)


try:
    from portal import register_portal
    register_portal(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
        "qry_id": _ns.get("qry_id"),
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
    from import_packs_enhance import register_import_packs_enhance
    register_import_packs_enhance(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
        "qry_id": _ns.get("qry_id"),
    })
except Exception as _imp_err:
    print("[CA FirmHub] Import packs enhance not loaded:", _imp_err)


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


try:
    from cron_enhance import register_cron_enhance
    register_cron_enhance(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
    })
except Exception as _cron_err:
    print("[CA FirmHub] Cron enhance not loaded:", _cron_err)


try:
    from verify_enhance import register_verify_enhance
    register_verify_enhance(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
    })
except Exception as _verify_err:
    print("[CA FirmHub] Verify enhance not loaded:", _verify_err)


try:
    from library_enhance import register_library_enhance
    register_library_enhance(app, {
        "qry": _ns["qry"],
        "execute": _ns["execute"],
        "login_required": _ns["login_required"],
        "require_role": _ns["require_role"],
        "log_action": _ns.get("log_action", lambda *a, **k: None),
    })
except Exception as _lib_err:
    print("[CA FirmHub] Library enhance not loaded:", _lib_err)


try:
    def _sa_with_library():
        path = Path(__file__).resolve().parent / "static" / "superadmin.html"
        html = path.read_text(encoding="utf-8")
        tag = '<script src="/static/superadmin-library.js" defer></script>\n'
        if "superadmin-library.js" not in html and "</body>" in html:
            html = html.replace("</body>", tag + "</body>", 1)
        return _Response(html, mimetype="text/html")
    app.view_functions["superadmin_page"] = _sa_with_library
except Exception as _sa_lib_err:
    print("[CA FirmHub] SuperAdmin library UI inject:", _sa_lib_err)


try:
    from flask import send_from_directory as _sfd_mrl
    @app.route("/tools/mrl")
    def mrl_maker_page():
        return _sfd_mrl("static", "mrl_maker.html")
except Exception as _mrl_route_err:
    print("[CA FirmHub] MRL route:", _mrl_route_err)
