"""Load compliance enhance body from static/_compliance_parts."""
from pathlib import Path

def register_compliance_enhance(app, helpers):
    parts_dir = Path(__file__).resolve().parent / "static" / "_compliance_parts"
    parts = sorted(parts_dir.glob("part_*.txt"))
    if not parts:
        print("[compliance] no parts found — skipping")
        return
    src = "".join(p.read_text(encoding="utf-8") for p in parts)
    ns = {"__name__": "compliance_enhance_body"}
    exec(compile(src, str(parts_dir / "body.py"), "exec"), ns)
    ns["register_compliance_enhance"](app, helpers)
