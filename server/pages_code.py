# Generated pages. Executed by site_builder.build() with DATA and OUT in globals.
import datetime
S_ = DATA['settings']
SITE = S_['site'].rstrip('/'); BRAND = S_.get('brand', 'Trip Campus'); LEGAL = S_.get('legal', 'Trip Campus Travel & Tourism')
WA = re.sub(r'\D', '', S_['whatsapp']); EMAIL = S_['email']; INSTAGRAM = S_.get('instagram', '')
PHONES = [(x['tel'], x['label']) for x in S_['phones']] or [('+' + WA, '+' + WA)]
ADDRESS = S_['address']; MAPS = S_.get('maps', '')
LASTMOD = datetime.date.today().isoformat()
C_ = DATA['common']; EXCLUDED, CARRY, NOTES, BREAKFAST, MEALS = C_['excluded'], C_['carry'], C_['notes'], C_['breakfast'], C_['meals']
HOME_FAQ = [tuple(x) for x in DATA['home']['faq']]; COLLEGES = DATA['home']['colleges']
IV = DATA['iv']; GUIDES = DATA['guides']; CHECKLIST = [tuple(x) for x in DATA['checklist']]; PUBLISHED = DATA.get('published', LASTMOD)
SERV = DATA['services']; IM = DATA['images']; OGCARDS = set(DATA.get('ogCards', []))
COMMON = list(C_.get('included', [])) or ["Rooms on 4-bed share basis", "Toll, parking and taxes", "Three unlimited meals a day (chicken is limited)", "All entry tickets", "Drinking water"]
WARN = []
def _img(k): return k if (k and k in IM) else None
PACKS = []
for _p in DATA['packages']:
    if _p.get('status', 'Published') != 'Published' or not _p.get('name') or not _p.get('days'): continue
    p = dict(_p); p['all'] = p.get('inc') or COMMON; p['inc'] = []
    p['hero'] = _img(p.get('hero')); p.setdefault('t', [p['name'], '']); p.setdefault('tags', ['bus'])
    p['ndays'] = int(p.get('ndays') or len(p['days'])); p.setdefault('facts', []); p.setdefault('audience', 'College groups')
    p['title'] = p.get('title') or (p['name'] + ' Tour Package – ' + p['len']); p['desc'] = p.get('desc') or p.get('sum', '')
    p['price'] = int(p['price']) if str(p.get('price') or '').isdigit() else None
    PACKS.append(p)
_SL = {p['slug']: i for i, p in enumerate(PACKS)}
DEST, DEST_MORE = [], {}
for _d in DATA['destinations']:
    if _d.get('status', 'Published') != 'Published': continue
    d = dict(_d); d['packs'] = [_SL[s] for s in d.get('packs', []) if s in _SL]; d['img'] = _img(d.get('img'))
    if not d['packs']: WARN.append('destination hidden (no published package): ' + d['id']); continue
    DEST.append(d); DEST_MORE[d['id']] = {'intro': d.get('intro', ''), 'tips': d.get('tips', [])}
for _d in DEST_MORE.values():
    if not _d['tips']: _d['tips'] = list(CARRY)
DID = {d['id']: d for d in DEST}
GALLERY = [g for g in DATA['gallery'] if g.get('key') in IM]
CAP = {g['key']: g['cap'] for g in GALLERY}
GAL = [(g['key'], g['dest']) for g in GALLERY if g.get('dest') in DID]
HOMEKEY = _img(DATA['home'].get('heroKey')) or (GALLERY[0]['key'] if GALLERY else None)
IVKEY = _img('c3') or HOMEKEY
def dslug(d): return d['id']
def J(o): return json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
def waurl(t): return 'https://wa.me/%s?text=%s' % (WA, quote(t))
def price_txt(p): return ('From ₹' + format(p['price'], ',') + ' per person') if p.get('price') else 'On request'
pages = []
# ---------- icons ----------
ICO = {
 'wa': '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.3.8 3.2.7.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/></svg>',
 'call': '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>',
 'quote': '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v12H7l-3 3z"/></svg>',
 'menu': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
 'prev': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
 'next': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>',
}

# ---------- images ----------
HS = '(max-aspect-ratio: 1/1) 230vw, 100vw'
def pic(key, alt, sizes='100vw', eager=False, cls='', w_attr=True):
    m = IM[str(key)]; s = m['slug']
    srcset = ', '.join(f'{R}assets/img/{s}-{w}.webp {w}w' for w in m['ws'])
    fb = f'{R}assets/img/{s}-{m["fb"]}.jpg'
    h = round(m['h'] * m['fb'] / m['w'])
    load = 'fetchpriority="high" decoding="async"' if eager else 'loading="lazy" decoding="async"'
    return (f'<picture{(" class=%s" % cls) if cls else ""}><source type="image/webp" srcset="{srcset}" sizes="{sizes}">'
            f'<img src="{fb}" alt="{E(alt)}" width="{m["fb"]}" height="{h}" {load}></picture>')
def art(lines, cls='art'):
    return f'<div class="{cls}" aria-hidden="true"><svg viewBox="0 0 200 60" preserveAspectRatio="none"><path d="M0 50 C60 10 120 70 200 8" fill="none" stroke="rgba(243,112,33,.55)" stroke-width="1.2" stroke-dasharray="3 4"/></svg><span>{" · ".join(E(x) for x in lines)}</span></div>'
def pstops(p): return [x.strip() for x in p['name'].replace(' by Train', '').split('+')]
def full(key):
    m = IM[str(key)]; return f'{R}assets/img/{m["slug"]}-{m["ws"][-1]}.webp'
def ogimg(key, fallback=None):
    if key and key in IM: return f'{SITE}/assets/og/{IM[str(key)]["slug"]}.jpg'
    return f'{SITE}/assets/og/{fallback if fallback in OGCARDS else "trip-campus"}.jpg'
def preload(key):
    m = IM[str(key)]; s = m['slug']
    return (f'<link rel="preload" as="image" type="image/webp" fetchpriority="high" imagesrcset="'
            + ', '.join(f'{R}assets/img/{s}-{w}.webp {w}w' for w in m['ws']) + f'" imagesizes="{HS}">')

# ---------- shared blocks ----------
NAV = [('index.html', 'Home'), ('packages/', 'Packages'), ('destinations/', 'Destinations'), ('guides/', 'Guides'), ('gallery.html', 'Gallery'), ('services.html', 'Services'), ('contact.html', 'Contact')]
def href(p): return R + (p + 'index.html' if p.endswith('/') else p)

ORG = {"@type": "TravelAgency", "@id": SITE + "/#org", "name": "Trip Campus Tourism", "alternateName": [BRAND, LEGAL],
       "url": SITE + "/", "logo": SITE + "/assets/img/trip-campus-logo.png", "image": SITE + "/assets/og/trip-campus.jpg",
       "description": "Tour operator in Edappal, Kerala planning train and bus group tours for colleges and families, plus flights, hotels, visas and attestation.",
       "telephone": PHONES[0][0], "email": EMAIL, "sameAs": [INSTAGRAM],
       "address": {"@type": "PostalAddress", "streetAddress": ADDRESS['street'], "addressLocality": ADDRESS['locality'], "addressRegion": ADDRESS['region'], "postalCode": ADDRESS['postal'], "addressCountry": ADDRESS['country']},
       "areaServed": [{"@type": "State", "name": "Kerala"}, {"@type": "Country", "name": "India"}],
       "contactPoint": [{"@type": "ContactPoint", "telephone": t, "contactType": "customer service", "areaServed": "IN", "availableLanguage": ["en", "ml"]} for t, _ in PHONES[:2]],
       "knowsAbout": ["College tour packages", "Group tours from Kerala", "Train tour packages"]}

def crumbs_html(items):
    lis = ''.join(f'<li><a href="{u}">{E(n)}</a></li>' if u else f'<li aria-current="page">{E(n)}</li>' for n, u, _ in items)
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{lis}</ol></nav>'
def crumbs_ld(items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i+1, "name": n, "item": a} for i, (n, _, a) in enumerate(items)]}
def faq_ld(qs): return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qs]}
def faq_html(qs, first_open=True):
    return '<div class="faq">' + ''.join(f'<details{" open" if (i == 0 and first_open) else ""}><summary>{E(q)}</summary><p>{E(a)}</p></details>' for i, (q, a) in enumerate(qs)) + '</div>'

