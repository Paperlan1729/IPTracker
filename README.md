# IPtracker

Simple Flask app that tracks visitors by IP, browser, geolocation (best effort), and visit count using SQLite.

## Features
- Records IP, browser, country, city, visit count, last visit time (UTC ISO)
- Uses SQLite (`visitors.db`)
- Shows client public IP in-page via `api.ipify.org`

## Requirements
- Python 3.9+

## Setup
```bash
python -m venv .venv
# Windows PowerShell
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run (local)
```bash
python app.py
# open http://127.0.0.1:5000/
```

To test from other devices on your LAN:
```bash
python -c "from app import app, init_db; init_db(); app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)"
# then open http://<your_pc_lan_ip>:5000/ from phone/computer on same Wi‑Fi
```

## Reverse proxy / real client IPs
The app prefers `CF-Connecting-IP`, then `X-Real-IP`, then `X-Forwarded-For` (first IP), and falls back to Flask `access_route`/`remote_addr`.
If you're behind a trusted proxy, enable ProxyFix and configure host/port/debug via env vars.

Example Nginx snippet:
```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Real-IP $remote_addr;
```

## Environment variables
- `FLASK_HOST` (default `127.0.0.1`)
- `FLASK_PORT` (default `5000`)
- `FLASK_DEBUG` (`1` or `0`, default `1`)
- `TRUST_PROXY` (`1` to enable ProxyFix, default `0`)

Example:
```bash
$env:FLASK_HOST="0.0.0.0"; $env:FLASK_PORT="5000"; $env:FLASK_DEBUG="0"; $env:TRUST_PROXY="1"; python app.py
```

## Notes
- Private IPs (10.x, 172.16–31.x, 192.168.x) won’t geolocate reliably.
- Free IP APIs are rate-limited; production use should add caching and error handling (already added basic timeout/handling).
- Do not run `debug=True` in production.
