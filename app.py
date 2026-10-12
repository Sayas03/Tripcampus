"""Trip Campus server for a single VPS (Amazon Lightsail, Ubuntu). Python 3 standard library only.

Nginx serves the website files and forwards /api/ to this app on 127.0.0.1:8000.

  POST   /api/enquiry              public quote form -> SQLite + email
  POST   /api/auth/login           admin sign in (sets a secure session cookie)
  POST   /api/auth/logout
  GET    /api/auth/me
  POST   /api/auth/password        change the admin password
  GET    /api/admin/data           site content
  PUT    /api/admin/data           save site content (draft)
  POST   /api/admin/publish        rebuild the website pages
  PUT    /api/admin/upload?name=   upload one processed photo file
  GET    /api/admin/leads          enquiries
  PATCH  /api/admin/leads/<id>     change status
  DELETE /api/admin/leads/<id>
"""
import datetime, hashlib, hmac, json, os, re, secrets, shutil, smtplib, sqlite3, sys, tempfile, threading, time, uuid
from email.message import EmailMessage
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_builder

CONFIG_FILE = os.environ.get('TC_CONFIG', '/etc/tripcampus/config.json')
DEFAULTS = {
    'data_dir': '/var/lib/tripcampus',          # site-data.json, history/, tripcampus.db
    'site_dir': '/var/www/tripcampus',          # what nginx serves
    'listen': '127.0.0.1', 'port': 8000,
    'api_path': '/api',
    'admin_email': '', 'password_hash': '',     # set with: sudo tc-admin set-password
    'smtp': {'host': '', 'port': 587, 'user': '', 'password': '', 'from': '', 'to': ''},
    'serve_static': False,                      # True only for local testing without nginx
}
LEAD_STATUSES = ('New', 'Contacted', 'Quoted', 'Booked', 'Lost')
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
IMG_NAME = re.compile(r'^(img|og)/[a-z0-9]+(?:-[a-z0-9]+)*\.(webp|jpg)$')
SESSION_DAYS = 7
LOCK = threading.Lock()


def load_config():
    cfg = json.loads(json.dumps(DEFAULTS))
    if os.path.exists(CONFIG_FILE):
        user = json.load(open(CONFIG_FILE))
        smtp = dict(cfg['smtp']); smtp.update(user.get('smtp') or {})
        cfg.update(user); cfg['smtp'] = smtp
    return cfg


CFG = load_config()
DATA_FILE = os.path.join(CFG['data_dir'], 'site-data.json')
DB_FILE = os.path.join(CFG['data_dir'], 'tripcampus.db')


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ---------------------------------------------------------------- password + sessions
def hash_password(pw, salt=None, iterations=600000):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', pw.encode(), bytes.fromhex(salt), iterations)
    return 'pbkdf2_sha256$%d$%s$%s' % (iterations, salt, dk.hex())


def check_password(pw, stored):
    try:
        _, it, salt, h = stored.split('$')
        return hmac.compare_digest(hash_password(pw, salt, int(it)).split('$')[3], h)
    except Exception:
        return False