def enquiry_form(fid, pack_name=None):
    opts = ''.join(f'<option{" selected" if pack_name == p["name"] else ""}>{E(p["name"])}</option>' for p in PACKS)
    return f'''<form class="form" data-enquiry="{fid}" novalidate>
  <div class="row2"><label for="{fid}-name">Your name<input id="{fid}-name" name="name" autocomplete="name" required></label>
  <label for="{fid}-phone">Phone<input id="{fid}-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required></label></div>
  <label for="{fid}-pk">Package<select id="{fid}-pk" name="package"><option>Not sure yet</option>{opts}<option>A custom group tour</option></select></label>
  <div class="row2"><label for="{fid}-size">Group size<input id="{fid}-size" name="size" inputmode="numeric" placeholder="e.g. 45"></label>
  <label for="{fid}-month">Travel month<input id="{fid}-month" name="month" placeholder="e.g. January"></label></div>
  <label for="{fid}-note">College or group, boarding point, requests<textarea id="{fid}-note" name="note"></textarea></label>
  <label class="hp" aria-hidden="true">Leave this empty<input name="website" tabindex="-1" autocomplete="off"></label>
  <p class="err" role="alert" hidden></p>
  <button class="btn btn-wa" type="submit">{ICO["wa"]}Get a quote on WhatsApp</button>
  <p class="hint">Opens WhatsApp with your details filled in. Nothing is sent until you press send.</p>
</form>'''

def card(p, i, sizes='(min-width:1024px) 33vw, (min-width:640px) 50vw, 85vw'):
    tags = ' '.join(p['tags'] + ['d%d' % p['ndays'], 'short' if p['ndays'] <= 3 else 'long'])
    return f'''<article class="card" data-tags="{tags}">
  <div class="card-img">{pic(p["hero"], "A Trip Campus group on the " + p["name"] + " tour", sizes) if p["hero"] else art(pstops(p))}<span class="badge">{E(p["len"])}</span></div>
  <div class="card-body"><small>{E(p["place"])}</small>
    <h3><a href="{R}packages/{p["slug"]}.html">{E(p["name"])}</a></h3>
    <p>{E(p["sum"])}</p>
    <ul class="chips"><li>Starts {E(p["via"].replace("by tourist bus from your college", "from your college by bus"))}</li><li>{"IV / study tour" if p["audience"] == "College groups" else E(p["audience"])}</li></ul>
    <div class="card-foot"><span class="link">{("From ₹" + format(p["price"], ",") + " · ") if p.get("price") else ""}View itinerary →</span>
      <a class="wa-mini" href="{waurl("Hi Trip Campus, please share a quote for the " + p["name"] + " package.")}" data-wa="Hi Trip Campus, please share a quote for the {E(p["name"])} package." data-loc="card" target="_blank" rel="noopener" aria-label="Get a quote for {E(p["name"])} on WhatsApp">{ICO["wa"]}Quote</a></div>
  </div></article>'''

def page(path, title, desc, body, og=None, ld=(), active='', extra_head='', robots='index,follow', sheet_cta=True):
    global R
    canon = SITE + '/' + path.replace('index.html', '')
    og = og or SITE + '/assets/og/trip-campus.jpg'
    nav = ''.join(f'<a href="{href(u)}"{" aria-current=\"page\"" if active == n else ""}>{n}</a>' for u, n in NAV)
    sheet = ''.join(f'<a href="{href(u)}"{" aria-current=\"page\"" if active == n else ""}>{n}<span aria-hidden="true">→</span></a>' for u, n in NAV)
    graph = {"@context": "https://schema.org", "@graph": [ORG] + list(ld)}
    html = f'''<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#10140f">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website"><meta property="og:site_name" content="Trip Campus Tourism"><meta property="og:locale" content="en_IN">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{og}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{og}">
<meta name="geo.region" content="IN-KL"><meta name="geo.placename" content="Edappal">
<link rel="icon" href="{R}favicon.ico" sizes="32x32"><link rel="apple-touch-icon" href="{R}assets/icon-180.png"><link rel="manifest" href="{R}manifest.webmanifest">
<link rel="preload" href="{R}assets/fonts/dm-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{R}assets/fonts/oswald-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{R}assets/css/style.css">
{extra_head}
<script type="application/ld+json">{J(graph)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="hdr"><div class="wrap">
  <a class="logo" href="{R}index.html" aria-label="Trip Campus home"><img src="{R}assets/img/trip-campus-logo-light.png" alt="Trip Campus – the perfect travel partner" width="516" height="223"></a>
  <nav class="nav" aria-label="Main">{nav}</nav>
  <a class="btn btn-fill hdr-cta" href="{R}contact.html">Get a quote</a>
  <button class="menu-btn" id="menuBtn" aria-label="Menu" aria-expanded="false" aria-controls="sheet">{ICO["menu"]}</button>
</div></header>
<div class="sheet" id="sheet" hidden><nav aria-label="Mobile">{sheet}</nav>
  <div class="btns"><a class="btn btn-wa" href="{waurl("Hi Trip Campus, I would like to plan a group tour.")}" data-wa="" data-loc="menu" target="_blank" rel="noopener">{ICO["wa"]}WhatsApp</a><a class="btn" href="tel:{PHONES[0][0]}" data-loc="menu">{ICO["call"]}Call</a></div></div>
<main id="main">
{body}
</main>
<footer class="ftr"><div class="wrap">
  <div class="ftr-grid">
    <div><a class="logo" href="{R}index.html"><img src="{R}assets/img/trip-campus-logo-light.png" alt="Trip Campus" width="516" height="223" loading="lazy"></a>
      <p>Trip Campus Tourism plans train and bus group tours from Kerala for colleges and families. IATA accredited agent.</p>
      <p style="margin-top:10px">{ADDRESS["street"]}, {ADDRESS["locality"]} {ADDRESS["postal"]}, Kerala</p></div>
    <div><h2>Packages</h2><ul>{"".join(f'<li><a href="{R}packages/{p["slug"]}.html">{E(p["name"])}</a></li>' for p in PACKS[:6])}<li><a href="{R}packages/index.html">All packages</a></li></ul></div>
    <div><h2>Kerala trips</h2><ul>{"".join(f'<li><a href="{R}packages/{p["slug"]}.html">{E(p["name"])}</a></li>' for p in PACKS[6:])}<li><a href="{R}destinations/index.html">All destinations</a></li></ul></div>
    <div><h2>Contact</h2><ul>{"".join(f'<li><a href="tel:{t}" data-loc="footer">{n}</a></li>' for t, n in PHONES)}<li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram @tripcampus.co</a></li></ul></div>
  </div>
  <div class="ftr-base"><span>© <span id="year">2026</span> {LEGAL}</span><span><a href="{R}{IV['slug']}.html">IV and study tours</a> · <a href="{R}guides/index.html">Guides</a> · <a href="{R}services.html">Services</a> · <a href="{R}gallery.html">Gallery</a> · <a href="{R}contact.html">Contact</a></span></div>
</div></footer>
<nav class="bar" aria-label="Quick contact">
  <a href="tel:{PHONES[0][0]}" data-loc="bar">{ICO["call"]}Call</a>
  <a class="b-wa" href="{waurl("Hi Trip Campus, I would like to plan a group tour.")}" data-wa="" data-loc="bar" target="_blank" rel="noopener">{ICO["wa"]}WhatsApp</a>
  <a class="b-q" href="{R}contact.html#quote">{ICO["quote"]}Get quote</a>
</nav>
<a class="fab" href="{waurl("Hi Trip Campus, I would like to plan a group tour.")}" data-wa="" data-loc="fab" target="_blank" rel="noopener" aria-label="Chat with Trip Campus on WhatsApp">{ICO["wa"]}</a>
<script src="{R}assets/js/config.js"></script>
<script src="{R}assets/js/main.js" defer></script>
</body>
</html>
'''
    html = re.sub(r'\n\s*\n', '\n', html)
    # link to clean directory URLs (/packages/ not /packages/index.html), matching canonical tags
    html = re.sub(r'href="(/?(?:\.\./)*(?:[a-z0-9-]+/)*)index\.html(#[^"]*)?"', lambda m: 'href="%s%s"' % (m.group(1) or './', m.group(2) or ''), html)
    os.makedirs(os.path.dirname(OUT + '/' + path) or OUT, exist_ok=True)
    open(OUT + '/' + path, 'w', encoding='utf-8').write(html)
    if robots.startswith('index'): pages.append(path)

def depth(path): global R; R = '../' * path.count('/')

