"""
CA FirmHub — bootstrap loader.
Reassembles the full application from static/_main_chunks (pushed in parts
due to connector size limits). Once deployed, you may replace this file
with the single monolithic main.py from your backup; behaviour is identical.
"""
from pathlib import Path

_chunks_dir = Path(__file__).resolve().parent / "static" / "_main_chunks"
_parts = sorted(_chunks_dir.glob("part_*.txt"))
if not _parts:
    raise RuntimeError(
        "CA FirmHub: missing static/_main_chunks/part_*.txt. "
        "Restore main.py from backup or re-push the chunk files."
    )
_code = "".join(p.read_text(encoding="utf-8") for p in _parts)
_ns = {"__name__": "main", "__file__": str(Path(__file__).resolve())}
exec(compile(_code, str(Path(__file__).resolve()), "exec"), _ns)
# Expose Flask app for gunicorn: `gunicorn main:app`
app = _ns["app"]
