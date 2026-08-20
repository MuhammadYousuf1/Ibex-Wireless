import sys
from pathlib import Path

# Make the project root importable so `app`, `data`, and `pages` resolve on Vercel.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from asgiref.wsgi import WsgiToAsgi

from app import app as dash_app

# Dash wraps an underlying Flask (WSGI) application. Vercel's Python runtime
# serves ASGI apps, so adapt the Flask server with asgiref's WSGI-to-ASGI
# bridge. Expose it as `app` — the name Vercel expects for a function handler.
app = WsgiToAsgi(dash_app.server)