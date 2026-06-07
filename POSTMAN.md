# Mastodon Traffic Poster API - Postman / curl Guide

### Postman Collection (Recommended)
You can import the pre-configured Postman Collection file directly into Postman to have all endpoints loaded with a shared environment variable:
1. Open Postman, click **Import**, and select the **[`mastodon_api.postman_collection.json`](file:///home/priyanka/projects/mastodonvps/mastodon_api.postman_collection.json)** file.
2. In Postman, select the collection and go to the **Variables** tab to set your `vps_ip` (defaults to `localhost`). All requests will automatically use it!

---

### Manual Import via curl
Alternatively, you can copy any of the `curl` commands below and paste them directly into Postman's **Import** search bar (or click *Import* -> *Raw text* / *Paste raw text*) to quickly generate individual requests.

> [!NOTE]
> For the curl commands, replace `<your-vps-ip>` with the actual IP address or domain of your VPS.

---

### 1. Check API Status (`GET`)
Checks if the Flask API server is online and running.

```bash
curl -X GET http://<your-vps-ip>:5050/
```

**Expected Response:**
```json
{
  "message": "Mastodon Traffic Poster API is running.",
  "status": "online"
}
```

---

### 2. Fetch & Post Traffic Summary (`POST` / `GET`)
Triggers the script to scrape the page views summary from `https://24x7stream.shop/product/21/` and post the formatted summary directly to your Mastodon instance.

```bash
curl -X POST http://<your-vps-ip>:5050/post-traffic
```
*(Also supports simple `GET` requests if you want to trigger it directly in a browser address bar)*

**Expected Response:**
```json
{
  "success": true,
  "endpoint": "https://localhost:8443/api/v1/statuses",
  "post_url": "https://mastodon.24x7stream.shop/@24x7stream/116707112139179739",
  "posted_content": "📊 Page Views Summary: Starter Streaming Plan..."
}
```

---

### 3. Post Custom Status (`POST`)
Posts a custom status message directly to your Mastodon instance.

```bash
curl -X POST http://<your-vps-ip>:5050/post \
  -H "Content-Type: application/json" \
  -d '{"status": "Hello from my API server via Postman!"}'
```

**Expected Response:**
```json
{
  "success": true,
  "endpoint": "https://localhost:8443/api/v1/statuses",
  "post_url": "https://mastodon.24x7stream.shop/@24x7stream/116707112139179739"
}
```