# ======================= HOME =======================
depth('index.html')
HP = [p for p in PACKS if p['hero'] and p.get('inHero', True)]
brand = f'''<article class="slide" aria-roledescription="slide" aria-label="1 of {len(HP)+1}: College tours from Kerala">
  {pic(HOMEKEY, 'A Trip Campus college group on the beach', HS, eager=True)}
  <div class="slide-body"><div>
    <span class="place">Trip Campus Tourism, Edappal</span>
    <h2><span>College tours</span><span>from Kerala</span></h2>
    <p>{len(PACKS)} group tours by train and bus to Goa, Karnataka, Maharashtra, Tamil Nadu and the hills of Kerala, with stay, meals and tickets arranged.</p>
    <p class="slide-meta"><b>3 to 6 days</b> · for colleges and families</p>
    <div class="btns"><a class="btn btn-fill" href="packages/index.html">See all packages</a>
      <a class="btn" href="{waurl("Hi Trip Campus, I would like to plan a college tour.")}" data-wa="Hi Trip Campus, I would like to plan a college tour." data-loc="hero" target="_blank" rel="noopener">{ICO["wa"]}Get a quote</a></div>
  </div></div></article>'''
slides = brand + ''.join(f'''<article class="slide" aria-roledescription="slide" aria-label="{i+2} of {len(HP)+1}: {E(p["name"])}">
  {pic(p["hero"], "A Trip Campus group on the " + p["name"] + " tour", HS)}
  <div class="slide-body"><div>
    <span class="place">{E(p["place"])}</span>
    <h2><span>{E(p["t"][0])}</span><span>{E(p["t"][1])}</span></h2>
    <p>{E(p["sum"])}</p>
    <p class="slide-meta"><b>{E(p["len"])}</b> · {E(p["via"])}</p>
    <div class="btns"><a class="btn btn-fill" href="packages/{p["slug"]}.html">View itinerary</a>
      <a class="btn" href="{waurl("Hi Trip Campus, please share the " + p["name"] + " itinerary and a quote.")}" data-wa="Hi Trip Campus, please share the {E(p["name"])} itinerary and a quote." data-loc="hero" target="_blank" rel="noopener">{ICO["wa"]}Get a quote</a></div>
  </div></div></article>''' for i, p in enumerate(HP))
dots = ''.join(f'<button aria-label="Show {E(n)}" aria-current="{"true" if i == 0 else "false"}"></button>' for i, n in enumerate(['College tours from Kerala'] + [p['name'] for p in HP]))
thumbs = '<button aria-label="Show College tours from Kerala" hidden>' + pic(HOMEKEY, '', '150px') + '<span>College tours</span></button>' + ''.join(f'<button aria-label="Show {E(p["name"])}">{pic(p["hero"], "", "150px")}<span>{E(p["name"].replace(" by Train", ""))}</span></button>' for p in HP)
realrail = ''.join(f'<button class="photo" data-full="{full(r["key"])}" data-cap="{E(r["cap"])}">{pic(r["key"], r["cap"] + " on a Trip Campus tour", "(min-width:1024px) 25vw, (min-width:640px) 46vw, 82vw")}<span>{E(r["cap"])}</span></button>' for r in GALLERY[:10])
tiles = ''.join(f'<a class="tile{" nophoto" if d["img"] is None else ""}" href="destinations/{dslug(d)}.html">{pic(d["img"], "A Trip Campus group in " + d["name"], "(min-width:1024px) 25vw, (min-width:640px) 33vw, 50vw") if d["img"] is not None else art([d["name"]])}<div><small>{E(d["state"])}</small><b>{E(d["name"])}</b><span>{len(d["packs"])} package{"s" if len(d["packs"]) > 1 else ""}</span></div></a>' for d in DEST)
home = f'''<section class="hero" aria-roledescription="carousel" aria-label="Trip Campus tour packages">
  <h1 class="hero-h1">Group tour packages from Kerala for colleges and families</h1>
  <div class="slides" id="slides">{slides}</div>
  <div class="dots" id="dots">{dots}<span class="count js-count" aria-hidden="true">01</span></div>
  <div class="thumbs" id="thumbs" aria-label="More packages">{thumbs}</div>
  <div class="h-arrows"><button id="hPrev" aria-label="Previous package">{ICO["prev"]}</button><button id="hNext" aria-label="Next package">{ICO["next"]}</button><div class="track"><i id="hBar"></i></div><span class="count js-count" aria-hidden="true">01</span></div>
</section>

<section class="sec"><div class="wrap split">
  <div><span class="eyebrow">Trip Campus Tourism, Edappal</span>
    <h2>The perfect travel partner for your group</h2>
    <p class="lead">Trip Campus plans college tours and family group trips from Kerala to Goa, Karnataka, Maharashtra, Tamil Nadu and the hills of Kerala. We book the train or tourist bus, rooms, three meals a day, entry tickets and sightseeing, so your group only has to show up.</p>
    <ul class="trust"><li class="hl">IATA accredited agent</li><li>Train and bus tours</li><li>Meals and stay included</li><li>3 to 6 day trips</li></ul>
    <div class="btns"><a class="btn btn-fill" href="packages/index.html">See all {len(PACKS)} packages</a><a class="btn" href="contact.html#quote">Plan a custom trip</a></div></div>
  <div class="panel" style="margin-top:28px"><h3 style="margin-bottom:14px">Every group tour includes</h3>
    <ul class="ticks"><li>Train tickets or a tourist bus for the whole route</li><li>Rooms on a share basis</li><li>Three unlimited meals a day</li><li>All entry tickets</li><li>Toll, parking and taxes</li><li>Sightseeing and activities in the plan</li></ul></div>
</div></section>

<section class="sec alt" aria-labelledby="pk-h"><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">Tour packages</span><h2 id="pk-h">Popular group tours</h2></div><a class="link" href="packages/index.html">All packages →</a></div>
  <div class="rail cards-rail">{"".join(card(p, i, "(min-width:1024px) 33vw, (min-width:640px) 46vw, 82vw") for i, p in enumerate(PACKS))}</div>
</div></section>

<section class="sec" aria-labelledby="rt-h"><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">College groups on the road with Trip Campus</span><h2 id="rt-h">Recent trips</h2></div><a class="link" href="gallery.html">Full gallery →</a></div>
  <div class="rail">{realrail}</div>
  <h3 style="margin:36px 0 14px">Colleges that travelled with us</h3>
  <ul class="colleges">{"".join(f"<li>{E(c)}</li>" for c in COLLEGES)}</ul>
</div></section>

<section class="sec" aria-labelledby="iv-h"><div class="wrap"><div class="band">
  <div><span class="eyebrow" style="color:#fff">For class tours</span><h2 id="iv-h">IV and study tour packages</h2><p>Planning your department's IV (industrial visit) or study tour? Every Trip Campus package can be booked for a whole class, with train or bus, stay, meals and tickets arranged.</p></div>
  <div class="btns" style="margin:0"><a class="btn btn-fill" href="{IV['slug']}.html">IV packages</a></div>
</div></div></section>

<section class="sec alt" aria-labelledby="ds-h"><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">Where we go</span><h2 id="ds-h">{len(DEST)} destinations</h2></div><a class="link" href="destinations/index.html">All destinations →</a></div>
  <div class="tiles">{tiles}</div>
</div></section>

<section class="sec" aria-labelledby="gd-h"><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">Trip planning</span><h2 id="gd-h">Guides for college trips</h2></div><a class="link" href="guides/index.html">All guides →</a></div>
  <div class="plinks gl">{"".join(f'<a class="plink" href="guides/{x["slug"]}.html"><div><b>{E(x["h1"])}</b><small>{E(x["kicker"])}</small></div><span aria-hidden="true">→</span></a>' for x in GUIDES)}</div>
</div></section>

<section class="sec alt" aria-labelledby="how-h"><div class="wrap">
  <span class="eyebrow">Booking is simple</span><h2 id="how-h" style="margin-bottom:20px">How it works</h2>
  <ol class="steps"><li><b>Pick a trip</b><span>Choose a package or tell us where your group wants to go.</span></li>
    <li><b>Share your group details</b><span>Group size, travel month and boarding point, on WhatsApp or a call.</span></li>
    <li><b>Get your itinerary and quote</b><span>We confirm the plan and book train or bus, stay, meals and tickets.</span></li></ol>
</div></section>

<section class="sec" aria-labelledby="faq-h"><div class="wrap split">
  <div><span class="eyebrow">Questions</span><h2 id="faq-h">Frequently asked questions</h2><p class="lead">Can't find your answer? Call {PHONES[0][1]} or message us on WhatsApp.</p></div>
  {faq_html(HOME_FAQ)}
</div></section>

<section class="sec"><div class="wrap"><div class="band">
  <div><h2>Planning a college tour?</h2><p>Tell us your group size and month. We will send the itinerary and a quote on WhatsApp.</p></div>
  <div class="btns" style="margin:0"><a class="btn btn-wa" href="{waurl("Hi Trip Campus, I would like to plan a college tour.")}" data-wa="Hi Trip Campus, I would like to plan a college tour." data-loc="band" target="_blank" rel="noopener">{ICO["wa"]}WhatsApp us</a><a class="btn" href="tel:{PHONES[0][0]}" data-loc="band">{ICO["call"]}Call</a></div>
</div></div></section>
<dialog class="lb" id="lb" aria-label="Photo"><button class="lb-x" aria-label="Close photo">×</button><img id="lbImg" alt=""><p id="lbCap"></p></dialog>'''
home_ld = [{"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "Trip Campus Tourism", "inLanguage": "en-IN", "publisher": {"@id": SITE + "/#org"}},
           faq_ld(HOME_FAQ),
           {"@type": "ItemList", "name": "Trip Campus tour packages", "itemListElement": [{"@type": "ListItem", "position": i+1, "url": f"{SITE}/packages/{p['slug']}.html", "name": p['name']} for i, p in enumerate(PACKS)]}]
page('index.html', 'College Tour Packages from Kerala | Trip Campus, Edappal',
     'Group tour packages from Kerala for colleges and families: Goa, Dandeli, Hampi, Gokarna, Chikmagalur, Munnar, Wayanad and more. Stay and meals included.',
     home, ld=home_ld, active='Home', extra_head=preload(HOMEKEY))

# ======================= PACKAGES INDEX =======================
depth('packages/index.html')
cr = [('Home', '../index.html', SITE + '/'), ('Packages', None, SITE + '/packages/')]
filters = [('', 'All'), ('train', 'By train'), ('bus', 'By bus'), ('short', '3 days'), ('long', '4–6 days')]
body = f'''<div class="wrap">{crumbs_html(cr)}</div>
<section class="sec pbasic"><div class="wrap">
  <span class="eyebrow">Group tours from Kerala</span><h1>Tour packages</h1>
  <p class="lead">{len(PACKS)} group tours by train and tourist bus for college tours, IVs, study tours and family trips. Every package includes stay, three meals a day, entry tickets and sightseeing. Dates, group size and boarding point are fixed with each group.</p>
  <div class="filters" role="group" aria-label="Filter packages" data-filter-group="#pkGrid" data-count="#pkCount" style="margin-top:24px">{"".join(f'<button class="filter" data-v="{v}" aria-pressed="{"true" if not v else "false"}">{n}</button>' for v, n in filters)}</div>
  <p class="result-count" id="pkCount" aria-live="polite">{len(PACKS)} packages</p>
  <div class="cards" id="pkGrid">{"".join(card(p, i) for i, p in enumerate(PACKS))}</div>
  <p class="hint" style="margin-top:28px">Not included in any package: camera and video fees inside monuments, travel insurance and personal expenses.</p>
</div></section>'''
page('packages/index.html', 'Tour Packages from Kerala for College Groups | Trip Campus',
     'Compare 9 group tours from Kerala by train or bus: Dandeli, Goa, Hampi, Gokarna, Chikmagalur, Mumbai, Munnar, Wayanad and Kodaikanal. 3 to 6 days.',
     body, ld=[crumbs_ld(cr), {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i+1, "url": f"{SITE}/packages/{p['slug']}.html", "name": p['name']} for i, p in enumerate(PACKS)]}],
     active='Packages')

