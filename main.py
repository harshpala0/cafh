"""CA FirmHub emergency loader — restores last known-good bootstrap, then adds MRL routes.
Designed & Built by Harsh Pala.
"""
import urllib.request
from pathlib import Path

_RESTORE = (
    "https://raw.githubusercontent.com/harshpala0/cafh/"
    "c529ec2200677f0dd2086b3440d7eeee41c2c0f5/main.py"
)
print("[CA FirmHub] Emergency load from", _RESTORE)
with urllib.request.urlopen(_RESTORE, timeout=90) as _r:
    _src = _r.read().decode("utf-8")
exec(compile(_src, "main_restored.py", "exec"), globals())

# --- Statutory MRL: Company vs LLP (chunked or full HTML) ---
try:
    from flask import send_from_directory as _sfd_mrl, Response as _MrlResp

    def _serve_mrl_html(stem):
        root = Path(__file__).resolve().parent / "static"
        full = root / f"{stem}.html"
        if full.exists() and full.stat().st_size > 2000:
            return _sfd_mrl("static", f"{stem}.html")
        parts = sorted(root.glob(f"{stem}_part_*.txt"))
        if parts:
            html = "".join(p.read_text(encoding="utf-8") for p in parts)
            return _MrlResp(html, mimetype="text/html; charset=utf-8")
        return _MrlResp(f"MRL tool '{stem}' not installed.", status=404, mimetype="text/plain")

    @app.route("/tools/mrl/company")
    def mrl_company_page():
        return _serve_mrl_html("mrl_company")

    @app.route("/tools/mrl/llp")
    def mrl_llp_page():
        return _serve_mrl_html("mrl_llp")

    print("[CA FirmHub] MRL company/LLP routes registered")
except Exception as _mrl_err:
    print("[CA FirmHub] MRL company/LLP routes:", _mrl_err)


# --- Day / Night theme (module-wide) ---
try:
    from theme_enhance import register_theme_enhance
    register_theme_enhance(app)
except Exception as _theme_err:
    print("[CA FirmHub] Theme enhance:", _theme_err)
