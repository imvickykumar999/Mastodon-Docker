import json
import urllib.request
import urllib.error
import ssl
import os
import re

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
                return
        except Exception as e:
            print(f"Failed: {e}\n")
            continue
            
    print("Error: Could not connect to any of the Mastodon endpoints.")

if __name__ == "__main__":
    status_text = fetch_traffic_summary()
    if status_text:
        post_status(status_text)
    else:
        print("Failed to fetch traffic summary, aborting post.")

