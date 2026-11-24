"""
CA FirmHub — Day / Night theme (module-wide).
Injects theme CSS/JS into the main SPA shell without rewriting index.html.
Designed & Built by Harsh Pala.
"""
from pathlib import Path
from flask import Response


_INJECT_HEAD = """
<script>
/* CA FirmHub theme boot — apply before paint */
(function(){try{var t=localStorage.getItem('cfh-theme');if(t!=='dark'&&t!=='light'){t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','light');}})();
</script>
<link rel="stylesheet" href="/static/theme.css" id="cfh-theme-css">
"""

_INJECT_BODY = """
<script src="/static/theme.js" defer></script>
"""


def _inject(html: str) -> str:
    """Inject only at the real document head/body ends — never inside JS template strings."""
    if not html:
        return html
    # First </head> in the first 80KB is the real document head
    if 'id="cfh-theme-css"' not in html:
        idx = html.find('</head>')
        if 0 <= idx < 80000:
            html = html[:idx] + _INJECT_HEAD + html[idx:]
    # Final </body> must sit near the true end of the file
    last_body = html.rfind('</body>')
    if last_body >= max(0, len(html) - 800):
        near = html[max(0, last_body - 300):last_body]
        if '/static/theme.js' not in near:
            html = html[:last_body] + _INJECT_BODY + html[last_body:]
    return html


def register_theme_enhance(app, helpers=None):
    """Wrap the root HTML response to inject day/night theme assets."""

    endpoint = None
    for r in app.url_map.iter_rules():
        if r.rule == '/' and 'GET' in (r.methods or set()):
            endpoint = r.endpoint
            break

    view = app.view_functions.get(endpoint) if endpoint else None
    if not view:
        @app.route('/')
        def cfh_themed_index():
            path = Path(__file__).resolve().parent / 'static' / 'index.html'
            html = path.read_text(encoding='utf-8', errors='replace') if path.exists() else '<html><body>CA FirmHub</body></html>'
            return Response(_inject(html), mimetype='text/html')
        print('[CA FirmHub] Day/Night theme enhance registered (direct /)')
        return

    def themed_index(*args, **kwargs):
        resp = view(*args, **kwargs)
        try:
            if isinstance(resp, Response):
                ctype = (resp.headers.get('Content-Type') or '')
                data = resp.get_data(as_text=True)
                if data and ('text/html' in ctype or '<html' in data[:200].lower()):
                    resp.set_data(_inject(data))
                    if 'Content-Type' not in resp.headers:
                        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
                return resp
            if isinstance(resp, str) and '<html' in resp[:500].lower():
                return Response(_inject(resp), mimetype='text/html')
            if isinstance(resp, tuple) and resp and isinstance(resp[0], str) and '<html' in resp[0][:500].lower():
                return (Response(_inject(resp[0]), mimetype='text/html'),) + resp[1:]
        except Exception as ex:
            print('[CA FirmHub] theme inject skip:', ex)
            return resp
        return resp

    app.view_functions[endpoint] = themed_index
    print('[CA FirmHub] Day/Night theme enhance registered on', endpoint)
