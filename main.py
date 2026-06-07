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
            
    chart_image_bytes = None
    if weekly_dates and weekly_views:
        chart_image_bytes = generate_chart_image(weekly_dates, weekly_views)
        
    return msg, chart_image_bytes

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
            f'    <title>Mastodon Broadcast Successful</title>\n'
            f'    <link rel="icon" type="image/png" href="https://avatars.githubusercontent.com/u/67197854">\n'
            f'    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">\n'
            f'    <style>\n'
            f'        :root {{\n'
            f'            --bg-color: #03030d;\n'
            f'            --card-bg: rgba(10, 10, 25, 0.45);\n'
            f'            --accent-primary: #00f0ff;\n'
            f'            --accent-secondary: #ff007f;\n'
            f'            --accent-tertiary: #b432ff;\n'
            f'            --text-main: #ffffff;\n'
            f'            --text-muted: #8b8ea8;\n'
            f'        }}\n'
            f'        * {{\n'
            f'            box-sizing: border-box;\n'
            f'        }}\n'
            f'        html, body {{\n'
            f'            margin: 0;\n'
            f'            padding: 0;\n'
            f'            width: 100%;\n'
            f'            min-height: 100vh;\n'
            f'            background-color: var(--bg-color);\n'
            f'            font-family: "Outfit", sans-serif;\n'
            f'            color: var(--text-main);\n'
            f'            overflow-x: hidden;\n'
            f'        }}\n'
            f'        .aurora-container {{\n'
            f'            position: fixed;\n'
            f'            width: 100%;\n'
            f'            height: 100%;\n'
            f'            top: 0;\n'
            f'            left: 0;\n'
            f'            overflow: hidden;\n'
            f'            z-index: 0;\n'
            f'            pointer-events: none;\n'
            f'        }}\n'
            f'        .aurora-blob {{\n'
            f'            position: absolute;\n'
            f'            border-radius: 50%;\n'
            f'            filter: blur(120px);\n'
            f'            opacity: 0.35;\n'
            f'            mix-blend-mode: screen;\n'
            f'            animation: floatBlob 25s infinite alternate ease-in-out;\n'
            f'        }}\n'
            f'        .blob-1 {{\n'
            f'            width: 500px;\n'
            f'            height: 500px;\n'
            f'            background: radial-gradient(circle, var(--accent-primary) 0%, transparent 80%);\n'
            f'            top: -100px;\n'
            f'            left: -100px;\n'
            f'        }}\n'
            f'        .blob-2 {{\n'
            f'            width: 600px;\n'
            f'            height: 600px;\n'
            f'            background: radial-gradient(circle, var(--accent-tertiary) 0%, transparent 80%);\n'
            f'            bottom: -150px;\n'
            f'            right: -100px;\n'
            f'            animation-duration: 35s;\n'
            f'        }}\n'
            f'        .blob-3 {{\n'
            f'            width: 400px;\n'
            f'            height: 400px;\n'
            f'            background: radial-gradient(circle, var(--accent-secondary) 0%, transparent 80%);\n'
            f'            top: 40%;\n'
            f'            left: 60%;\n'
            f'            animation-duration: 18s;\n'
            f'        }}\n'
            f'        @keyframes floatBlob {{\n'
            f'            0% {{ transform: translate(0, 0) scale(1); }}\n'
            f'            50% {{ transform: translate(80px, 50px) scale(1.1); }}\n'
            f'            100% {{ transform: translate(-40px, -60px) scale(0.9); }}\n'
            f'        }}\n'
            f'        .grid-overlay {{\n'
            f'            position: fixed;\n'
            f'            top: 0;\n'
            f'            left: 0;\n'
            f'            width: 100%;\n'
            f'            height: 100%;\n'
            f'            background-image: \n'
            f'                linear-gradient(rgba(0, 240, 255, 0.02) 1px, transparent 1px),\n'
            f'                linear-gradient(90deg, rgba(0, 240, 255, 0.02) 1px, transparent 1px);\n'
            f'            background-size: 50px 50px;\n'
            f'            background-position: center;\n'
            f'            transform: perspective(500px) rotateX(60deg) translateY(-30%) translateZ(0);\n'
            f'            transform-origin: top center;\n'
            f'            mask-image: linear-gradient(to bottom, rgba(0,0,0,1), rgba(0,0,0,0));\n'
            f'            -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1), rgba(0,0,0,0));\n'
            f'            z-index: 1;\n'
            f'            animation: gridScroll 20s linear infinite;\n'
            f'            pointer-events: none;\n'
            f'        }}\n'
            f'        @keyframes gridScroll {{\n'
            f'            0% {{ background-position: 0 0; }}\n'
            f'            100% {{ background-position: 0 100%; }}\n'
            f'        }}\n'
            f'        .container {{\n'
            f'            display: flex;\n'
            f'            justify-content: center;\n'
            f'            align-items: flex-start;\n'
            f'            width: 100%;\n'
            f'            min-height: 100vh;\n'
            f'            padding: 40px 20px;\n'
            f'            position: relative;\n'
            f'            z-index: 2;\n'
            f'        }}\n'
            f'        .embed-card {{\n'
            f'            background: var(--card-bg);\n'
            f'            border: 1px solid rgba(0, 240, 255, 0.15);\n'
            f'            border-radius: 24px;\n'
            f'            padding: 35px;\n'
            f'            backdrop-filter: blur(25px);\n'
            f'            -webkit-backdrop-filter: blur(25px);\n'
            f'            box-shadow: \n'
            f'                0 20px 50px rgba(0, 0, 0, 0.6),\n'
            f'                inset 0 0 20px rgba(255, 255, 255, 0.05),\n'
            f'                0 0 40px rgba(0, 240, 255, 0.1);\n'
            f'            max-width: 600px;\n'
            f'            width: 100%;\n'
            f'            display: flex;\n'
            f'            flex-direction: column;\n'
            f'            gap: 25px;\n'
            f'            position: relative;\n'
            f'            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);\n'
        )
        embed_html += (
            f'        }}\n'
            f'        .embed-card::before {{\n'
            f'            content: "";\n'
            f'            position: absolute;\n'
            f'            top: -2px; left: -2px; right: -2px; bottom: -2px;\n'
            f'            background: linear-gradient(45deg, var(--accent-primary), transparent, var(--accent-tertiary), transparent, var(--accent-secondary));\n'
            f'            background-size: 400% 400%;\n'
            f'            z-index: -1;\n'
            f'            border-radius: 26px;\n'
            f'            opacity: 0.2;\n'
            f'            animation: borderGlow 8s linear infinite;\n'
            f'        }}\n'
            f'        @keyframes borderGlow {{\n'
            f'            0% {{ background-position: 0% 50%; }}\n'
            f'            50% {{ background-position: 100% 50%; }}\n'
            f'            100% {{ background-position: 0% 50%; }}\n'
            f'        }}\n'
            f'        .card-header {{\n'
            f'            display: flex;\n'
            f'            align-items: center;\n'
            f'            gap: 15px;\n'
            f'            border-bottom: 1px solid rgba(255, 255, 255, 0.08);\n'
            f'            padding-bottom: 20px;\n'
            f'        }}\n'
            f'        .success-icon {{\n'
            f'            width: 44px;\n'
            f'            height: 44px;\n'
            f'            border-radius: 50%;\n'
            f'            background: rgba(0, 240, 255, 0.1);\n'
            f'            border: 2px solid var(--accent-primary);\n'
            f'            color: var(--accent-primary);\n'
            f'            display: flex;\n'
            f'            align-items: center;\n'
            f'            justify-content: center;\n'
            f'            font-size: 20px;\n'
            f'            font-weight: bold;\n'
            f'            box-shadow: 0 0 15px rgba(0, 240, 255, 0.25);\n'
            f'            animation: pulseSuccess 2s infinite ease-in-out;\n'
            f'            flex-shrink: 0;\n'
            f'        }}\n'
            f'        @keyframes pulseSuccess {{\n'
            f'            0%, 100% {{ box-shadow: 0 0 15px rgba(0, 240, 255, 0.25); transform: scale(1); }}\n'
            f'            50% {{ box-shadow: 0 0 25px rgba(0, 240, 255, 0.5); transform: scale(1.05); }}\n'
            f'        }}\n'
            f'        .header-text h3 {{\n'
            f'            margin: 0;\n'
            f'            font-size: 20px;\n'
            f'            font-weight: 700;\n'
            f'            background: linear-gradient(90deg, #ffffff, #a5a6ff, var(--accent-primary));\n'
            f'            -webkit-background-clip: text;\n'
            f'            -webkit-text-fill-color: transparent;\n'
            f'            letter-spacing: 0.5px;\n'
            f'        }}\n'
            f'        .header-text p {{\n'
            f'            margin: 4px 0 0 0;\n'
            f'            font-size: 13px;\n'
            f'            color: var(--text-muted);\n'
            f'        }}\n'
            f'        .embed-body {{\n'
            f'            display: flex;\n'
            f'            justify-content: center;\n'
            f'            width: 100%;\n'
            f'        }}\n'
            f'        .card-footer {{\n'
            f'            display: flex;\n'
            f'            justify-content: center;\n'
            f'            border-top: 1px solid rgba(255, 255, 255, 0.08);\n'
            f'            padding-top: 20px;\n'
            f'        }}\n'
            f'        .action-btn {{\n'
            f'            display: inline-block;\n'
            f'            padding: 12px 32px;\n'
            f'            background: linear-gradient(90deg, var(--accent-primary), var(--accent-tertiary));\n'
            f'            border: none;\n'
            f'            color: white;\n'
            f'            text-decoration: none;\n'
            f'            border-radius: 12px;\n'
            f'            font-weight: 600;\n'
            f'            font-size: 14px;\n'
            f'            box-shadow: 0 4px 20px rgba(0, 240, 255, 0.3);\n'
            f'            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);\n'
            f'        }}\n'
            f'        .action-btn:hover {{\n'
            f'            transform: translateY(-2px);\n'
            f'            box-shadow: 0 8px 25px rgba(0, 240, 255, 0.5), 0 0 15px rgba(180, 50, 255, 0.3);\n'
            f'            background: linear-gradient(90deg, #00e5ff, #c24eff);\n'
            f'        }}\n'
            f'        @keyframes fadeInUp {{\n'
            f'            0% {{ opacity: 0; transform: translateY(20px); }}\n'
            f'            100% {{ opacity: 1; transform: translateY(0); }}\n'
            f'        }}\n'
            f'        @media (max-width: 600px) {{\n'
            f'            .container {{\n'
            f'                align-items: flex-start;\n'
            f'                padding: 15px;\n'
            f'            }}\n'
            f'            .embed-card {{\n'
            f'                padding: 20px;\n'
            f'                border-radius: 18px;\n'
            f'                gap: 15px;\n'
            f'            }}\n'
            f'        }}\n'
            f'    </style>\n'
            f'</head>\n'
            f'<body>\n'
            f'    <div class="aurora-container">\n'
            f'        <div class="aurora-blob blob-1"></div>\n'
            f'        <div class="aurora-blob blob-2"></div>\n'
            f'        <div class="aurora-blob blob-3"></div>\n'
            f'    </div>\n'
            f'    <div class="grid-overlay"></div>\n'
            f'    <div class="container">\n'
            f'        <div class="embed-card">\n'
            f'            <div class="card-header">\n'
            f'                <div class="success-icon">✓</div>\n'
            f'                <div class="header-text">\n'
            f'                    <h3>Report Broadcast Successful</h3>\n'
            f'                    <p>Metrics page updated and shared on Mastodon</p>\n'
            f'                </div>\n'
            f'            </div>\n'
            f'            <div class="embed-body">\n'
            f'                <blockquote class="mastodon-embed" data-embed-url="{post_url}/embed" '
            f'style="background: #FCF8FF; border-radius: 8px; border: 1px solid #C9C4DA; margin: 0 auto; max-width: 540px; min-width: 270px; width: 100%; overflow: hidden; padding: 0;"> '
            f'<a href="{post_url}" target="_blank" style="align-items: center; color: #1C1A25; display: flex; flex-direction: column; font-family: system-ui, -apple-system, BlinkMacSystemFont, \'Segoe UI\', Oxygen, Ubuntu, Cantarell, \'Fira Sans\', \'Droid Sans\', \'Helvetica Neue\', Roboto, sans-serif; font-size: 14px; justify-content: center; letter-spacing: 0.25px; line-height: 20px; padding: 24px; text-decoration: none;"> '
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="32" height="32" viewBox="0 0 79 75"><path d="M63 45.3v-20c0-4.1-1-7.3-3.2-9.7-2.1-2.4-5-3.7-8.5-3.7-4.1 0-7.2 1.6-9.3 4.7l-2 3.3-2-3.3c-2-3.1-5.1-4.7-9.2-4.7-3.5 0-6.4 1.3-8.6 3.7-2.1 2.4-3.1 5.6-3.1 9.7v20h8V25.9c0-4.1 1.7-6.2 5.2-6.2 3.8 0 5.8 2.5 5.8 7.4V37.7H44V27.1c0-4.9 1.9-7.4 5.8-7.4 3.5 0 5.2 2.1 5.2 6.2V45.3h8ZM74.7 16.6c.6 6 .1 15.7.1 17.3 0 .5-.1 4.8-.1 5.3-.7 11.5-8 16-15.6 17.5-.1 0-.2 0-.3 0-4.9 1-10 1.2-14.9 1.4-1.2 0-2.4 0-3.6 0-4.8 0-9.7-.6-14.4-1.7-.1 0-.1 0-.1 0s-.1 0-.1 0 0 .1 0 .1 0 0 0 0c.1 1.6.4 3.1 1 4.5.6 1.7 2.9 5.7 11.4 5.7 5 0 9.9-.6 14.8-1.7 0 0 0 0 0 0 .1 0 .1 0 .1 0 0 .1 0 .1 0 .1.1 0 .1 0 .1.1v5.6s0 .1-.1.1c0 0 0 0 0 .1-1.6 1.1-3.7 1.7-5.6 2.3-.8.3-1.6.5-2.4.7-7.5 1.7-15.4 1.3-22.7-1.2-6.8-2.4-13.8-8.2-15.5-15.2-.9-3.8-1.6-7.6-1.9-11.5-.6-5.8-.6-11.7-.8-17.5C3.9 24.5 4 20 4.9 16 6.7 7.9 14.1 2.2 22.3 1c1.4-.2 4.1-1 16.5-1h.1C51.4 0 56.7.8 58.1 1c8.4 1.2 15.5 7.5 16.6 15.6Z" fill="currentColor"/></svg> '
            f'<div style="color: #787588; margin-top: 16px;">Post by {username}@{domain}</div> '
            f'<div style="font-weight: 500;">View on Mastodon</div> '
            f'</a> '
            f'</blockquote>\n'
            f'            </div>\n'
            f'            <div class="card-footer">\n'
            f'                <a href="{post_url}" class="action-btn">View Live Post</a>\n'
            f'            </div>\n'
            f'        </div>\n'
            f'    </div>\n'
            f'    <script data-allowed-prefixes="{base_url_slash}" async src="{base_url_slash}embed.js"></script>\n'
            f'</body>\n'
            f'</html>'
        )
        return embed_html
    return post_url

