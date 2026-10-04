# CA FirmHub — Restore & Mobile PWA

## Current status
- `static/manifest.json`, `static/sw.js`, `android/README.md` are already on this repo.
- `main.py` was temporarily reduced; restore it from your backup (or the file provided in chat).
- Replace `static/index.html` with the mobile-enhanced version provided in chat.

## Optional: Digital Asset Links (for Play Store TWA)
After restoring main.py, add this route after `static_files`:

```python
@app.route("/.well-known/assetlinks.json")
def assetlinks():
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
```

## Mobile / PWA changes in index.html
- Hamburger menu + slide-out sidebar on screens ≤900px
- Responsive login, tables, cards
- PWA meta tags + service worker registration
- Desktop layout unchanged

## Play Store
See `android/README.md` (Bubblewrap TWA).
