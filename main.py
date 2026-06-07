import json
import urllib.request
import urllib.error
import ssl
import os
import re
import sys

# Helper to read from .env file
def load_env(env_path=".env"):
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

# Load configuration from .env
load_env()
CLIENT_KEY = os.getenv("CLIENT_KEY")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Endpoints to attempt.
# If running on the VPS itself, NAT loopback might block the public domain,
# so the script falls back to the local Docker HTTPS port.
URLS_TO_TRY = [
    ("https://mastodon.24x7stream.shop/api/v1/statuses", True, {}),
    ("https://localhost:8443/api/v1/statuses", False, {"Host": "mastodon.24x7stream.shop"}),
    ("http://localhost:8080/api/v1/statuses", True, {"Host": "mastodon.24x7stream.shop"}),
]

def fetch_traffic_summary():
    url = "https://24x7stream.shop/product/21/"
    print(f"Fetching page views summary from {url}...")
    
    # Use unverified context to avoid SSL handshake issues on the VPS if any
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    
    try:
        with urllib.request.urlopen(req, context=context, timeout=15) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching page views: {e}")
        return None

    # Parse Total Views
    total_views_match = re.search(r'(\d+)\s+Total Views', html)
    total_views = total_views_match.group(1) if total_views_match else "N/A"
    
    # Parse Today's Views
    today_views_match = re.search(r'<div class="floating-counter"[^>]*>\s*([\d,]+)\s*Views\s*</div>', html, re.DOTALL)
    today_views = today_views_match.group(1) if today_views_match else "N/A"
    
    # Parse Top 4 locations
    top_4 = []
    card_pattern = re.compile(
        r'<h6 class="card-title text-secondary">([^<]+)</h6>\s*'
        r'<small class="text-muted d-block mb-2">([^<]+)</small>\s*'
        r'<h4 class="card-text text-info">([^<]+)</h4>',
        re.DOTALL
    )
    for match in card_pattern.finditer(html):
        country, city, views = match.groups()
        top_4.append({
            "country": country.strip(),
            "city": city.strip(),
            "views": views.strip()
        })
        
    # Parse Weekly Traffic
    weekly_dates = []
    weekly_views = []
    weekly_dates_match = re.search(r'const weeklyDates = (\[[^\]]+\]);', html)
    weekly_views_match = re.search(r'const weeklyViews = (\[[^\]]+\]);', html)
    if weekly_dates_match and weekly_views_match:
        try:
            weekly_dates = json.loads(weekly_dates_match.group(1))
            weekly_views = json.loads(weekly_views_match.group(1))
        except Exception:
            pass

    # Build the status message
    msg = f"📊 Page Views Summary: Starter Streaming Plan\n"
    msg += f"🔗 https://24x7stream.shop/product/21/\n\n"
    msg += f"📈 Total Views: {total_views}\n"
    msg += f"🔥 Today's Views: {today_views}\n\n"
    
    if top_4:
        msg += "🌍 Top Traffic Locations:\n"
        for idx, item in enumerate(top_4, 1):
            msg += f"  {idx}. {item['country']} ({item['city']}): {item['views']} views\n"
        msg += "\n"
        
    if weekly_dates and weekly_views:
        msg += "📅 Last 7 Days Traffic:\n"
        for date, val in zip(weekly_dates, weekly_views):
            msg += f"  • {date}: {val} views\n"
            
    return msg