def generate_chart_image(dates, views):
    import urllib.parse
    import urllib.request
    
    try:
        # Convert views list elements to integers
        views = [int(v) for v in views]
    except Exception:
        pass

    chart_config = {
        "type": "line",
        "data": {
            "labels": dates,
            "datasets": [{
                "label": "Page Views",
                "data": views,
                "borderColor": "rgb(54, 162, 235)",
                "backgroundColor": "rgba(54, 162, 235, 0.15)",
                "fill": True,
                "lineTension": 0.4,
                "pointBackgroundColor": "rgb(54, 162, 235)",
                "pointRadius": 4
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": "Last 7 Days Traffic",
                "fontSize": 16,
                "fontColor": "#333"
            },
            "scales": {
                "xAxes": [{
                    "scaleLabel": {
                        "display": True,
                        "labelString": "Date (MM-DD)"
                    }
                }],
                "yAxes": [{
                    "scaleLabel": {
                        "display": True,
                        "labelString": "Views"
                    },
                    "ticks": {
                        "beginAtZero": True
                    }
                }]
            }
        }
    }
    
    chart_config_str = json.dumps(chart_config)
    quickchart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(chart_config_str)}&w=800&h=400&bkg=white"
    
    try:
        print(f"Generating chart image via QuickChart: {quickchart_url}")
        req = urllib.request.Request(quickchart_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Error generating chart image: {e}")
        return None

def upload_media_to_mastodon(image_bytes, access_token, api_url, verify_ssl):
    import requests
    
    media_url = api_url.replace("/statuses", "/media")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    files = {
        "file": ("chart.png", image_bytes, "image/png")
    }
    
    try:
        print(f"Uploading media to {media_url}...")
        response = requests.post(media_url, headers=headers, files=files, timeout=20, verify=verify_ssl)
        response.raise_for_status()
        res_json = response.json()
        media_id = res_json.get("id")
        print(f"Successfully uploaded media! ID: {media_id}")
        return media_id
    except Exception as e:
        print(f"Failed to upload media to Mastodon: {e}")
        return None

def post_status(status_text, chart_image_bytes=None):
    for url, verify_ssl, extra_headers in URLS_TO_TRY:
        media_id = None
        if chart_image_bytes:
            media_id = upload_media_to_mastodon(chart_image_bytes, ACCESS_TOKEN, url, verify_ssl)
            
        data = {"status": status_text}
        if media_id:
            data["media_ids"] = [media_id]
            
        payload = json.dumps(data).encode("utf-8")
        
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

def render_loading_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mastodon API | Publishing Report...</title>
    <link rel="icon" type="image/png" href="https://avatars.githubusercontent.com/u/67197854">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #03030d;
            --card-bg: rgba(10, 10, 25, 0.45);
            --accent-primary: #00f0ff;
            --accent-secondary: #ff007f;
            --accent-tertiary: #b432ff;
            --text-main: #ffffff;
            --text-muted: #8b8ea8;
        }
        
        * {
            box-sizing: border-box;
        }
        
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            min-height: 100vh;
            background-color: var(--bg-color);
            font-family: 'Outfit', sans-serif;
            color: var(--text-main);
            position: relative;
        }

        .loader-container {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            min-height: 100vh;
            padding: 20px;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 10;
            transition: opacity 0.5s ease;
        }

        .aurora-container {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            overflow: hidden;
            z-index: 0;
            pointer-events: none;
        }

        .aurora-blob {
            position: absolute;
            border-radius: 50%;
            filter: blur(120px);
            opacity: 0.35;
            mix-blend-mode: screen;
            animation: floatBlob 25s infinite alternate ease-in-out;
        }

        .blob-1 {
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, var(--accent-primary) 0%, transparent 80%);
            top: -100px;
            left: -100px;
        }

        .blob-2 {
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, var(--accent-tertiary) 0%, transparent 80%);
            bottom: -150px;
            right: -100px;
            animation-duration: 35s;
        }

        .blob-3 {
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, var(--accent-secondary) 0%, transparent 80%);
            top: 40%;
            left: 60%;
            animation-duration: 18s;
        }

        @keyframes floatBlob {
            0% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(80px, 50px) scale(1.1); }
            100% { transform: translate(-40px, -60px) scale(0.9); }
        }

        .grid-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 240, 255, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 240, 255, 0.02) 1px, transparent 1px);
            background-size: 50px 50px;
            background-position: center;
            transform: perspective(500px) rotateX(60deg) translateY(-30%) translateZ(0);
            transform-origin: top center;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,1), rgba(0,0,0,0));
            -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1), rgba(0,0,0,0));
            z-index: 1;
            animation: gridScroll 20s linear infinite;
            pointer-events: none;
        }
        
        @keyframes gridScroll {
            0% { background-position: 0 0; }
            100% { background-position: 0 100%; }
        }
        
        .loader-card {
            position: relative;
            z-index: 10;
            background: var(--card-bg);
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-radius: 24px;
            padding: 50px 50px;
            text-align: center;
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            box-shadow: 
                0 20px 50px rgba(0, 0, 0, 0.6),
                inset 0 0 20px rgba(255, 255, 255, 0.05),
                0 0 40px rgba(0, 240, 255, 0.15);
            max-width: 480px;
            width: 90%;
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .loader-card::before {
            content: '';
            position: absolute;
            top: -2px; left: -2px; right: -2px; bottom: -2px;
            background: linear-gradient(45deg, var(--accent-primary), transparent, var(--accent-tertiary), transparent, var(--accent-secondary));
            background-size: 400% 400%;
            z-index: -1;
            border-radius: 26px;
            opacity: 0.2;
            animation: borderGlow 8s linear infinite;
        }

        @keyframes borderGlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .spinner-wrapper {
            position: relative;
            width: 140px;
            height: 140px;
            margin-bottom: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .brand-logo {
            width: 76px;
            height: 76px;
            border-radius: 50%;
            object-fit: cover;
            position: absolute;
            z-index: 5;
            border: 3px solid rgba(0, 240, 255, 0.25);
            animation: pulseLogo 2s infinite ease-in-out;
            box-shadow: 
                0 0 25px rgba(0, 240, 255, 0.35),
                inset 0 0 10px rgba(0, 240, 255, 0.2);
        }
        
        @keyframes pulseLogo {
            0%, 100% {
                transform: scale(1);
                filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.4));
            }
            50% {
                transform: scale(1.06);
                filter: drop-shadow(0 0 20px rgba(0, 240, 255, 0.6)) drop-shadow(0 0 10px rgba(255, 0, 127, 0.3));
            }
        }
        
        .spinner-outer {
            position: absolute;
            width: 120px;
            height: 120px;
            border: 4px solid transparent;
            border-top: 4px solid var(--accent-primary);
            border-bottom: 4px solid var(--accent-primary);
            border-radius: 50%;
            animation: spin 3s linear infinite;
            filter: drop-shadow(0 0 10px var(--accent-primary));
        }

        .spinner-inner {
            position: absolute;
            width: 102px;
            height: 102px;
            border: 3px solid transparent;
            border-left: 3px solid var(--accent-secondary);
            border-right: 3px solid var(--accent-secondary);
            border-radius: 50%;
            animation: spinReverse 2.0s linear infinite;
            filter: drop-shadow(0 0 8px var(--accent-secondary));
        }

        .spinner-dashed {
            position: absolute;
            width: 136px;
            height: 136px;
            border: 1px dashed rgba(180, 50, 255, 0.3);
            border-radius: 50%;
            animation: spin 10s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes spinReverse {
            0% { transform: rotate(360deg); }
            100% { transform: rotate(0deg); }
        }
        
        h2 {
            font-size: 26px;
            font-weight: 700;
            margin: 0 0 12px 0;
            background: linear-gradient(90deg, #ffffff, #a5a6ff, var(--accent-primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 0.5px;
        }
        
        p {
            font-size: 15px;
            color: var(--text-muted);
            margin: 0;
            font-weight: 400;
            line-height: 1.5;
        }

        .dots::after {
            content: '';
            animation: loadingDots 1.5s infinite steps(4);
        }
        
        @keyframes loadingDots {
            0% { content: ''; }
            25% { content: '.'; }
            50% { content: '..'; }
            75% { content: '...'; }
        }

        .status-console {
            margin-top: 25px;
            width: 100%;
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-radius: 10px;
            padding: 12px 16px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 12px;
            color: var(--accent-primary);
            text-align: left;
            min-height: 48px;
            position: relative;
            box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
        }
        
        .status-line::before {
            content: '> ';
            color: var(--accent-secondary);
            font-weight: bold;
        }

        #content {
            width: 100%;
            min-height: 100vh;
            display: none;
            opacity: 0;
            transition: opacity 0.8s ease;
            box-sizing: border-box;
            z-index: 2;
        }
        
        #content.visible {
            display: block;
            opacity: 1;
        }
        
        .error-card {
            background: rgba(255, 75, 75, 0.08);
            border: 1px solid rgba(255, 75, 75, 0.3);
            border-radius: 20px;
            padding: 35px;
            text-align: center;
            max-width: 420px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(255, 75, 75, 0.15);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            position: relative;
        }
        .error-card h3 {
            color: #ff4b4b;
            margin: 0 0 12px 0;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .retry-btn {
            margin-top: 20px;
            padding: 12px 28px;
            background: linear-gradient(90deg, #ff4b4b, #ff007f);
            border: none;
            color: white;
            border-radius: 10px;
            font-family: inherit;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
            transition: all 0.2s ease;
        }
        .retry-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 75, 75, 0.6);
        }
    </style>
