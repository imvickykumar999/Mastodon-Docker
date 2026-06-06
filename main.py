import json
import urllib.request
import urllib.error
import ssl
import os

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
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

STATUS_TEXT = "hello world"

# Endpoints to attempt.
# If running on the VPS itself, NAT loopback might block the public domain,
# so the script falls back to the local Docker HTTPS port.
URLS_TO_TRY = [
    ("https://mastodon.24x7stream.shop/api/v1/statuses", True, {}),
    ("https://localhost:8443/api/v1/statuses", False, {"Host": "mastodon.24x7stream.shop"}),
    ("http://localhost:8080/api/v1/statuses", True, {"Host": "mastodon.24x7stream.shop"}),
]

def post_status():
    payload = json.dumps({"status": STATUS_TEXT}).encode("utf-8")
    
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
    post_status()

