"""CA FirmHub — Excel import with Compliance Packs (loader).
Designed & Built by Harsh Pala.
"""
from pathlib import Path

def register_import_packs_enhance(app, helpers):
    body = Path(__file__).resolve().parent / "static" / "_import_packs_body.py"
    ns = {"__name__": "import_packs_body"}
    exec(compile(body.read_text(encoding="utf-8"), str(body), "exec"), ns)
    return ns["register_import_packs_enhance"](app, helpers)
