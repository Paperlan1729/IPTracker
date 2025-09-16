from flask import Flask, request, render_template
import os
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)

# Optionally enable ProxyFix for trusted reverse proxies
if os.getenv("TRUST_PROXY", "0") == "1":
    # Default: trust one proxy in front (adjust as needed)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Create database and table if not exists
def init_db():
    conn = sqlite3.connect("visitors.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS visitors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ip TEXT,
                        browser TEXT,
                        country TEXT,
                        city TEXT,
                        visits INTEGER,
                        last_visit TEXT
                    )''')
    cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_visitors_ip ON visitors(ip)''')
    conn.commit()
    conn.close()

@app.route("/")
def home():
    # Get visitor IP and User-Agent
    # Prefer common proxy headers, then access_route/remote_addr
    ip = (
        request.headers.get('CF-Connecting-IP')
        or request.headers.get('X-Real-IP')
        or (request.headers.get('X-Forwarded-For') or '').split(',')[0].strip()
        or (request.access_route[-1] if request.access_route else None)
        or request.remote_addr
        or "Unknown"
    )
    browser = request.user_agent.string

    # Get location details
    try:
        api_response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        response = api_response.json()
        if response.get("status") == "success":
            country = response.get("country", "Unknown")
            city = response.get("city", "Unknown")
        else:
            country, city = "Unknown", "Unknown"
    except requests.RequestException:
        country, city = "Unknown", "Unknown"

    conn = sqlite3.connect("visitors.db")
    cursor = conn.cursor()

    # Use UTC ISO timestamp and UPSERT to insert/update visitor row
    last_visit = datetime.utcnow().isoformat() + "Z"
    cursor.execute(
        """
        INSERT INTO visitors (ip, browser, country, city, visits, last_visit)
        VALUES (?, ?, ?, ?, 1, ?)
        ON CONFLICT(ip) DO UPDATE SET
            visits = visitors.visits + 1,
            browser = excluded.browser,
            country = excluded.country,
            city = excluded.city,
            last_visit = excluded.last_visit
        """,
        (ip, browser, country, city, last_visit),
    )

    # Retrieve current visit count for this IP
    cursor.execute("SELECT visits FROM visitors WHERE ip=?", (ip,))
    row = cursor.fetchone()
    visits = row[0] if row else 1

    conn.commit()
    conn.close()

    return render_template("index.html", ip=ip, browser=browser, country=country, city=city, visits=visits)

if __name__ == "__main__":
    init_db()
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
