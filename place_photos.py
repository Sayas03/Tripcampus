"""Destination cover photos for the package pages, from Wikimedia Commons (free licences only).

Run on the server, from the tripcampus-vps folder:

  sudo python3 deploy/place_photos.py find            find up to 12 high-resolution photo options per package
                                                      -> review them at https://<your site>/photo-picks/
  sudo python3 deploy/place_photos.py find --min 4000           only photos at least 4000 px wide
  sudo python3 deploy/place_photos.py search 5 "Om Beach Gokarna" --min 5000
                                                      new search for package 5 only, largest photos first
  sudo python3 deploy/place_photos.py apply auto      use option 1 for every package
  sudo python3 deploy/place_photos.py apply 1=3 4=2   package 1 -> option 3, package 4 -> option 2 (others unchanged)
  sudo python3 deploy/place_photos.py undo            put the previous cover photos back

Only photos under CC0, public domain, CC BY or CC BY-SA are offered. Their authors and licences are listed
automatically on /photo-credits.html (linked in the footer), which those licences require.
Covers are saved as WebP at 480, 960, 1600 and 2400 px wide (plus a JPG fallback and a 1200x630 share image).
"""
import hashlib, html, io, json, os, re, shutil, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.environ.get('TC_APP_DIR', '/opt/tripcampus'))
import app  # noqa: E402  (the installed Trip Campus app: paths, data, publish)

UA = 'TripCampusWebsite/1.0 (https://www.tripcampustourism.com; tripcampusedpl@gmail.com)'
API = 'https://commons.wikimedia.org/w/api.php'
PICKS = os.path.join(app.CFG['data_dir'], 'photo-picks.json')
SITE = app.CFG['site_dir']
WIDTHS = [480, 960, 1600, 2400]

# What to search for each package, best first (the main scenery of the trip).
TERMS = {
    'dandeli-goa-train-tour': ['Kali River Dandeli', 'Dandeli', 'Basilica of Bom Jesus Goa', 'Aguada Fort Goa'],
    'hampi-dandeli-goa-tour': ['Vittala Temple Hampi', 'Virupaksha Temple Hampi', 'Hampi ruins', 'Hampi'],
    'lonavala-matheran-mumbai-tour': ['Matheran', 'Lonavala', 'Gateway of India Mumbai', 'Marine Drive Mumbai'],
    'chikmagalur-dandeli-goa-tour': ['Mullayanagiri', 'Chikmagalur', 'Chikkamagaluru coffee', 'Baba Budangiri'],
    'chikmagalur-dandeli-gokarna-tour': ['Om Beach Gokarna', 'Chikmagalur', 'Kudle Beach', 'Mullayanagiri'],
    'dandeli-gokarna-train-tour': ['Gokarna beach', 'Om Beach Gokarna', 'Kali River Dandeli', 'Gokarna'],
    'munnar-vattavada-tour': ['Munnar tea plantation', 'Munnar', 'Vattavada', 'Top Station Munnar'],
    'wayanad-900-woods-tour': ['Chembra Peak', 'Wayanad', 'Banasura Sagar', 'Wayanad forest'],
    'ramakkalmedu-kodaikanal-tour': ['Kodaikanal lake', 'Kodaikanal', 'Ramakkalmedu', 'Kodaikanal hills'],
}
BAD = re.compile(r'map|logo|flag|diagram|chart|stamp|coin|poster|plan|sketch|drawing|painting|selfie|portrait|svg|signboard|ticket', re.I)
OK_LIC = re.compile(r'^(cc0|public domain|pd|cc[ -]by(-sa)?[ -]\d)', re.I)


