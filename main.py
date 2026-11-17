"""CA FirmHub bootstrap loader — Designed & Built by Harsh Pala."""
from pathlib import Path
_root = Path(__file__).resolve().parent
_parts = sorted(_root.glob("bootstrap_part_*.txt"))
if not _parts:
    _parts = sorted((_root / "static").glob("bootstrap_part_*.txt"))
if not _parts:
    raise SystemExit("CA FirmHub: bootstrap_part_*.txt missing")
_src = "".join(p.read_text(encoding="utf-8") for p in _parts)
exec(compile(_src, str(_root / "main_boot.py"), "exec"), globals())
