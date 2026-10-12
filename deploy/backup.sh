#!/bin/sh
# Daily backup of content, enquiries and settings (installed in /etc/cron.daily). Keeps 14 days.
set -e
mkdir -p /var/backups/tripcampus
sqlite3 /var/lib/tripcampus/tripcampus.db ".backup /var/lib/tripcampus/tripcampus-backup.db" 2>/dev/null || true
tar czf /var/backups/tripcampus/tripcampus-$(date +%F).tgz /var/lib/tripcampus /etc/tripcampus /var/www/tripcampus/assets/img /var/www/tripcampus/assets/og 2>/dev/null
find /var/backups/tripcampus -name 'tripcampus-*.tgz' -mtime +14 -delete