# ======================= PACKAGE PAGES =======================
for i, p in enumerate(PACKS):
    path = f'packages/{p["slug"]}.html'; depth(path)
    dests = [d for d in DEST if i in d['packs']]
    inc = p.get('all') or COMMON + p.get('inc', [])
    cr = [('Home', '../index.html', SITE + '/'), ('Packages', 'index.html', SITE + '/packages/'), (p['name'], None, f'{SITE}/{path}')]
    mode = 'Train and tourist bus' if 'train' in p['via'] else 'Tourist bus'
    qs = [
     (f'How many days is the {p["name"]} tour?', f'{p["len"]}. The day-by-day plan above shows the full route: {p["route"]}.'),
     ('Where does the trip start?', f'The trip starts {p["via"]}. The boarding point can be discussed with Trip Campus when you book.'),
     ('What is included in the package?', 'Included: ' + '; '.join(inc) + '. Not included: ' + '; '.join(EXCLUDED).lower() + '.'),
     ('Is food included?', f'Yes, three unlimited meals a day (chicken is limited). Breakfast is any three items from {BREAKFAST.lower()}. Lunch and dinner are any two items from {MEALS.lower()}, subject to availability.'),
     (f'What is the price of the {p["name"]} package?', ((f'Prices start from ₹{p["price"]:,} per person. ' if p.get('price') else '') + 'The final price depends on group size, travel dates and boarding point. Send your group details on WhatsApp or call ' + PHONES[0][1] + ' for a quote.')),
     ('What should we carry?', '; '.join(CARRY) + '.'),
    ]
    if p['audience'] == 'College groups':
        qs.insert(1, (f'Can we book the {p["name"]} tour as an IV or study tour?', f'Yes. Many Kerala colleges book this {p["len"].lower()} trip as their IV (industrial visit) or study tour. Trip Campus plans it for the whole class, with transport, stay, meals and entry tickets arranged. Ask if your department needs a company or institution visit added.'))
    who = ('Planned for college groups, and booked by many Kerala colleges as an IV (industrial visit) or study tour. Groups travel with a dedicated tourist bus, and teachers can travel with the class.'
           if p['audience'] == 'College groups' else 'Planned for families and friends groups, and also suitable for a short college trip. The group travels together in a dedicated tourist bus from your starting point.')
    related = [q for q in PACKS if q is not p and set(q['tags']) & set(p['tags'])][:3]
    body = f'''<section class="phero{"" if p["hero"] else " noimg"}">{pic(p["hero"], "A Trip Campus group on the " + p["name"] + " tour", HS, eager=True) if p["hero"] else art(pstops(p), "art big")}
  <div class="wrap">{crumbs_html(cr)}<span class="eyebrow" style="margin-top:14px">{E(p["place"])} · {E(p["audience"])}</span>
  <h1>{E(p["name"])} tour package</h1><p class="sub">{E(p["sum"])}</p></div></section>
<div class="wrap">
  <dl class="facts"><div><dt>Duration</dt><dd>{E(p["len"])}</dd></div><div><dt>Starts from</dt><dd>{E(p["from"][0].upper() + p["from"][1:])}</dd></div><div><dt>Travel</dt><dd>{mode}</dd></div><div><dt>Price</dt><dd>{E(price_txt(p))}</dd></div></dl>
  <div class="btns"><a class="btn btn-wa" href="{waurl("Hi Trip Campus, please share a quote for the " + p["name"] + " package.")}" data-wa="Hi Trip Campus, please share a quote for the {E(p["name"])} package." data-loc="pack-top" target="_blank" rel="noopener">{ICO["wa"]}Get a quote on WhatsApp</a><a class="btn" href="tel:{PHONES[0][0]}" data-loc="pack-top">{ICO["call"]}Call {PHONES[0][1]}</a></div>
</div>
<section class="sec"><div class="wrap layout">
  <div class="block" style="gap:40px">
    <div class="block"><h2>Who this tour is for</h2><p class="about">{E(who)}{' <a class="link" href="../' + IV['slug'] + '.html">IV and study tours →</a>' if p['audience'] == 'College groups' else ''}</p></div>
    <div class="block"><h2>Route and highlights</h2><p class="about">{E(p["route"])}</p><ul class="chips">{"".join(f"<li>{E(f)}</li>" for f in p["facts"])}</ul></div>
    <div class="block"><h2>Day-by-day itinerary</h2><ol class="days">{"".join(f'<li><b>Day {k+1}</b><p>{E(d)}</p></li>' for k, d in enumerate(p["days"]))}</ol></div>
    <div class="block"><h2>What's included</h2><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in inc)}</ul>
      <h3 style="margin-top:10px">Not included</h3><ul class="ticks x">{"".join(f"<li>{E(x)}</li>" for x in EXCLUDED)}</ul></div>
    <div class="block"><h2>Food on the trip</h2><p class="about"><b>Breakfast</b>, any three items: {E(BREAKFAST)}.</p><p class="about"><b>Lunch and dinner</b>, any two items: {E(MEALS)}. Items are subject to availability and meals are single item.</p></div>
    <div class="block"><h2>Things to carry</h2><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in CARRY)}</ul>
      <p class="hint">{" ".join(E(x) for x in NOTES)}</p></div>
    <div class="block"><h2>Destinations on this tour</h2><div class="tiles">{"".join(f'<a class="tile{" nophoto" if d["img"] is None else ""}" href="../destinations/{dslug(d)}.html">{pic(d["img"], "A Trip Campus group in " + d["name"], "(min-width:1024px) 20vw, 50vw") if d["img"] is not None else art([d["name"]])}<div><small>{E(d["state"])}</small><b>{E(d["name"])}</b></div></a>' for d in dests)}</div></div>
    <div class="block"><h2>Questions about this tour</h2>{faq_html(qs)}</div>
  </div>
  <aside class="aside" id="quote"><div class="panel"><h2 style="font-size:26px;margin-bottom:6px">Get a quote</h2><p class="hint" style="margin-bottom:16px">Send your group details and Trip Campus will reply with the itinerary and price.</p>{enquiry_form("pk" + str(i), p["name"])}</div></aside>
</div></section>
<section class="sec alt"><div class="wrap"><div class="sec-head"><h2>Similar tours</h2><a class="link" href="index.html">All packages →</a></div>
  <div class="cards">{"".join(card(q, 0) for q in related)}</div></div></section>'''
    trip = {"@type": "TouristTrip", "@id": f"{SITE}/{path}#trip", "name": p['name'] + ' tour package', "description": p['desc'],
            "url": f"{SITE}/{path}", "image": ogimg(p['hero'], 'pkg-' + p['slug']), "touristType": p['audience'],
            "provider": {"@id": SITE + "/#org"},
            "itinerary": {"@type": "ItemList", "numberOfItems": len(p['days']), "itemListElement": [{"@type": "ListItem", "position": k+1, "name": f"Day {k+1}", "description": d} for k, d in enumerate(p['days'])]},
            "subjectOf": {"@type": "WebPage", "@id": f"{SITE}/{path}"}}
    if p.get('price'): trip["offers"] = {"@type": "Offer", "price": str(p['price']), "priceCurrency": "INR", "url": f"{SITE}/{path}", "availability": "https://schema.org/InStock", "description": "Starting price per person"}
    title = p['title'] + (' | Trip Campus' if len(p['title']) <= 46 else '')
    page(path, title, p['desc'], body, og=ogimg(p['hero'], 'pkg-' + p['slug']), ld=[crumbs_ld(cr), trip, faq_ld(qs)], active='Packages', extra_head=preload(p['hero']) if p['hero'] else '')

