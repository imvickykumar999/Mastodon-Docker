# Mastodon Docker

<img width="1535" height="982" alt="image" src="https://github.com/user-attachments/assets/b63c1d4d-b746-4917-a223-923d2544d6ba" />

    I am hosting my own platform on VPS after 2 account got suspended.
    Do mastodon have rights to suspend mastodon of my own docker image hosted on my vps?
    
**No, the Mastodon organization does not have the right or the technical ability to suspend or shut down the Mastodon software running on your own Virtual Private Server (VPS).**

### Why You Are in Control

* **Open-Source Independence:** Mastodon is published as free and open-source software under the Affero General Public License (AGPLv3), which allows anyone to use or modify the software.
* **Decentralized Infrastructure:** Mastodon operates as a federated network of independently managed servers rather than a centrally controlled platform. Because you are hosting the server yourself, it is run entirely by you, and you have complete ownership of the instance.
* **Absolute Administration:** As the server administrator, you establish your own moderation policies and content guidelines.

### Federation Moderation

While no central authority can take your server offline, the decentralized network (the Fediverse) operates on mutual consent. Other server administrators do have the ability to sever ties with your instance at the server level.

If another administrator chooses to "suspend" your instance from theirs:

* No content from your server will be stored locally on their server, except for usernames.
* All existing follow relationships between accounts on your server and their server will be permanently removed and will not be restored even if the suspension is lifted.
* Your server will remain fully online and operational, and you will still be able to communicate with any other independent Mastodon servers that have not blocked you.

<img width="1535" height="982" alt="image" src="https://github.com/user-attachments/assets/cc05d47d-59eb-4ecd-b15d-f4d92e39e07d" />
<img width="1535" height="983" alt="image" src="https://github.com/user-attachments/assets/71d0d334-c7ca-4ca9-a54a-2140a2bb95a5" />
<img width="1536" height="1033" alt="image" src="https://github.com/user-attachments/assets/eb41222f-8e02-41b0-8089-9186556833d5" />

## Deployment

This repository includes a standard `docker-compose.yml` configuration using the `lscr.io/linuxserver/mastodon:latest` Docker image.

### Quick Start

1. **Configure Environment:**
   Edit the `docker-compose.yml` file to specify your:
   - `LOCAL_DOMAIN`
   - `DB_PASS` (must match `POSTGRES_PASSWORD`)
   - SMTP details for email/notifications.

2. **Generate Secrets:**
   Run the following commands using the Mastodon container to generate your secrets, then update the corresponding environment variables in your `docker-compose.yml`:
   ```bash
   # Generate SECRET_KEY_BASE & OTP_SECRET (run twice to get two different keys)
   docker run --rm -it --entrypoint /bin/bash lscr.io/linuxserver/mastodon:latest generate-secret

   # Generate VAPID_PRIVATE_KEY & VAPID_PUBLIC_KEY
   docker run --rm -it --entrypoint /bin/bash lscr.io/linuxserver/mastodon:latest generate-vapid
   ```

3. **Start the Stack:**
   ```bash
   docker compose up -d
   ```