def get(params):
    q = dict(params, format='json', formatversion='2')
    req = urllib.request.Request(API + '?' + urllib.parse.urlencode(q), headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def plain(v):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', v or ''))).strip()


def search(term, minw=2400, pages=2):
    found = []
    for k in range(pages):   # 50 results per page; the biggest photos are kept after filtering
        d = get({'action': 'query', 'generator': 'search', 'gsrsearch': term + ' filetype:bitmap', 'gsrnamespace': 6, 'gsrlimit': 50,
                 'gsroffset': 50 * k, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': 640,
                 'iiextmetadatafilter': 'LicenseShortName|Artist|ObjectName'})
        found += (d.get('query') or {}).get('pages', [])
        if 'continue' not in d: break
        time.sleep(0.3)
    out = []
    for pg in found:
        ii = (pg.get('imageinfo') or [{}])[0]
        md = ii.get('extmetadata') or {}
        lic = plain((md.get('LicenseShortName') or {}).get('value'))
        w, h = ii.get('width', 0), ii.get('height', 0)
        if ii.get('mime') != 'image/jpeg' or w < minw or not h or not (1.3 <= w / h <= 2.4): continue
        if not OK_LIC.match(lic) or BAD.search(pg['title']): continue
        out.append({'title': pg['title'], 'w': w, 'h': h, 'license': lic, 'thumb': ii.get('thumburl'),
                    'page': ii.get('descriptionurl'), 'author': plain((md.get('Artist') or {}).get('value'))[:120] or 'Unknown',
                    'name': plain((md.get('ObjectName') or {}).get('value')) or re.sub(r'^File:|\.\w+$', '', pg['title']),
                    'mp': round(w * h / 1e6, 1), 'q': term})
    out.sort(key=lambda c: -c['w'] * c['h'])   # highest resolution first
    return out


def packages():
    return [p for p in app.load_data()['packages'] if p.get('status', 'Published') == 'Published']


def find(minw=2400, only=None, term=None):
    old = {pk['n']: pk for pk in json.load(open(PICKS))} if os.path.exists(PICKS) else {}
    picks = []
    for i, p in enumerate(packages(), 1):
        if only and i != only:
            picks.append(old.get(i) or {'n': i, 'slug': p['slug'], 'name': p['name'], 'options': []}); continue
        seen, opts = set(), []
        for t in [term] if term else (TERMS.get(p['slug']) or [x.strip() for x in p.get('route', p['name']).split('·')]):
            try:
                for c in search(t, minw):
                    if c['title'] not in seen:
                        seen.add(c['title']); opts.append(c)
            except Exception as ex:
                print('   search failed for', t, '-', ex)
            time.sleep(0.5)
        opts.sort(key=lambda c: -c['w'] * c['h'])
        picks.append({'n': i, 'slug': p['slug'], 'name': p['name'], 'options': opts[:12]})
        best = ('largest %d×%d' % (opts[0]['w'], opts[0]['h'])) if opts else 'try a different search word'
        print('%d. %-38s %2d options  (%s)' % (i, p['name'], len(opts[:12]), best))
    json.dump(picks, open(PICKS, 'w'), indent=1)
    page(picks)
    print('\nReview: https://www.tripcampustourism.com/photo-picks/  (options are numbered largest first)')


def page(picks):
    rows = ''
    for pk in picks:
        cards = ''.join(f'<figure data-w="{c["w"]}" data-px="{c["w"] * c["h"]}" data-i="{j}"><a href="{html.escape(c["page"])}" target="_blank"><img src="{html.escape(c["thumb"])}" loading="lazy" alt=""></a>'
                        f'<figcaption><b>Option {j}</b> · {c["w"]}×{c["h"]} · <b>{c.get("mp", round(c["w"] * c["h"] / 1e6, 1))} MP</b><br>{html.escape(c["name"][:70])}<br><small>{html.escape(c["license"])} · {html.escape(c["author"][:50])} · search: {html.escape(c.get("q", ""))}</small></figcaption></figure>'
                        for j, c in enumerate(pk['options'], 1)) or '<p>No suitable photos found. Try: <code>search %d "other words" --min 2000</code></p>' % pk['n']
        rows += f'<h2>Package {pk["n"]}: {html.escape(pk["name"])}</h2><div class="g">{cards}</div>'
    os.makedirs(os.path.join(SITE, 'photo-picks'), exist_ok=True)
    open(os.path.join(SITE, 'photo-picks', 'index.html'), 'w').write(
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
        '<title>Cover photo options</title><style>body{font:15px system-ui;margin:16px;background:#111;color:#eee}h2{margin:28px 0 10px}'
        '.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}figure{margin:0;background:#222;border-radius:8px;overflow:hidden}'
        'img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}figcaption{padding:8px}small{color:#aaa}a{color:#8cf}'
        '.bar{position:sticky;top:0;background:#111;padding:10px 0;display:flex;gap:12px;flex-wrap:wrap;align-items:center;z-index:1}select{font:inherit;padding:6px}</style>'
        '<h1>Cover photo options</h1><p>Pick an option number for each package, then run on the server, for example:<br>'
        '<code>sudo python3 deploy/place_photos.py apply 1=2 2=1 3=4</code> &nbsp;or&nbsp; <code>... apply auto</code> (option 1 = largest photo)</p>'
        '<div class="bar"><label>Sort <select id="srt"><option value="px">Highest resolution first</option><option value="w">Widest first</option><option value="i">Option number</option></select></label>'
        '<label>Show <select id="min"><option value="0">All sizes</option><option value="3000">3000 px wide +</option><option value="4000">4000 px wide +</option><option value="5000">5000 px wide +</option><option value="6000">6000 px wide +</option></select></label></div>'
        + rows +
        '<script>function u(){var s=document.getElementById("srt").value,m=+document.getElementById("min").value;'
        'document.querySelectorAll(".g").forEach(function(g){var f=[].slice.call(g.children).filter(function(x){return x.tagName=="FIGURE"});'
        'f.sort(function(a,b){return s=="i"?a.dataset.i-b.dataset.i:b.dataset[s]-a.dataset[s]});'
        'f.forEach(function(x){x.hidden=+x.dataset.w<m;g.appendChild(x)})})}'
        'document.getElementById("srt").onchange=u;document.getElementById("min").onchange=u;u()</script>')


def download(title):
    d = get({'action': 'query', 'titles': title, 'prop': 'imageinfo', 'iiprop': 'url', 'iiurlwidth': 2560})
    ii = d['query']['pages'][0]['imageinfo'][0]
    url = ii.get('thumburl') or ii['url']
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save_images(raw, slug):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
    if im.width > 2560: im = im.resize((2560, round(im.height * 2560 / im.width)), Image.LANCZOS)
    W, H = im.size
    ws = [w for w in WIDTHS if w <= W] or [W]
    d = os.path.join(SITE, 'assets', 'img')
    for w in ws:
        im.resize((w, round(H * w / W)), Image.LANCZOS).save(os.path.join(d, f'{slug}-{w}.webp'), 'WEBP', quality=82, method=6)
    im.resize((960, round(H * 960 / W)), Image.LANCZOS).save(os.path.join(d, f'{slug}-960.jpg'), 'JPEG', quality=82, optimize=True, progressive=True)
    og = ImageOps.fit(im, (1200, 630), Image.LANCZOS)
    os.makedirs(os.path.join(SITE, 'assets', 'og'), exist_ok=True)
    og.save(os.path.join(SITE, 'assets', 'og', f'{slug}.jpg'), 'JPEG', quality=85, optimize=True)
    return {'slug': slug, 'w': W, 'h': H, 'ws': ws, 'fb': 960}


def backup(data, tag):
    hd = os.path.join(app.CFG['data_dir'], 'history'); os.makedirs(hd, exist_ok=True)
    json.dump(data, open(os.path.join(hd, time.strftime('%Y%m%d-%H%M%S') + '-' + tag + '.json'), 'w'), ensure_ascii=False)


def finish(data):
    app.store_data(data)
    os.system('chown -R tripcampus:tripcampus %s %s/assets/img %s/assets/og 2>/dev/null' % (app.CFG['data_dir'], SITE, SITE))
    r = app.publish('photos')
    print('Published %d pages.' % r['pages'])


def apply(args):
    try:
        import PIL  # noqa
    except ImportError:
        sys.exit('Install the image library first:  sudo apt-get install -y python3-pil')
    if not os.path.exists(PICKS): sys.exit('Run "find" first.')
    picks = {pk['n']: pk for pk in json.load(open(PICKS))}
    choice = {n: 1 for n in picks} if args == ['auto'] else {int(a.split('=')[0]): int(a.split('=')[1]) for a in args}
    data = app.load_data(); backup(data, 'before-photos')
    bys = {p['slug']: p for p in data['packages']}
    for n, j in sorted(choice.items()):
        pk = picks.get(n)
        if not pk or not (1 <= j <= len(pk['options'])):
            print('Skipping package %s option %s (not available)' % (n, j)); continue
        c = pk['options'][j - 1]; p = bys.get(pk['slug'])
        if not p: continue
        print('%d. %s <- %s' % (n, pk['name'], c['title']))
        key = 'place-' + pk['slug'] + '-' + hashlib.md5(c['title'].encode()).hexdigest()[:6]   # new name per photo, so browsers never show a cached old one
        m = save_images(download(c['title']), key)
        m['alt'] = '%s – %s' % (c['name'][:90], p.get('place') or p['name'])
        m['credit'] = {'author': c['author'], 'license': c['license'], 'url': c['page']}
        data['images'][key] = m
        if 'heroPrev' not in p: p['heroPrev'] = p.get('hero')   # keep the original for undo
        p['hero'] = key
        time.sleep(0.5)
    finish(data)


def undo():
    data = app.load_data(); backup(data, 'before-undo')
    for p in data['packages']:
        if 'heroPrev' in p:
            p['hero'] = p.pop('heroPrev'); print('Restored', p['name'])
    finish(data)


if __name__ == '__main__':
    if os.geteuid() != 0: sys.exit('Run with sudo.')
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    argv = sys.argv[2:]
    minw = 2400
    if '--min' in argv:
        k = argv.index('--min'); minw = int(argv[k + 1]); del argv[k:k + 2]
    if cmd == 'find': find(minw)
    elif cmd == 'search' and len(argv) >= 2: find(minw, only=int(argv[0]), term=' '.join(argv[1:]))
    elif cmd == 'apply' and argv: apply(argv)
    elif cmd == 'undo': undo()
    else: print(__doc__)
