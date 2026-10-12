# Trip Campus on Amazon Lightsail (VPS) – setup guide

Your server: **Ubuntu, Mumbai (ap-south-1a), public IP 13.201.34.207**.

What runs on the server:

- **Nginx** serves the website (phone and desktop layouts in one site) and the admin at `/admin/`, with HTTPS from Let's Encrypt.
- **Trip Campus app** (Python, runs as a service) handles the admin login, saving content, photo uploads, publishing pages and the enquiry form.
- **Data**: content in `/var/lib/tripcampus/site-data.json` (with the last 200 saves kept), enquiries in a small SQLite database, settings in `/etc/tripcampus/config.json`.
- **One admin login**: the email you give the setup script. The password is stored hashed; 8 wrong tries locks sign-in for 15 minutes.

---

## Step 1 – Keep the IP address fixed (Static IP)

The IP of a Lightsail server changes if it is stopped and started, unless it has a static IP (free while attached).

1. Lightsail → your instance → **Networking** tab → **Attach static IP** (or *Create static IP* → choose this instance → *Create*).
2. Use the **new static IP** everywhere below instead of 13.201.34.207 if it is different.

## Step 2 – Open the HTTPS port

Lightsail → instance → **Networking** tab → **IPv4 Firewall** → **Add rule** → Application **HTTPS** (port 443) → Create.
Do the same under **IPv6 Firewall**. SSH (22) and HTTP (80) are open by default.

## Step 3 – Copy the files to the server

### Option A – from Windows PowerShell (recommended)

1. Lightsail home → **Account** (top right) → **Account** → **SSH keys** → under *Default keys*, download the key for **Mumbai (ap-south-1)**. It saves as `LightsailDefaultKey-ap-south-1.pem` in Downloads.
2. Open **PowerShell** and run (one time, so Windows lets SSH use the key):

```powershell
$key = "$HOME\Downloads\LightsailDefaultKey-ap-south-1.pem"
icacls $key /inheritance:r
icacls $key /grant:r "$($env:USERNAME):(R)"
```

3. Copy the zip to the server (type `yes` if asked to trust the server):

```powershell
scp -i $key "C:\Users\sayas\OneDrive\Desktop\Trip Campus\website\tripcampus-vps.zip" ubuntu@13.201.34.207:~/
```

### Option B – the Lightsail browser terminal

Lightsail → instance → **Connect using SSH**. If the terminal window offers an **Upload file** option, use it to upload `tripcampus-vps.zip`. If it does not, use Option A.

## Step 4 – Install

1. Lightsail → instance → **Connect using SSH** (opens a terminal in the browser).
2. Paste, using your own email (this becomes the one admin login):

```bash
sudo apt-get update -y && sudo apt-get install -y unzip
unzip -q -o tripcampus-vps.zip && cd tripcampus-vps
sudo bash deploy/setup.sh your-email@example.com
```

3. It asks you to choose the **admin password** (at least 10 characters) twice. Nothing appears while you type; that is normal.
4. When it finishes, open **http://13.201.34.207/** in your browser. The website should load.

Do not sign in to the admin until Step 5 is done: without HTTPS the password travels unencrypted.

## Step 5 – Connect the domain and turn on HTTPS

1. At your domain registrar (or Lightsail → **Domains & DNS**), create two **A records** pointing to the static IP:
   - `www` → 13.201.34.207
   - `@` (the bare domain) → 13.201.34.207
2. Wait until `www.tripcampustourism.com` opens the site (usually minutes, sometimes up to a few hours).
3. In the server terminal:

```bash
cd ~/tripcampus-vps
sudo bash deploy/setup.sh your-email@example.com www.tripcampustourism.com
```

This gets a free Let's Encrypt certificate for both `www` and the bare domain, redirects all traffic to HTTPS, renews the certificate automatically, and updates every canonical link and the sitemap to the domain.

4. Open **https://www.tripcampustourism.com/admin/** and sign in.
5. Google Search Console: add the domain and submit `https://www.tripcampustourism.com/sitemap.xml`.

## Step 6 – Enquiry emails (Gmail)

Enquiries are always saved in the admin. To also get them by email at tripcampusedpl@gmail.com:

1. Sign in to that Google account → **Manage your Google Account** → **Security** → turn on **2-Step Verification** → then search for **App passwords** → create one named "Trip Campus website" → copy the 16-character password.
2. On the server:

```bash
sudo nano /etc/tripcampus/config.json
```

Fill in the `smtp` section:

```json
"smtp": {"host": "smtp.gmail.com", "port": 587, "user": "tripcampusedpl@gmail.com",
         "password": "the 16-character app password", "from": "tripcampusedpl@gmail.com", "to": "tripcampusedpl@gmail.com"}
```

Save (Ctrl+O, Enter, Ctrl+X), then:

```bash
sudo systemctl restart tripcampus
sudo tc-admin test-email
```

## Step 7 – Backups

- **Daily backup** on the server (already installed): `/var/backups/tripcampus/`, last 14 days of content, enquiries, settings and uploaded photos.
- **Whole-server snapshots** (recommended): Lightsail → instance → **Snapshots** tab → turn on **Automatic snapshots**.

---

## Using the admin

- **Save** stores a change. The public website changes only when you press **Publish website** at the top of the admin.
- **Packages**: add, edit, day-by-day plan, "from ₹" price, cover photo, homepage slider, Google title and description, publish/unpublish, delete.
- **Destinations**, **Gallery** (photo upload in Chrome or Edge), **Enquiries** (status, WhatsApp/call links, CSV), **Settings** (contact details, GA4 and Meta Pixel IDs, homepage photo, password change).

## Server commands

| Task | Command |
|---|---|
| Reset / change the admin password | `sudo tc-admin set-password` |
| Change the admin email | `sudo tc-admin set-email new@example.com` |
| Rebuild the website pages | `sudo tc-admin publish` |
| Show settings | `sudo tc-admin status` |
| Test enquiry email | `sudo tc-admin test-email` |
| App status / logs | `sudo systemctl status tripcampus` · `sudo journalctl -u tripcampus -n 50` |
| Restart | `sudo systemctl restart tripcampus` · `sudo systemctl reload nginx` |

## Updating the website code later

Copy the new `tripcampus-vps.zip` to the server (Step 3), then:

```bash
unzip -q -o tripcampus-vps.zip && cd tripcampus-vps
sudo bash deploy/setup.sh your-email@example.com www.tripcampustourism.com
```

Content, photos, enquiries, the password and the HTTPS certificate are kept.

## Test on your own computer (optional)

`bash local/run_local.sh` → http://127.0.0.1:8800/ and /admin/ (login `admin@example.com` / `LocalPass123`).