# ======================= DESTINATIONS =======================
depth('destinations/index.html')
cr = [('Home', '../index.html', SITE + '/'), ('Destinations', None, SITE + '/destinations/')]
types = [('', 'All')] + [(t.replace(' ', '-').replace('&', 'and').lower(), t) for t in dict.fromkeys(d['type'] for d in DEST)]
def tkey(t): return t.replace(' ', '-').replace('&', 'and').lower()
body = f'''<div class="wrap">{crumbs_html(cr)}</div>
<section class="sec pbasic"><div class="wrap">
  <span class="eyebrow">Where Trip Campus goes</span><h1>Destinations</h1>
  <p class="lead">{len(DEST)} places across Kerala, Tamil Nadu, Karnataka, Goa and Maharashtra, reached by train or tourist bus from Kerala. Pick one to see what you do there and which packages include it.</p>
  <div class="filters" role="group" aria-label="Filter destinations" data-filter-group="#dGrid" style="margin-top:24px">{"".join(f'<button class="filter" data-v="{v}" aria-pressed="{"true" if not v else "false"}">{n}</button>' for v, n in types)}</div>
  <div class="tiles" id="dGrid">{"".join(f'<a class="tile{" nophoto" if d["img"] is None else ""}" data-tags="{tkey(d["type"])}" href="{dslug(d)}.html">{pic(d["img"], "A Trip Campus group in " + d["name"], "(min-width:1024px) 25vw, (min-width:640px) 33vw, 50vw") if d["img"] is not None else art([d["name"]])}<div><small>{E(d["state"])} · {E(d["type"])}</small><b>{E(d["name"])}</b><span>{E(d["hook"])}</span></div></a>' for d in DEST)}</div>
</div></section>'''
page('destinations/index.html', 'Group Tour Destinations from Kerala | Trip Campus',
     '13 group tour destinations from Kerala: Goa, Dandeli, Hampi, Gokarna, Chikmagalur, Mumbai, Munnar, Wayanad, Kodaikanal and more, with things to do.',
     body, ld=[crumbs_ld(cr)], active='Destinations')

for d in DEST:
    path = f'destinations/{dslug(d)}.html'; depth(path)
    dp = [PACKS[i] for i in d['packs']]
    photos = [g[0] for g in GAL if g[1] == d['id']]
    vias = list(dict.fromkeys(p['via'] for p in dp))
    qs = [(f'When is the best time to visit {d["name"]}?', d['when']),
          (f'How do we get to {d["name"]} from Kerala?', ', or '.join(vias)[0].upper() + ', or '.join(vias)[1:] + '. Trip Campus arranges the transport, stay and meals for the whole group.'),
          (f'Which Trip Campus packages include {d["name"]}?', ', '.join(p['name'] + ' (' + p['len'] + ')' for p in dp) + '.'),
          ('What should we carry?', '; '.join(CARRY) + '.')]
    more = DEST_MORE[d['id']]
    # sample day: the longest itinerary day that mentions this place
    cand = [(len(day), day, p, k) for p in dp for k, day in enumerate(p['days']) if d['name'].lower() in day.lower()]
    _, sday, spack, sk = max(cand, key=lambda x: (x[0], -PACKS.index(x[2]))) if cand else (0, '', dp[0], 0)
    reach = (f'Trip Campus groups reach {d["name"]} ' + ' or '.join(vias) + '. ' +
             ' '.join(f'On the {p["name"]} tour ({p["len"]}), the route is {p["route"]}.' for p in dp[:3]) +
             ' The train or bus, stay and meals are arranged for the whole group.')
    cr = [('Home', '../index.html', SITE + '/'), ('Destinations', 'index.html', SITE + '/destinations/'), (d['name'], None, f'{SITE}/{path}')]
    heroimg = pic(d['img'], f'A Trip Campus group in {d["name"]}', HS, eager=True) if d['img'] is not None else art([d['name']], 'art big')
    body = f'''<section class="phero{"" if d["img"] else " noimg"}">{heroimg}<div class="wrap">{crumbs_html(cr)}<span class="eyebrow" style="margin-top:14px">{E(d["state"])} · {E(d["type"])}</span>
  <h1>{E(d["name"])} tour packages</h1><p class="sub">{E(d["hook"])}</p></div></section>
<section class="sec"><div class="wrap layout">
  <div class="block" style="gap:40px">
    <div class="block"><h2>About {E(d["name"])}</h2><p class="about">{E(d["about"])}</p><p class="about">{E(more["intro"])}</p></div>
    <div class="block"><h2>Things to do in {E(d["name"])}</h2><ul class="ticks">{"".join(f"<li>{E(t)}</li>" for t in d["todo"])}</ul></div>
    {f'<div class="block"><h2>Trip photos</h2><div class="masonry">' + "".join(f'<button class="photo" data-full="{full(k)}" data-cap="{E(CAP[k])}">{pic(k, CAP[k] + " in " + d["name"], "(min-width:1024px) 20vw, 50vw")}</button>' for k in photos) + '</div></div>' if photos else ''}
    {f'<div class="block"><h2>A day in {E(d["name"])} with Trip Campus</h2><p class="about">{E(sday)}</p><p class="hint">From day {sk + 1} of the <a class="link" href="../packages/{spack["slug"]}.html">{E(spack["name"])}</a> itinerary.</p></div>' if sday else ''}
    <div class="block"><h2>How to get to {E(d["name"])} from Kerala</h2><p class="about">{E(reach)}</p></div>
    <div class="block"><h2>Best time to visit {E(d["name"])}</h2><p class="about">{E(d["when"])}</p></div>
    <div class="block"><h2>Tips for college groups</h2><ul class="ticks">{"".join(f"<li>{E(t)}</li>" for t in more["tips"])}</ul></div>
    <div class="block"><h2>Good to know</h2>{faq_html(qs, first_open=False)}</div>
  </div>
  <aside class="aside"><div class="block"><h2 style="font-size:26px">Packages that include {E(d["name"])}</h2>
    <div class="plinks">{"".join(f'<a class="plink" href="../packages/{p["slug"]}.html"><div><b>{E(p["name"])}</b><small>{E(p["len"])} · {E(p["via"])}</small></div><span aria-hidden="true">→</span></a>' for p in dp)}</div>
    <a class="btn btn-wa" href="{waurl("Hi Trip Campus, I would like to plan a trip to " + d["name"] + ".")}" data-wa="Hi Trip Campus, I would like to plan a trip to {E(d["name"])}." data-loc="dest" target="_blank" rel="noopener">{ICO["wa"]}Plan a {E(d["name"])} trip</a></div></aside>
</div></section>
<dialog class="lb" id="lb" aria-label="Photo"><button class="lb-x" aria-label="Close photo">×</button><img id="lbImg" alt=""><p id="lbCap"></p></dialog>'''
    place = {"@type": "TouristDestination", "name": d['name'], "description": d['about'], "url": f"{SITE}/{path}",
             "containedInPlace": {"@type": "State", "name": d['state']}, "touristType": ["College groups", "Families"]}
    place["image"] = ogimg(d['img'], 'dest-' + d['id'])
    t = f'{d["name"]} Tour Packages from Kerala – {d["hook"]}'
    if len(t) > 60: t = f'{d["name"]} Tour Packages from Kerala'
    desc = f'{d["about"].split(". ")[0].rstrip(".")}. See Trip Campus group tours that include {d["name"]}, things to do and the best time to visit.'
    page(path, t + ' | Trip Campus' if len(t) <= 46 else t, desc[:158].rsplit(' ', 1)[0] + ('…' if len(desc) > 158 else ''), body,
         og=ogimg(d['img'], 'dest-' + d['id']), ld=[crumbs_ld(cr), place, faq_ld(qs)], active='Destinations',
         extra_head=preload(d['img']) if d['img'] is not None else '')