def db():
    con = sqlite3.connect(DB_FILE, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    os.makedirs(CFG['data_dir'], exist_ok=True)
    with db() as con:
        con.execute('CREATE TABLE IF NOT EXISTS leads (id TEXT PRIMARY KEY, createdAt TEXT, status TEXT, name TEXT, phone TEXT, '
                    'package TEXT, size TEXT, month TEXT, note TEXT, page TEXT, source TEXT, updatedAt TEXT)')
        con.execute('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, email TEXT, expires REAL)')
        con.execute('CREATE TABLE IF NOT EXISTS attempts (key TEXT, at REAL)')


def rate_limited(key, limit, window):
    t = time.time()
    with db() as con:
        con.execute('DELETE FROM attempts WHERE at < ?', (t - 86400,))
        n = con.execute('SELECT COUNT(*) FROM attempts WHERE key = ? AND at > ?', (key, t - window)).fetchone()[0]
        if n >= limit:
            return True
        con.execute('INSERT INTO attempts VALUES (?, ?)', (key, t))
    return False


def new_session(email):
    tok = secrets.token_urlsafe(32)
    with db() as con:
        con.execute('DELETE FROM sessions WHERE expires < ?', (time.time(),))
        con.execute('INSERT INTO sessions VALUES (?, ?, ?)', (hashlib.sha256(tok.encode()).hexdigest(), email, time.time() + SESSION_DAYS * 86400))
    return tok


def session_email(tok):
    if not tok:
        return None
    with db() as con:
        r = con.execute('SELECT email, expires FROM sessions WHERE token_hash = ?', (hashlib.sha256(tok.encode()).hexdigest(),)).fetchone()
    if r and r['expires'] > time.time() and r['email'] == CFG['admin_email']:
        return r['email']
    return None


def end_session(tok):
    if tok:
        with db() as con:
            con.execute('DELETE FROM sessions WHERE token_hash = ?', (hashlib.sha256(tok.encode()).hexdigest(),))


def end_all_sessions():
    with db() as con:
        con.execute('DELETE FROM sessions')


# ---------------------------------------------------------------- content
class HttpError(Exception):
    def __init__(self, status, message):
        super().__init__(message); self.status, self.message = status, message


def load_data():
    return json.load(open(DATA_FILE, encoding='utf-8'))


def store_data(data):
    tmp = DATA_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


def clean_lines(v, limit=60):
    if isinstance(v, str):
        v = v.split('\n')
    return [str(x).strip()[:2000] for x in (v or []) if str(x).strip()][:limit]


def validate(data):
    errs = []
    if not isinstance(data, dict):
        raise HttpError(400, 'Content must be an object')
    for k in ('settings', 'packages', 'destinations', 'gallery', 'images'):
        if k not in data:
            errs.append('missing section: ' + k)
    if errs:
        raise HttpError(400, '; '.join(errs))
    seen = set()
    for p in data['packages']:
        p['name'] = str(p.get('name', '')).strip(); p['slug'] = str(p.get('slug', '')).strip().lower()
        if not p['name']: errs.append('a package has no name')
        if not SLUG.match(p['slug']): errs.append('package "%s" has an invalid web address' % p['name'])
        if p['slug'] in seen: errs.append('two packages use the web address "%s"' % p['slug'])
        seen.add(p['slug']); p['id'] = p.get('id') or p['slug']
        for f in ('days', 'facts', 'inc', 'tags'):
            p[f] = clean_lines(p.get(f))
        digits = re.sub(r'\D', '', str(p.get('price') or ''))
        p['price'] = int(digits) if digits else None
        if p.get('status') not in ('Published', 'Draft'): p['status'] = 'Draft'
        if p['status'] == 'Published' and not p['days']:
            errs.append('package "%s" needs at least one day in the itinerary before it can be published' % p['name'])
    dseen = set()
    for d in data['destinations']:
        d['id'] = str(d.get('id', '')).strip().lower()
        if not SLUG.match(d['id']): errs.append('destination "%s" has an invalid web address' % d.get('name', ''))
        if d['id'] in dseen: errs.append('two destinations use "%s"' % d['id'])
        dseen.add(d['id'])
        for f in ('todo', 'tips', 'packs'):
            d[f] = clean_lines(d.get(f))
        if d.get('status') not in ('Published', 'Draft'): d['status'] = 'Published'
    s = data['settings']
    if not re.sub(r'\D', '', str(s.get('whatsapp', ''))): errs.append('the WhatsApp number is empty')
    if not re.match(r'^https?://', str(s.get('site', ''))): errs.append('the website address must start with https://')
    if errs:
        raise HttpError(400, '; '.join(errs[:8]))
    return data


def publish(who='admin'):
    t0 = time.time()
    data = load_data()
    site = CFG['site_dir']
    out = tempfile.mkdtemp(prefix='tc_site_')
    try:
        res = site_builder.build(data, out, CFG['api_path'], site)
        for root, _, files in os.walk(out):
            for fn in files:
                src = os.path.join(root, fn)
                dst = os.path.join(site, os.path.relpath(src, out))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst + '.tmp'); os.replace(dst + '.tmp', dst)
        old = set((data.get('meta') or {}).get('pages') or [])
        gone = sorted(k for k in old - set(res['pages']) if k.endswith('.html'))
        for k in gone:
            p = os.path.join(site, k)
            if os.path.isfile(p): os.remove(p)
        meta = dict(data.get('meta') or {})
        meta.update(publishedAt=now(), publishedBy=who, dirty=False, pages=res['pages'])
        data['meta'] = meta
        store_data(data)
        return {'ok': True, 'pages': len(res['pages']), 'removed': gone, 'warnings': res['warnings'], 'seconds': round(time.time() - t0, 1), 'meta': meta}
    finally:
        shutil.rmtree(out, ignore_errors=True)