</head>
<body>
    <div class="aurora-container">
        <div class="aurora-blob blob-1"></div>
        <div class="aurora-blob blob-2"></div>
        <div class="aurora-blob blob-3"></div>
    </div>
    <div class="grid-overlay"></div>

    <div class="loader-container">
        <div id="loader" class="loader-card">
            <div class="spinner-wrapper">
                <img class="brand-logo" src="https://avatars.githubusercontent.com/u/67197854" alt="Branding Logo">
                <div class="spinner-outer"></div>
                <div class="spinner-inner"></div>
                <div class="spinner-dashed"></div>
            </div>
            <h2>Generating Report<span class="dots"></span></h2>
            <p>Scraping traffic metrics & publishing dynamic chart to Mastodon</p>
            <div class="status-console">
                <div id="status-line" class="status-line">Establishing target VPS handshake...</div>
            </div>
        </div>
    </div>
    
    <div id="content"></div>
    
    <script>
        // Status console messaging loop
        const statusTexts = [
            "Establishing secure target VPS handshake...",
            "Accessing 24x7stream.shop analytics portal...",
            "Scraping product page views database...",
            "Extracting 7-day view counters...",
            "Compiling date-to-metric dataset...",
            "Requesting SVG-to-PNG line chart via QuickChart...",
            "Uploading high-resolution PNG to Mastodon storage...",
            "Acquiring Mastodon Media ID for attachment...",
            "Formulating status broadcast parameters...",
            "Transmitting status text payload to Mastodon network...",
            "Successfully posted status! Retrieving web-embed JSON...",
            "Compiling graphics and glassmorphic container layout...",
            "Deploying iframe blocks..."
        ];
        
        let statusIndex = 0;
        const consoleLine = document.getElementById('status-line');
        
        function updateStatus() {
            if (statusIndex < statusTexts.length) {
                consoleLine.textContent = statusTexts[statusIndex];
                statusIndex++;
                const nextTime = 600 + Math.random() * 800; // rotate updates smoothly
                setTimeout(updateStatus, nextTime);
            }
        }
        
        updateStatus();

        document.addEventListener('DOMContentLoaded', () => {
            fetch(window.location.pathname + '?run=true', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || 'Failed to post traffic') });
                }
                return response.text();
            })
            .then(html => {
                const loaderContainer = document.querySelector('.loader-container');
                const content = document.getElementById('content');
                
                loaderContainer.style.opacity = '0';
                
                setTimeout(() => {
                    loaderContainer.style.display = 'none';
                    content.innerHTML = html;
                    content.classList.add('visible');
                    
                    const scripts = content.querySelectorAll('script');
                    scripts.forEach(oldScript => {
                        const newScript = document.createElement('script');
                        Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                        newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                        oldScript.parentNode.replaceChild(newScript, oldScript);
                    });
                }, 500);
            })
            .catch(error => {
                const loaderContainer = document.querySelector('.loader-container');
                loaderContainer.style.display = 'none';
                
                const content = document.getElementById('content');
                content.innerHTML = `
                    <div class="error-card" style="margin: auto; z-index: 10;">
                        <h3>Broadcast Failed</h3>
                        <p style="color: #ecc9c9;">${error.message}</p>
                        <button class="retry-btn" onclick="window.location.reload()">Try Again</button>
                    </div>
                `;
                content.classList.add('visible');
            });
        });
    </script>
</body>
</html>"""

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
        # If the parameter run=true is passed, run the scrape and post synchronously
        if request.args.get("run") == "true":
            result = fetch_traffic_summary()
            if not result:
                return "Failed to fetch traffic summary from page", 500
                
            status_text, chart_image_bytes = result
            res = post_status(status_text, chart_image_bytes)
            if res["success"]:
                return generate_embed_html(res["url"]), 200
            else:
                return res["error"], 500
                
        # Otherwise, immediately return the loading HTML page template
        return render_loading_page(), 200
            
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
        result = fetch_traffic_summary()
        if result:
            status_text, chart_image_bytes = result
            post_status(status_text, chart_image_bytes)
        else:
            print("Failed to fetch traffic summary, aborting post.")

