#!/usr/bin/env bash
# Installs or updates the Trip Campus website on an Ubuntu server (Amazon Lightsail).
#   First install (no domain yet):  sudo bash deploy/setup.sh you@example.com
#   With the domain (adds HTTPS):   sudo bash deploy/setup.sh you@example.com www.tripcampustourism.com
# Running it again updates the code and pages; saved content, photos, enquiries and the password are kept.
set -euo pipefail
ADMIN_EMAIL="$(echo "${1:-}" | tr 'A-Z' 'a-z')"
DOMAIN="${2:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ "$(id -u)" = 0 ] || { echo "Please run with sudo:  sudo bash deploy/setup.sh $*"; exit 1; }
[ -n "$ADMIN_EMAIL" ] || { echo "Usage: sudo bash deploy/setup.sh admin-email@example.com [www.yourdomain.com]"; exit 1; }

echo "==> 1/7 Installing server software"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y -q
apt-get install -y -q nginx python3 sqlite3 certbot python3-certbot-nginx unzip >/dev/null

echo "==> 2/7 Creating folders and the service user"
id tripcampus >/dev/null 2>&1 || useradd --system --home /var/lib/tripcampus --shell /usr/sbin/nologin tripcampus
mkdir -p /opt/tripcampus /var/www/tripcampus /var/lib/tripcampus /etc/tripcampus /var/backups/tripcampus

echo "==> 3/7 Copying the app, website files and admin"
cp -r "$HERE"/server/. /opt/tripcampus/
cp -r "$HERE"/site/. /var/www/tripcampus/
printf '#!/bin/sh\nexec /usr/bin/python3 /opt/tripcampus/tc_admin.py "$@"\n' > /usr/local/bin/tc-admin && chmod 755 /usr/local/bin/tc-admin
install -m 755 "$HERE/deploy/backup.sh" /etc/cron.daily/tripcampus-backup

PUBLIC_IP="$(curl -s --max-time 5 http://checkip.amazonaws.com || hostname -I | awk '{print $1}')"
SITE_URL="http://$PUBLIC_IP"; [ -n "$DOMAIN" ] && SITE_URL="https://$DOMAIN"

if [ ! -f /var/lib/tripcampus/site-data.json ]; then
  python3 - "$HERE/data/site-data.json" "$SITE_URL" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8')); d['settings']['site'] = sys.argv[2]
json.dump(d, open('/var/lib/tripcampus/site-data.json', 'w', encoding='utf-8'), ensure_ascii=False)
PY
  echo "     Starting content loaded."
else
  echo "     Keeping the saved content."
fi

python3 - "$ADMIN_EMAIL" <<'PY'
import json, os, sys
p = '/etc/tripcampus/config.json'
c = json.load(open(p)) if os.path.exists(p) else {}
if c.get('admin_email') and c['admin_email'] != sys.argv[1]:
    print('     Admin email changed from %s to %s' % (c['admin_email'], sys.argv[1]))
c['admin_email'] = sys.argv[1]
c.setdefault('smtp', {'host': '', 'port': 587, 'user': '', 'password': '', 'from': '', 'to': 'tripcampusedpl@gmail.com'})
json.dump(c, open(p, 'w'), indent=1)
PY
chown -R tripcampus:tripcampus /var/www/tripcampus /var/lib/tripcampus /etc/tripcampus
chmod 700 /etc/tripcampus && chmod 600 /etc/tripcampus/config.json

echo "==> 4/7 Setting up nginx and the app service"
SERVER_NAME="_"; [ -n "$DOMAIN" ] && SERVER_NAME="$DOMAIN"
APEX="${DOMAIN#www.}"; CERT_NAMES="-d $DOMAIN"
if [ -n "$DOMAIN" ] && [ "$APEX" != "$DOMAIN" ]; then SERVER_NAME="$DOMAIN $APEX"; CERT_NAMES="-d $DOMAIN -d $APEX"; fi
sed "s/__SERVER_NAME__/$SERVER_NAME/" "$HERE/deploy/nginx.conf" > /etc/nginx/sites-available/tripcampus.new
if [ -f /etc/nginx/sites-available/tripcampus ] && grep -q "ssl_certificate" /etc/nginx/sites-available/tripcampus && [ -n "$DOMAIN" ]; then
  rm /etc/nginx/sites-available/tripcampus.new; echo "     Keeping the existing HTTPS nginx config."
else
  mv /etc/nginx/sites-available/tripcampus.new /etc/nginx/sites-available/tripcampus
fi
[ -s /proc/net/if_inet6 ] || sed -i '/listen \[::\]/d' /etc/nginx/sites-available/tripcampus   # server without IPv6
ln -sf /etc/nginx/sites-available/tripcampus /etc/nginx/sites-enabled/tripcampus
rm -f /etc/nginx/sites-enabled/default
cp "$HERE/deploy/tripcampus.service" /etc/systemd/system/tripcampus.service
systemctl daemon-reload
systemctl enable --now tripcampus >/dev/null 2>&1
systemctl restart tripcampus
nginx -t -q && systemctl reload nginx

echo "==> 5/7 Admin password"
if python3 -c "import json,sys; sys.exit(0 if json.load(open('/etc/tripcampus/config.json')).get('password_hash') else 1)"; then
  echo "     Password already set (change it with: sudo tc-admin set-password)"
else
  tc-admin set-password
fi

echo "==> 6/7 Publishing the website pages"
tc-admin publish
chown -R tripcampus:tripcampus /var/www/tripcampus /var/lib/tripcampus

if [ -n "$DOMAIN" ]; then
  echo "==> 7/7 HTTPS certificate for $DOMAIN (Let's Encrypt)"
  if ! grep -q "ssl_certificate" /etc/nginx/sites-available/tripcampus; then
    certbot --nginx $CERT_NAMES --redirect --agree-tos -m "$ADMIN_EMAIL" --non-interactive
  else
    echo "     Certificate already installed (renews automatically)."
  fi
  python3 - "$DOMAIN" <<'PY'
import json, sys
p = '/var/lib/tripcampus/site-data.json'; d = json.load(open(p, encoding='utf-8'))
if d['settings'].get('site') != 'https://' + sys.argv[1]:
    d['settings']['site'] = 'https://' + sys.argv[1]; json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
PY
  chown tripcampus:tripcampus /var/lib/tripcampus/site-data.json
  tc-admin publish >/dev/null && chown -R tripcampus:tripcampus /var/www/tripcampus /var/lib/tripcampus
else
  echo "==> 7/7 HTTPS: skipped (no domain yet)"
fi

echo
echo "  Website: $SITE_URL/"
echo "  Admin:   $SITE_URL/admin/   (login: $ADMIN_EMAIL)"
[ -z "$DOMAIN" ] && echo "  Sign in to the admin only after HTTPS is set up (run this script again with your domain)."
echo "  Enquiry emails: edit /etc/tripcampus/config.json (smtp), then: sudo systemctl restart tripcampus && sudo tc-admin test-email"