# ======================= GALLERY =======================
depth('gallery.html')
cr = [('Home', 'index.html', SITE + '/'), ('Gallery', None, SITE + '/gallery.html')]
gitems = ''.join(f'<button class="photo" data-tags="groups {r.get("dest") or ""}" data-full="{full(r["key"])}" data-cap="{E(r["cap"])}">{pic(r["key"], r["cap"] + " on a Trip Campus tour", "(min-width:1024px) 25vw, (min-width:640px) 33vw, 50vw")}<span>{E(r["cap"])}</span></button>' for r in GALLERY)
gf = [('', 'All')] + [(d['id'], d['name']) for d in DEST if any(t == d['id'] for _, t in GAL)]
body = f'''<div class="wrap">{crumbs_html(cr)}</div>
<section class="sec pbasic"><div class="wrap">
  <span class="eyebrow">Photos from the trips</span><h1>Gallery</h1>
  <p class="lead">Real photos of college groups Trip Campus has taken on tour. Tap a photo to see it full size.</p>
  <div class="filters" role="group" aria-label="Filter photos" data-filter-group="#gGrid" style="margin-top:24px">{"".join(f'<button class="filter" data-v="{v}" aria-pressed="{"true" if not v else "false"}">{E(n)}</button>' for v, n in gf)}</div>
  <div class="masonry" id="gGrid">{gitems}</div>
</div></section>
<dialog class="lb" id="lb" aria-label="Photo"><button class="lb-x" aria-label="Close photo">×</button><img id="lbImg" alt=""><p id="lbCap"></p></dialog>'''
gal_ld = {"@type": "ImageGallery", "name": "Trip Campus tour photos", "url": SITE + "/gallery.html",
          "image": [{"@type": "ImageObject", "contentUrl": f"{SITE}/assets/img/{IM[r['key']]['slug']}-{IM[r['key']]['fb']}.jpg", "caption": r['cap'] + ' on a Trip Campus tour'} for r in GALLERY for n in [0] if r['key'] in IM][:50]}
page('gallery.html', 'Trip Photos – College Tours with Trip Campus | Gallery',
     'Real photos of college groups on Trip Campus tours from Kerala, from Dandeli rafting and the Hampi ruins to Chikmagalur hills, beaches and forts.',
     body, og=ogimg(GALLERY[0]['key']) if GALLERY else None, ld=[crumbs_ld(cr), gal_ld], active='Gallery')

# ======================= SERVICES =======================
depth('services.html')
cr = [('Home', 'index.html', SITE + '/'), ('Services', None, SITE + '/services.html')]
sl = ''
for g in SERV:
    sl += f'<div class="sgroup"><h2>{E(g[0])}</h2>'
    for s in g[1]:
        link = f'<a class="link" href="packages/index.html">View packages →</a>' if len(s) > 3 else f'<a class="link" href="{waurl("Hi Trip Campus, I need help with: " + s[0] + ".")}" data-wa="Hi Trip Campus, I need help with: {E(s[0])}." data-loc="service" target="_blank" rel="noopener">Enquire on WhatsApp →</a>'
        sl += f'<div class="srv"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="{s[2]}"/></svg><div><h3>{E(s[0])}</h3><p>{E(s[1])}</p>{link}</div></div>'
    sl += '</div>'
