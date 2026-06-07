# Mastodon Traffic Poster API - Postman / curl / OpenClaw Guide

To avoid firewall blocks on port `5050` and NAT loopback issues from inside Docker containers (like OpenClaw), the API is reverse-proxied through Nginx on the standard public HTTPS port (`443`).

---

## 🚀 1. For External Clients (Postman from your laptop, etc.)

Use the public reverse proxy URL: **`https://mastodon.24x7stream.shop/mastodon-api/`**

### Check API Status (`GET`)
```bash
curl -X GET https://mastodon.24x7stream.shop/mastodon-api/
```

### Fetch & Post Traffic Summary (`POST`)
```bash
curl -X POST https://mastodon.24x7stream.shop/mastodon-api/post-traffic
```

### Post Custom Status (`POST`)
```bash
curl -X POST https://mastodon.24x7stream.shop/mastodon-api/post \
  -H "Content-Type: application/json" \
  -d '{"status": "Hello from my API server via public proxy!"}'
```

---

## 🤖 2. For OpenClaw / Docker Containers running on the VPS

Because the OpenClaw container runs on a Docker bridge network (`openclawvps_default`), it cannot resolve the host's public IP loopback or localhost directly. 

Instead, use the host's bridge gateway IP: **`http://172.22.0.1:5050/`**

### OpenClaw curl command:
Run this from the Telegram interface or inside the OpenClaw container:
```bash
curl --location --request POST 'http://172.22.0.1:5050/post-traffic'
```

---

## 📥 3. Postman Collection

You can import the pre-configured Postman Collection file directly into Postman:
1. Open Postman, click **Import**, and select the **[`mastodon_api.postman_collection.json`](file:///home/priyanka/projects/mastodonvps/mastodon_api.postman_collection.json)** file.
2. Under the Collection **Variables** tab:
   - For public proxy access, set `vps_url` to `https://mastodon.24x7stream.shop/mastodon-api`.
