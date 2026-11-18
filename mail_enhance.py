"""CA FirmHub — Client mail. Loads known-good base then enforces per-client send isolation.
Designed & Built by Harsh Pala.
"""
import urllib.request

_BASE = (
    "https://raw.githubusercontent.com/harshpala0/cafh/"
    "c529ec2200677f0dd2086b3440d7eeee41c2c0f5/mail_enhance.py"
)

_src = urllib.request.urlopen(_BASE, timeout=60).read().decode("utf-8")

# Query join: require engagement.client_id; drop global LIMIT 200
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

# Replace send loop with strict per-client isolation
_OLD = '''            sent, skipped, errors = [], [], []
            for r in rows:
                em = (r.get("contact_email") or "").strip()
                if not em or "@" not in em:
                    skipped.append({"id": r["id"], "name": r["name"], "reason": "No contact email"})
                    continue
                text = body.replace("{{client_name}}", r["name"] or "")
                text = text.replace("{{name}}", r["name"] or "")
                cid = int(r["id"])
                if cid in ctx_map and (iq or io or iu):
                    text = _mail_append_ctx(text, ctx_map[cid], iq, io, iu)
                ok, info = _send(
                    [em], subject, text,
                    from_name=from_name,
                    from_email=settings.get("from_email") or "",
                    reply_to=reply_to,
                )
                if ok:
                    sent.append({"id": r["id"], "name": r["name"], "email": em})
                else:
                    errors.append({"id": r["id"], "name": r["name"], "email": em, "error": info})
'''

_NEW = '''            by_id = {}
            for r in rows:
                if isinstance(r, dict) and r.get("id") is not None:
                    by_id[int(r["id"])] = r
            sent, skipped, errors = [], [], []
            for raw_id in client_ids:
                try:
                    cid = int(raw_id)
                except Exception:
                    continue
                r = by_id.get(cid)
                if not r:
                    skipped.append({"id": cid, "name": "?", "reason": "Client not in this firm"})
                    continue
                cname = (r.get("name") or "").strip() or ("Client #%s" % cid)
                em = (r.get("contact_email") or "").strip()
                if not em or "@" not in em:
                    skipped.append({"id": cid, "name": cname, "reason": "No contact email"})
                    continue
                text = body.replace("{{client_name}}", cname).replace("{{name}}", cname)
                if iq or io or iu:
                    only = dict(ctx_map.get(cid) or {})
                    only["pending_queries"] = list(only.get("pending_queries") or [])
                    only["overdue"] = list(only.get("overdue") or [])
                    only["upcoming"] = list(only.get("upcoming") or [])
                    text = _mail_append_ctx(text, only, iq, io, iu)
                ok, info = _send(
                    [em], subject, text,
                    from_name=from_name,
                    from_email=settings.get("from_email") or "",
                    reply_to=reply_to,
                )
                if ok:
                    sent.append({"id": cid, "name": cname, "email": em})
                else:
                    errors.append({"id": cid, "name": cname, "email": em, "error": info})
'''

if _OLD not in _src:
    print("[mail] WARN: send loop pattern not found — base may have changed")
else:
    _src = _src.replace(_OLD, _NEW, 1)
    print("[mail] Per-client send loop applied")

_ns = {}
exec(compile(_src, "mail_enhance_base.py", "exec"), _ns)
register_mail_enhance = _ns["register_mail_enhance"]
