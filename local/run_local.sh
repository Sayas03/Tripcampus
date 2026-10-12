#!/usr/bin/env bash
# Run the site + admin on your own computer (no nginx needed): http://127.0.0.1:8800/  and /admin/
# Login: admin@example.com / LocalPass123
set -e
cd "$(dirname "$0")/.."
T="${TMPDIR:-/tmp}/tripcampus-local"; mkdir -p "$T/site" "$T/data"
cp -r site/. "$T/site/"
[ -f "$T/data/site-data.json" ] || python3 -c "import json;d=json.load(open('data/site-data.json'));d['settings']['site']='http://127.0.0.1:8800';json.dump(d,open('$T/data/site-data.json','w'),ensure_ascii=False)"
cat > "$T/config.json" <<J
{"data_dir": "$T/data", "site_dir": "$T/site", "admin_email": "admin@example.com", "serve_static": true, "port": 8800}
J
export TC_CONFIG="$T/config.json"
python3 -c "import sys; sys.path.insert(0,'server'); import app; app.save_password('LocalPass123'); app.init_db(); print(app.publish('local')['pages'], 'pages built')"
python3 server/app.py