def send_email(subject, body):
    s = CFG['smtp']
    if not (s.get('host') and s.get('to')):
        return
    def run():
        try:
            m = EmailMessage(); m['Subject'] = subject; m['From'] = s.get('from') or s.get('user'); m['To'] = s['to']; m.set_content(body)
            with smtplib.SMTP(s['host'], int(s.get('port') or 587), timeout=20) as srv:
                srv.starttls()
                if s.get('user'): srv.login(s['user'], s['password'])
                srv.send_message(m)
        except Exception as ex:
            print('email error:', ex, flush=True)
    threading.Thread(target=run, daemon=True).start()


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = 'TripCampus'
    def log_message(self, fmt, *args):
        sys.stdout.write('%s %s\n' % (self.client_ip(), fmt % args)); sys.stdout.flush()

    def client_ip(self):
        return self.headers.get('X-Real-IP') or self.client_address[0]

    def https(self):
        return self.headers.get('X-Forwarded-Proto') == 'https'

    def cookie(self, name):
        for part in (self.headers.get('Cookie') or '').split(';'):
            k, _, v = part.strip().partition('=')
            if k == name: return v
        return None

    def reply(self, status, body=None, cookies=()):
        raw = json.dumps(body if body is not None else {}, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        for c in cookies: self.send_header('Set-Cookie', c)
        self.end_headers(); self.wfile.write(raw)

    def read_body(self, limit=2_000_000):
        n = int(self.headers.get('Content-Length') or 0)
        if n > limit: raise HttpError(413, 'Too large')
        return self.rfile.read(n) if n else b''

    def json_body(self):
        try:
            return json.loads(self.read_body() or b'{}')
        except ValueError:
            raise HttpError(400, 'Request body is not valid JSON')

    def set_cookie(self, tok, max_age):
        return 'tc_s=%s; Path=/api; HttpOnly; SameSite=Strict; Max-Age=%d%s' % (tok, max_age, '; Secure' if self.https() else '')

    def admin(self):
        email = session_email(self.cookie('tc_s'))
        if not email: raise HttpError(401, 'Please sign in')
        if self.command != 'GET' and self.headers.get('X-TC') != '1': raise HttpError(403, 'Missing request header')   # CSRF guard
        return email

    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PUT(self): self.route('PUT')
    def do_PATCH(self): self.route('PATCH')
    def do_DELETE(self): self.route('DELETE')

    def route(self, m):
        u = urlparse(self.path); path = u.path
        api = CFG['api_path']
        if not path.startswith(api + '/'):
            if CFG['serve_static'] and m == 'GET': return self.static(path)
            return self.reply(404, {'error': 'Not found'})
        p = path[len(api):]
        try:
            if m == 'POST' and p == '/enquiry': return self.enquiry()
            if m == 'POST' and p == '/auth/login': return self.login()
            if m == 'POST' and p == '/auth/logout':
                end_session(self.cookie('tc_s')); return self.reply(200, {'ok': True}, [self.set_cookie('', 0)])
            if m == 'GET' and p == '/auth/me': return self.reply(200, {'email': self.admin()})
            if m == 'POST' and p == '/auth/password': return self.change_password()
            if p.startswith('/admin/'):
                who = self.admin()
                if m == 'GET' and p == '/admin/data': return self.reply(200, load_data())
                if m == 'PUT' and p == '/admin/data': return self.put_data(who)
                if m == 'POST' and p == '/admin/publish':
                    with LOCK: return self.reply(200, publish(who))
                if m == 'PUT' and p == '/admin/upload': return self.upload(parse_qs(u.query).get('name', [''])[0])
                if m == 'GET' and p == '/admin/leads':
                    with db() as con: rows = [dict(r) for r in con.execute('SELECT * FROM leads ORDER BY createdAt DESC')]
                    return self.reply(200, {'leads': [{k: v for k, v in r.items() if v not in (None, '')} for r in rows]})
                mt = re.match(r'^/admin/leads/([a-f0-9]{6,32})$', p)
                if mt and m == 'PATCH':
                    st = self.json_body().get('status')
                    if st not in LEAD_STATUSES: raise HttpError(400, 'Status must be one of: ' + ', '.join(LEAD_STATUSES))
                    with db() as con: n = con.execute('UPDATE leads SET status = ?, updatedAt = ? WHERE id = ?', (st, now(), mt.group(1))).rowcount
                    if not n: raise HttpError(404, 'Enquiry not found')
                    return self.reply(200, {'ok': True})
                if mt and m == 'DELETE':
                    with db() as con: con.execute('DELETE FROM leads WHERE id = ?', (mt.group(1),))
                    return self.reply(200, {'ok': True})
            self.reply(404, {'error': 'Not found'})
        except HttpError as ex:
            self.reply(ex.status, {'error': ex.message})
        except Exception as ex:
            import traceback; traceback.print_exc()
            self.reply(500, {'error': 'Something went wrong on the server. Please try again.'})

    def login(self):
        b = self.json_body(); email = str(b.get('email', '')).strip().lower(); pw = str(b.get('password', ''))
        if rate_limited('login:' + self.client_ip(), 8, 900):
            raise HttpError(429, 'Too many sign-in attempts. Please wait 15 minutes.')
        if not CFG['password_hash']:
            raise HttpError(503, 'The admin password has not been set on the server yet (run: sudo tc-admin set-password).')
        if email != CFG['admin_email'] or not check_password(pw, CFG['password_hash']):
            time.sleep(1); raise HttpError(401, 'Incorrect email or password.')
        tok = new_session(email)
        self.reply(200, {'email': email}, [self.set_cookie(tok, SESSION_DAYS * 86400)])

    def change_password(self):
        self.admin(); b = self.json_body()
        if not check_password(str(b.get('current', '')), CFG['password_hash']): raise HttpError(400, 'Your current password is not correct.')
        new = str(b.get('new', ''))
        if len(new) < 10: raise HttpError(400, 'Use at least 10 characters for the new password.')
        save_password(new)
        end_all_sessions(); tok = new_session(CFG['admin_email'])
        self.reply(200, {'ok': True}, [self.set_cookie(tok, SESSION_DAYS * 86400)])

    def put_data(self, who):
        b = self.json_body(); data = validate(b.get('data'))
        with LOCK:
            current = load_data(); cur_v = int((current.get('meta') or {}).get('version') or 0)
            if b.get('baseVersion') is not None and int(b['baseVersion']) != cur_v:
                raise HttpError(409, 'These changes were saved from another tab or device since you opened the admin. Reload the page, then make your change again.')
            hist = os.path.join(CFG['data_dir'], 'history'); os.makedirs(hist, exist_ok=True)
            json.dump(current, open(os.path.join(hist, '%s-v%d.json' % (now().replace(':', ''), cur_v)), 'w', encoding='utf-8'), ensure_ascii=False)
            files = sorted(os.listdir(hist))
            for f in files[:-200]: os.remove(os.path.join(hist, f))          # keep the last 200 saves
            meta = dict(current.get('meta') or {}); meta.update(version=cur_v + 1, updatedAt=now(), updatedBy=who, dirty=True)
            data['meta'] = meta; store_data(data)
        self.reply(200, {'ok': True, 'meta': meta})

    def upload(self, name):
        if not IMG_NAME.match(name): raise HttpError(400, 'Invalid file name')
        raw = self.read_body(limit=8_000_000)
        ok = raw[:4] == b'RIFF' and raw[8:12] == b'WEBP' if name.endswith('.webp') else raw[:3] == b'\xff\xd8\xff'
        if not ok: raise HttpError(400, 'The file is not a valid image')
        dst = os.path.join(CFG['site_dir'], 'assets', name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst + '.tmp', 'wb') as fh: fh.write(raw)
        os.replace(dst + '.tmp', dst)
        self.reply(200, {'ok': True, 'name': name})

    def enquiry(self):
        b = self.json_body()
        if b.get('website'): return self.reply(200, {'ok': True})          # spam trap
        if rate_limited('enq:' + self.client_ip(), 10, 3600): raise HttpError(429, 'Too many enquiries from this connection. Please call or WhatsApp us.')
        name = str(b.get('name', '')).strip()[:120]
        phone = re.sub(r'[^\d+ ]', '', str(b.get('phone', '')))[:20].strip()
        if not name or len(re.sub(r'\D', '', phone)) < 10: raise HttpError(400, 'Name and a phone number with at least 10 digits are required')
        item = {'id': uuid.uuid4().hex[:12], 'createdAt': now(), 'status': 'New', 'name': name, 'phone': phone}
        for k, n in (('package', 120), ('size', 20), ('month', 40), ('note', 1500), ('page', 200), ('source', 200)):
            v = str(b.get(k, '') or '').strip()[:n]
            item[k] = v if v and v != 'Not sure yet' else None
        cols = list(item)
        with db() as con: con.execute('INSERT INTO leads (%s) VALUES (%s)' % (','.join(cols), ','.join('?' * len(cols))), [item[c] for c in cols])
        lines = ['New website enquiry', ''] + ['%s: %s' % (k.capitalize(), item[k]) for k in ('name', 'phone', 'package', 'size', 'month', 'note', 'page', 'source') if item.get(k)]
        d = re.sub(r'\D', '', phone); wa = 'https://wa.me/' + (d if len(d) > 10 else '91' + d[-10:])
        lines += ['', 'Reply on WhatsApp: ' + wa, 'All enquiries: admin > Enquiries']
        send_email('New enquiry: %s%s' % (name, (' – ' + item['package']) if item.get('package') else ''), '\n'.join(lines))
        self.reply(201, {'ok': True, 'id': item['id']})

    def static(self, path):     # local testing only; nginx does this on the server
        import mimetypes
        if path.endswith('/'): path += 'index.html'
        elif '.' not in path.rsplit('/', 1)[-1]:
            self.send_response(301); self.send_header('Location', path + '/'); self.end_headers(); return
        f = os.path.normpath(os.path.join(CFG['site_dir'], path.lstrip('/')))
        code = 200
        if not f.startswith(os.path.abspath(CFG['site_dir'])) or not os.path.isfile(f):
            f, code = os.path.join(CFG['site_dir'], '404.html'), 404
        raw = open(f, 'rb').read()
        self.send_response(code); self.send_header('Content-Type', mimetypes.guess_type(f)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)


def save_password(pw):
    global CFG
    cfg = json.load(open(CONFIG_FILE)) if os.path.exists(CONFIG_FILE) else {}
    cfg['password_hash'] = hash_password(pw)
    tmp = CONFIG_FILE + '.tmp'
    with open(tmp, 'w') as fh: json.dump(cfg, fh, indent=1)
    os.chmod(tmp, 0o600); os.replace(tmp, CONFIG_FILE)
    CFG['password_hash'] = cfg['password_hash']


def main():
    init_db()
    srv = ThreadingHTTPServer((CFG['listen'], int(CFG['port'])), Handler)
    print('Trip Campus app on %s:%s (admin: %s)' % (CFG['listen'], CFG['port'], CFG['admin_email'] or 'NOT SET'), flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    main()
