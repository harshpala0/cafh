"""CA FirmHub — mail context (loads base + strict per-client isolation).
Designed & Built by Harsh Pala.
"""
import urllib.request

_BASE = (
    "https://raw.githubusercontent.com/harshpala0/cafh/"
    "c529ec2200677f0dd2086b3440d7eeee41c2c0f5/mail_context_enhance.py"
)

_src = urllib.request.urlopen(_BASE, timeout=60).read().decode("utf-8")

# Drop global LIMIT so later clients are not starved of query rows
_src = _src.replace(
    "ORDER BY q.sr_no NULLS LAST, q.id\n                LIMIT 200",
    "ORDER BY e.client_id, q.sr_no NULLS LAST, q.id",
)
_src = _src.replace(
    "JOIN engagements e ON e.id = q.engagement_id\n"
    "                WHERE q.firm_id = %s AND e.client_id IN ({ph})",
    "INNER JOIN engagements e ON e.id = q.engagement_id AND e.firm_id = q.firm_id\n"
    "                WHERE q.firm_id = %s AND e.client_id IS NOT NULL AND e.client_id IN ({ph})",
)
# Include client_name in preview payload
_src = _src.replace(
    '"pending_queries_count": len(v["pending_queries"]),',
    '"client_name": "",\n                    "pending_queries_count": len(v["pending_queries"]),',
    1,
)

_ns = {}
exec(compile(_src, "mail_context_enhance_base.py", "exec"), _ns)
register_mail_context = _ns["register_mail_context"]