def generate_embed_html(post_url):
    match = re.match(r'^(https?://[^/]+)/(@[^/]+)/(\d+)', post_url)
    if match:
        base_url = match.group(1)
        username = match.group(2)
        domain = base_url.split("://")[-1]
        base_url_slash = base_url if base_url.endswith("/") else base_url + "/"
        
        embed_html = (
            f'<!DOCTYPE html>\n'
            f'<html lang="en">\n'
            f'<head>\n'
            f'    <meta charset="UTF-8">\n'
            f'    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'    <title>Mastodon Post Embed</title>\n'
            f'    <style>\n'
            f'        html, body {{\n'
            f'            margin: 0;\n'
            f'            padding: 0;\n'
            f'            width: 100%;\n'
            f'            min-height: 100vh;\n'
            f'            background-color: #f5f6f8;\n'
            f'            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;\n'
            f'        }}\n'
            f'        .container {{\n'
            f'            display: flex;\n'
            f'            justify-content: center;\n'
            f'            align-items: center;\n'
            f'            width: 100%;\n'
            f'            min-height: 100vh;\n'
            f'            padding: 20px;\n'
            f'            box-sizing: border-box;\n'
            f'        }}\n'
            f'        @media (max-width: 600px) {{\n'
            f'            .container {{\n'
            f'                align-items: flex-start;\n'
            f'                padding: 10px;\n'
            f'            }}\n'
            f'        }}\n'
            f'    </style>\n'
            f'</head>\n'
            f'<body>\n'
            f'    <div class="container">\n'
            f'        <blockquote class="mastodon-embed" data-embed-url="{post_url}/embed" '
            f'style="background: #FCF8FF; border-radius: 8px; border: 1px solid #C9C4DA; margin: 0 auto; max-width: 540px; min-width: 270px; width: 100%; overflow: hidden; padding: 0;"> '
            f'<a href="{post_url}" target="_blank" style="align-items: center; color: #1C1A25; display: flex; flex-direction: column; font-family: system-ui, -apple-system, BlinkMacSystemFont, \'Segoe UI\', Oxygen, Ubuntu, Cantarell, \'Fira Sans\', \'Droid Sans\', \'Helvetica Neue\', Roboto, sans-serif; font-size: 14px; justify-content: center; letter-spacing: 0.25px; line-height: 20px; padding: 24px; text-decoration: none;"> '
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="32" height="32" viewBox="0 0 79 75"><path d="M63 45.3v-20c0-4.1-1-7.3-3.2-9.7-2.1-2.4-5-3.7-8.5-3.7-4.1 0-7.2 1.6-9.3 4.7l-2 3.3-2-3.3c-2-3.1-5.1-4.7-9.2-4.7-3.5 0-6.4 1.3-8.6 3.7-2.1 2.4-3.1 5.6-3.1 9.7v20h8V25.9c0-4.1 1.7-6.2 5.2-6.2 3.8 0 5.8 2.5 5.8 7.4V37.7H44V27.1c0-4.9 1.9-7.4 5.8-7.4 3.5 0 5.2 2.1 5.2 6.2V45.3h8ZM74.7 16.6c.6 6 .1 15.7.1 17.3 0 .5-.1 4.8-.1 5.3-.7 11.5-8 16-15.6 17.5-.1 0-.2 0-.3 0-4.9 1-10 1.2-14.9 1.4-1.2 0-2.4 0-3.6 0-4.8 0-9.7-.6-14.4-1.7-.1 0-.1 0-.1 0s-.1 0-.1 0 0 .1 0 .1 0 0 0 0c.1 1.6.4 3.1 1 4.5.6 1.7 2.9 5.7 11.4 5.7 5 0 9.9-.6 14.8-1.7 0 0 0 0 0 0 .1 0 .1 0 .1 0 0 .1 0 .1 0 .1.1 0 .1 0 .1.1v5.6s0 .1-.1.1c0 0 0 0 0 .1-1.6 1.1-3.7 1.7-5.6 2.3-.8.3-1.6.5-2.4.7-7.5 1.7-15.4 1.3-22.7-1.2-6.8-2.4-13.8-8.2-15.5-15.2-.9-3.8-1.6-7.6-1.9-11.5-.6-5.8-.6-11.7-.8-17.5C3.9 24.5 4 20 4.9 16 6.7 7.9 14.1 2.2 22.3 1c1.4-.2 4.1-1 16.5-1h.1C51.4 0 56.7.8 58.1 1c8.4 1.2 15.5 7.5 16.6 15.6Z" fill="currentColor"/></svg> '
            f'<div style="color: #787588; margin-top: 16px;">Post by {username}@{domain}</div> '
            f'<div style="font-weight: 500;">View on Mastodon</div> '
            f'</a> '
            f'</blockquote>\n'
            f'    </div>\n'
            f'    <script data-allowed-prefixes="{base_url_slash}" async src="{base_url_slash}embed.js"></script>\n'
            f'</body>\n'
            f'</html>'
        )
        return embed_html
    return post_url

def post_status(status_text):
    payload = json.dumps({"status": status_text}).encode("utf-8")
    
    for url, verify_ssl, extra_headers in URLS_TO_TRY:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "MastodonPythonPoster/1.0",
            **extra_headers
        }
        
        # Set up SSL validation context
        if not verify_ssl:
            context = ssl._create_unverified_context()
        else:
            context = ssl.create_default_context()
            
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        
        try:
            print(f"Attempting to post to {url} (verify_ssl={verify_ssl})...")
            # 10 second timeout to fail-fast if loopback routing fails on the VPS
            with urllib.request.urlopen(req, context=context, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                print("\nSuccessfully posted!")
                print(f"Post URL: {res_json.get('url')}")
                return {
                    "success": True,
                    "url": res_json.get('url'),
                    "endpoint": url
                }
        except Exception as e:
            print(f"Failed: {e}\n")
            continue
            
    print("Error: Could not connect to any of the Mastodon endpoints.")
    return {
        "success": False,
        "error": "Could not connect to any of the Mastodon endpoints"
    }

def start_server():
    from flask import Flask, jsonify, request
    
    app = Flask(__name__)
    
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "status": "online",
            "message": "Mastodon Traffic Poster API is running."
        })
        
    @app.route("/post-traffic", methods=["POST", "GET"])
    def post_traffic():
        status_text = fetch_traffic_summary()
        if not status_text:
            return "Failed to fetch traffic summary from page", 500
            
        res = post_status(status_text)
        if res["success"]:
            return generate_embed_html(res["url"]), 200
        else:
            return res["error"], 500
            
    @app.route("/post", methods=["POST"])
    def post_custom():
        data = request.get_json(silent=True) or {}
        status_text = data.get("status")
        if not status_text:
            return "Missing 'status' in request body", 400
            
        res = post_status(status_text)
        if res["success"]:
            return generate_embed_html(res["url"]), 200
        else:
            return res["error"], 500

    print("Starting Flask API server on port 5050...")
    app.run(host="0.0.0.0", port=5050)

if __name__ == "__main__":
    if "--server" in sys.argv:
        start_server()
    else:
        status_text = fetch_traffic_summary()
        if status_text:
            post_status(status_text)
        else:
            print("Failed to fetch traffic summary, aborting post.")

