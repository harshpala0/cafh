"""
CA FirmHub — self-healing bootstrap.
Downloads the last known-good main.py from GitHub raw if needed,
optionally injects the Asset Links route, and exposes `app` for gunicorn.
"""
import urllib.request
from pathlib import Path

GOOD_COMMIT = "541da698cfbf70657b298f7ed30073c5355ffeda"
RAW_URL = f"https://raw.githubusercontent.com/harshpala0/cafh/{GOOD_COMMIT}/main.py"
CACHE = Path(__file__).resolve().parent / "static" / "_main_chunks" / "full_main_cache.py"

ASSETLINKS_SNIPPET = '''
@app.route("/.well-known/assetlinks.json")
def assetlinks():
    """Digital Asset Links for Android TWA / Play Store."""
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