body = f'''<div class="wrap">{crumbs_html(cr)}</div>
<section class="sec pbasic"><div class="wrap">
  <span class="eyebrow">More than tours</span><h1>Travel services</h1>
  <p class="lead">Trip Campus Tourism, Edappal, handles the travel and the paperwork around it: group tours, flight tickets, hotels, car rentals, insurance, visas, passports, certificate attestation, Hajj and Umrah, and business travel.</p>
  <ul class="trust"><li class="hl">IATA accredited agent</li></ul>
  <div style="margin-top:32px">{sl}</div>
  <div class="band" style="margin-top:40px"><div><h2>Tell us what you need</h2><p>{PHONES[0][1]} · {PHONES[1][1]}</p></div>
    <div class="btns" style="margin:0"><a class="btn btn-wa" href="{waurl("Hi Trip Campus, I need help with a travel service.")}" data-wa="Hi Trip Campus, I need help with a travel service." data-loc="services" target="_blank" rel="noopener">{ICO["wa"]}WhatsApp</a></div></div>
</div></section>'''
svc_ld = {"@type": "OfferCatalog", "name": "Trip Campus travel services", "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s[0], "description": s[1], "provider": {"@id": SITE + "/#org"}, "areaServed": "Kerala"}} for g in SERV for s in g[1]]}
page('services.html', 'Travel Agency in Edappal: Flights, Visa & Attestation',
     'IATA accredited travel agency in Edappal: group tours, flight tickets, hotels, car rentals, visa and passport help, certificate attestation, Hajj and Umrah.',
     body, ld=[crumbs_ld(cr), svc_ld], active='Services')

# ======================= CONTACT =======================
depth('contact.html')
cr = [('Home', 'index.html', SITE + '/'), ('Contact', None, SITE + '/contact.html')]
body = f'''<div class="wrap">{crumbs_html(cr)}</div>
<section class="sec pbasic"><div class="wrap">
  <span class="eyebrow">Plan your trip</span><h1>Contact Trip Campus</h1>
  <p class="lead">Tell us where your group wants to go and how many are travelling. The form opens WhatsApp with your details filled in.</p>
  <div class="layout" style="margin-top:28px">
    <div class="panel" id="quote"><h2 style="font-size:26px;margin-bottom:16px">Get a quote</h2>{enquiry_form("ct")}</div>
    <div class="contact-list">
      <div><h3>Call us</h3><ul class="phones">{"".join(f'<li><a href="tel:{t}" data-loc="contact">{n}</a></li>' for t, n in PHONES)}</ul></div>
      <div><h3>WhatsApp</h3><p><a href="{waurl("Hi Trip Campus, I would like to enquire.")}" data-wa="Hi Trip Campus, I would like to enquire." data-loc="contact" target="_blank" rel="noopener">{PHONES[0][1]}</a></p></div>
      <div><h3>Email</h3><p><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
      <div><h3>Visit the office</h3><address style="font-style:normal">Trip Campus Tourism<br>{ADDRESS["street"]}<br>{ADDRESS["locality"]} {ADDRESS["postal"]}, Kerala</address>
        <p style="margin-top:8px"><a href="{MAPS}" target="_blank" rel="noopener">Open in Google Maps</a></p></div>
      <div><h3>Follow</h3><p><a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram @tripcampus.co</a></p></div>
    </div>
  </div>
</div></section>'''
page('contact.html', 'Contact Trip Campus Tourism, Edappal – Get a Tour Quote',
     'Call or WhatsApp Trip Campus Tourism, Near CM Restaurant, Nellissery, Edappal 679578, Kerala, for college tour packages and group trip quotes. +91 89432 99434.',
     body, ld=[crumbs_ld(cr), {"@type": "ContactPage", "url": SITE + "/contact.html", "about": {"@id": SITE + "/#org"}}], active='Contact')

# ======================= 404 =======================
depth('404.html')
page('404.html', 'Page not found | Trip Campus', 'This page could not be found.', f'''<section class="sec"><div class="wrap"><span class="eyebrow">Error 404</span><h1>Page not found</h1>
<p class="lead">The page may have moved. Try the tour packages or contact us.</p><div class="btns"><a class="btn btn-fill" href="/packages/index.html">Tour packages</a><a class="btn" href="/index.html">Home</a></div></div></section>''', robots='noindex,follow')


# ======================= IV / STUDY TOUR LANDING =======================
path = IV['slug'] + '.html'; depth(path)
cr = [('Home', 'index.html', SITE + '/'), ('IV and study tours', None, f'{SITE}/{path}')]
college = [p for p in PACKS if p['audience'] == 'College groups']
body = f"""<section class="phero">{pic(IVKEY, 'A college group from Kerala on a Trip Campus IV tour in Dandeli', HS, eager=True)}
  <div class="wrap">{crumbs_html(cr)}<span class="eyebrow" style="margin-top:14px">College tours · IV · Study tours</span>
  <h1>{E(IV['h1'])}</h1><p class="sub">{E(IV['lead'])}</p>
  <div class="btns"><a class="btn btn-wa" href="{waurl('Hi Trip Campus, I would like a quote for our IV / study tour.')}" data-wa="Hi Trip Campus, I would like a quote for our IV / study tour." data-loc="iv-top" target="_blank" rel="noopener">{ICO['wa']}Get an IV quote</a><a class="btn" href="#iv-packages">See IV packages</a></div></div></section>
<section class="sec"><div class="wrap">
  <span class="eyebrow">Why colleges choose Trip Campus</span><h2 style="margin-bottom:20px">An IV planned from start to finish</h2>
  <ol class="steps">{''.join(f'<li><b>{E(a)}</b><span>{E(b)}</span></li>' for a, b in IV['why'])}</ol>
</div></section>
<section class="sec alt" id="iv-packages"><div class="wrap">
  <div class="sec-head"><div><span class="eyebrow">For college groups</span><h2>IV and study tour packages</h2></div><a class="link" href="packages/index.html">All packages →</a></div>
  <div class="cards">{''.join(card(p, 0) for p in college)}</div>
  <p class="hint" style="margin-top:20px">Shorter Kerala trips (3 days by bus) such as <a class="link" href="packages/munnar-vattavada-tour.html">Munnar and Vattavada</a> and <a class="link" href="packages/wayanad-900-woods-tour.html">Wayanad 900 Woods</a> also work as a quick class trip.</p>
</div></section>
<section class="sec"><div class="wrap">
  <span class="eyebrow">How to book</span><h2 style="margin-bottom:20px">Book your IV in three steps</h2>
  <ol class="steps"><li><b>Choose a route</b><span>Pick a package, or tell us the places and number of days your department wants.</span></li>
    <li><b>Send group details</b><span>Number of students and staff, travel month and boarding point.</span></li>
    <li><b>Confirm the plan</b><span>Trip Campus shares the itinerary and quote, then books transport, stay, meals and tickets.</span></li></ol>
</div></section>
<section class="sec alt"><div class="wrap layout">
  <div class="block"><h2>IV and study tour questions</h2>{faq_html(IV['faqs'])}
    <p class="about">Planning help: read the <a class="link" href="guides/college-tour-planning-checklist.html">college tour planning checklist</a> and the guide to the <a class="link" href="guides/best-college-tour-destinations-from-kerala.html">best college tour destinations from Kerala</a>.</p></div>
  <aside class="aside" id="quote"><div class="panel"><h2 style="font-size:26px;margin-bottom:6px">Get an IV quote</h2><p class="hint" style="margin-bottom:16px">Tell us your college, department and group size.</p>{enquiry_form('iv')}</div></aside>
</div></section>"""
svc = {"@type": "Service", "name": "IV and study tour packages from Kerala", "serviceType": "College tour packages", "description": IV['desc'],
       "provider": {"@id": SITE + "/#org"}, "areaServed": {"@type": "State", "name": "Kerala"}, "audience": {"@type": "EducationalAudience", "educationalRole": "student"},
       "hasOfferCatalog": {"@type": "OfferCatalog", "name": "IV packages", "itemListElement": [{"@type": "Offer", "itemOffered": {"@id": f"{SITE}/packages/{p['slug']}.html#trip"}} for p in college]}}
page(path, IV['title'], IV['desc'], body, og=ogimg(IVKEY), ld=[crumbs_ld(cr), svc, faq_ld(IV['faqs'])], extra_head=preload(IVKEY))

# ======================= GUIDES =======================
def table(head, rows):
    return ('<div class="tbl"><table><thead><tr>' + ''.join(f'<th scope="col">{E(h)}</th>' for h in head) + '</tr></thead><tbody>' +
            ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>')
def plink(p, pre=''): return f'<a class="link" href="{pre}../packages/{p["slug"]}.html">{E(p["name"])}</a>'
def dlink(d): return f'<a class="link" href="../destinations/{d["id"]}.html">{E(d["name"])}</a>'
P = {p['slug']: p for p in PACKS}

def guide_body(gd):
    s = gd['sections']
    if s == 'DEST_GUIDE':
        groups = [('Three-day trips in Kerala and Tamil Nadu', 'Bus trips that leave from your college at night. Ideal when your class can only spare a weekend and two days.', [p for p in PACKS if p['ndays'] == 3]),
                  ('Four-day trip to the Karnataka coast', 'A short train trip that still gets you river rafting and a beach.', [p for p in PACKS if p['ndays'] == 4]),
                  ('Five and six-day tours to Karnataka and Goa', 'The classic college tour from Kerala: forest adventure in Dandeli plus beaches, and either Hampi\'s ruins or Chikmagalur\'s peaks.', [p for p in PACKS if p['ndays'] >= 5 and 'Mumbai' not in p['name']]),
                  ('Five days in Maharashtra', 'Two hill stations and the city of Mumbai by sleeper train, for groups that want something different from Goa.', [p for p in PACKS if 'Mumbai' in p['name']])]
        out = ''
        for h, intro, ps in groups:
            ds = [DEST[k] for k in sorted({k for k, d in enumerate(DEST) for p in ps if PACKS.index(p) in d['packs']})]
            out += f'<h2>{E(h)}</h2><p>{E(intro)}</p>'
            for d in ds:
                out += f'<h3>{dlink(d)}: {E(d["hook"])}</h3><p>{E(d["about"].split(". ")[0])}. {E(DEST_MORE[d["id"]]["intro"].split(". ")[0])}.</p>'
            out += '<p><b>Packages:</b> ' + ', '.join(f'{plink(p)} ({E(p["len"])}, {E(p["via"])})' for p in ps) + '.</p>'
        out += '<h2>All packages at a glance</h2>' + table(['Package', 'Days', 'Starts', 'Best for'],
               [[plink(p), E(p['len']), E(p['via']), E(p['audience'])] for p in PACKS])
        out += '<h2>How to choose</h2><ul class="ticks"><li>Count the days you really have, including travel nights.</li><li>Mix one adventure day (Dandeli, Chikmagalur or a jeep safari) with one relaxed day (beach, lake or resort).</li><li>Check the season: beaches and Hampi are best from October to February; Kerala hills are good for most of the year outside heavy monsoon.</li><li>Ask the group what they want most: beaches, history, hills or adventure.</li></ul>'
        return out
    if s == 'DVG':
        dd, gk = DID['dandeli'], DID['gokarna']
        rows = [['Best for', 'Adventure and nature', 'Beaches, sunsets and temples'],
                ['Main activities', 'Rafting, kayaking, zorbing, zip line, forest trek, campfire', 'Om Beach, Kudle Beach, Yana Caves, Mirjan Fort, Murudeshwar'],
                ['Stay', 'Forest resort with pool and campfire', 'Usually visited as a day stop on the way back'],
                ['Best season', E(dd['when']), E(gk['when'])],
                ['What to pack', 'Quick-dry clothes, footwear that can get wet', 'Cap, sunscreen, sandals with grip']]
        out = '<h2>At a glance</h2>' + table(['', 'Dandeli', 'Gokarna'], rows)
        out += f'<h2>Choose Dandeli if your group wants adventure</h2><p>{E(dd["about"])}</p><p>{E(DEST_MORE["dandeli"]["intro"])}</p>'
        out += f'<h2>Choose Gokarna if your group wants the beach</h2><p>{E(gk["about"])}</p><p>{E(DEST_MORE["gokarna"]["intro"])}</p>'
        out += f'<h2>Or do both in one trip</h2><p>Dandeli and Gokarna are a few hours apart by road, so most groups combine them. The {plink(P["dandeli-gokarna-train-tour"])} takes 4 days from Kuttippuram by train: a full adventure day in Dandeli, then Yana Caves, Om Beach and Murudeshwar. The {plink(P["chikmagalur-dandeli-gokarna-tour"])} adds the peaks of Chikmagalur over 5 days, with pickup at Mangalore station.</p>'
        out += '<h2>Safety tips</h2><ul class="ticks">' + ''.join(f'<li>{E(t)}</li>' for t in DEST_MORE['dandeli']['tips'][:3] + DEST_MORE['gokarna']['tips'][:2]) + '</ul>'
        return out
    if s == 'CHECK':
        out = '<h2>Step by step</h2><ol class="steps steps-col">' + ''.join(f'<li><b>{E(a)}</b><span>{E(b)}</span></li>' for a, b in CHECKLIST) + '</ol>'
        out += '<h2>What a Trip Campus package already covers</h2><ul class="ticks">' + ''.join(f'<li>{E(x)}</li>' for x in COMMON) + '<li>Train tickets on train packages, and a tourist bus for the whole route</li></ul>'
        out += '<h2>Packing list</h2><ul class="ticks">' + ''.join(f'<li>{E(x)}</li>' for x in CARRY) + '</ul>'
        out += f'<p>Ready to plan? See the <a class="link" href="../{IV["slug"]}.html">IV and study tour packages</a> or compare all <a class="link" href="../packages/">tour packages</a>.</p>'
        return out
    if s == 'SHORT':
        ps = [p for p in PACKS if p['ndays'] == 3]
        out = '<h2>Compare the three trips</h2>' + table(['Trip', 'Highlights', 'Night stay', 'Best for'],
              [[plink(P['munnar-vattavada-tour']), 'Tea gardens, Gap Road, jeep trek to Vattavada falls and farms', 'Resort with infinity pool and campfire', 'Families and groups'],
               [plink(P['wayanad-900-woods-tour']), 'Lakkidi viewpoint, tribal village, jeep safari, Pookode Lake, Banasura Sagar Dam', 'Forest resort at 900 Woods with pool and campfire', 'Families and groups'],
               [plink(P['ramakkalmedu-kodaikanal-tour']), 'Jeep safari, ridge sunset, Guna Caves, Pillar Rocks, Kodai Lake', 'Ramakkalmedu, with campfire and DJ', 'College groups']])
        for p in ps:
            out += f'<h2>{E(p["name"])}</h2><p>{E(p["sum"])}</p><ol class="days">' + ''.join(f'<li><b>Day {k+1}</b><p>{E(x)}</p></li>' for k, x in enumerate(p['days'])) + '</ol><p>' + plink(p) + ' – full itinerary and quote.</p>'
        out += '<h2>How a 3-day bus trip works</h2><p>All three trips leave from your college at night, reach the hills early the next morning, and return overnight after the second full day. That means two nights on the bus and one night at a resort or stay, so carry a neck pillow and a warm layer for the bus.</p>'
        return out

depth('guides/index.html')
cr = [('Home', '../index.html', SITE + '/'), ('Guides', None, SITE + '/guides/')]
body = f"""<div class="wrap">{crumbs_html(cr)}</div>
<section class="sec pbasic"><div class="wrap">
  <span class="eyebrow">Trip planning</span><h1>College trip guides</h1>
  <p class="lead">Practical guides for planning a college tour, IV or group trip from Kerala: where to go, how to compare destinations and what to sort out before you leave.</p>
  <div class="plinks gl" style="margin-top:28px">{''.join(f'<a class="plink" href="{x["slug"]}.html"><div><b>{E(x["h1"])}</b><small>{E(x["desc"])}</small></div><span aria-hidden="true">→</span></a>' for x in GUIDES)}</div>
</div></section>"""
page('guides/index.html', 'College Trip Guides from Kerala | Trip Campus', 'Guides for planning a college tour, IV or study tour from Kerala: the best destinations, Dandeli vs Gokarna, 3-day trips and a planning checklist.',
     body, ld=[crumbs_ld(cr), {"@type": "CollectionPage", "name": "College trip guides", "url": SITE + "/guides/", "hasPart": [{"@type": "Article", "headline": x['h1'], "url": f"{SITE}/guides/{x['slug']}.html"} for x in GUIDES]}], active='Guides')

for gd in GUIDES:
    path = f'guides/{gd["slug"]}.html'; depth(path)
    try: _gb = guide_body(gd)
    except (KeyError, IndexError, ValueError) as ex:
        WARN.append('guide skipped: %s (%s)' % (gd['slug'], ex)); continue
    cr = [('Home', '../index.html', SITE + '/'), ('Guides', 'index.html', SITE + '/guides/'), (gd['h1'], None, f'{SITE}/{path}')]
    others = [x for x in GUIDES if x is not gd]
    body = f"""<div class="wrap">{crumbs_html(cr)}</div>
<article class="sec pbasic"><div class="wrap narrow">
  <span class="eyebrow">{E(gd['kicker'])}</span><h1>{E(gd['h1'])}</h1>
  <p class="byline">By Trip Campus Tourism, Edappal · Updated <time datetime="{PUBLISHED}">11 October 2026</time></p>
  <p class="lead">{E(gd['lead'])}</p>
  <div class="prose">{_gb}</div>
  <div class="band" style="margin-top:40px"><div><h2>Plan your trip with Trip Campus</h2><p>Send your group size and month on WhatsApp for an itinerary and quote.</p></div>
    <div class="btns" style="margin:0"><a class="btn btn-wa" href="{waurl('Hi Trip Campus, I read your guide and would like to plan a trip.')}" data-wa="Hi Trip Campus, I read your guide ({E(gd['h1'])}) and would like to plan a trip." data-loc="guide" target="_blank" rel="noopener">{ICO['wa']}WhatsApp us</a></div></div>
  <h2 class="more-h">More guides</h2><div class="plinks">{''.join(f'<a class="plink" href="{x["slug"]}.html"><div><b>{E(x["h1"])}</b><small>{E(x["kicker"])}</small></div><span aria-hidden="true">→</span></a>' for x in others)}</div>
</div></article>"""
    art_ld = {"@type": "Article", "headline": gd['h1'], "description": gd['desc'], "datePublished": PUBLISHED, "dateModified": PUBLISHED,
              "author": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"}, "mainEntityOfPage": f"{SITE}/{path}",
              "image": SITE + '/assets/og/trip-campus.jpg', "inLanguage": "en-IN"}
    page(path, gd['title'], gd['desc'], body, ld=[crumbs_ld(cr), art_ld], active='Guides')


def prio(pth): return '1.0' if pth == 'index.html' else '0.9' if pth.startswith('packages/') or pth.startswith('iv-') else '0.6' if pth.startswith('guides/') else '0.7' if pth.startswith('destinations/') else '0.6'
urls = ''.join(f'<url><loc>{SITE}/{"" if pth == "index.html" else pth.replace("index.html", "")}</loc><lastmod>{LASTMOD}</lastmod><priority>{prio(pth)}</priority></url>\n' for pth in pages)
open(OUT + '/sitemap.xml', 'w').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
open(OUT + '/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: {SITE}/sitemap.xml\n')
os.makedirs(OUT + '/assets/js', exist_ok=True)
open(OUT + '/assets/js/config.js', 'w').write('/* Written automatically when the site is published. Edit these in the admin Settings page. */\nwindow.TC_CONFIG = ' + json.dumps({"whatsapp": WA, "ga4": S_.get('ga4', ''), "metaPixel": S_.get('metaPixel', ''), "api": API_URL}) + ';\n')
