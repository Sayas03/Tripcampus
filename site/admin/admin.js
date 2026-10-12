/* Trip Campus admin — talks to the AWS API (API Gateway + Lambda) and Cognito login. No libraries. */
(function () {
  'use strict';
  var API = '/api';   // same server: nginx forwards /api/ to the Trip Campus app
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]; }); };
  var lines = function (s) { return String(s || '').split('\n').map(function (x) { return x.trim(); }).filter(Boolean); };
  var slugify = function (s) { return String(s || '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60); };
  var clone = function (o) { return JSON.parse(JSON.stringify(o)); };
  var fmtDate = function (iso) { if (!iso) return '—'; var d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString('en-IN', {day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit'}); };

  /* ------------------------------------------------------------------ toast */
  var tt;
  function toast(msg, bad) { var t = $('toast'); t.textContent = msg; t.className = 'toast' + (bad ? ' bad' : ''); t.hidden = false; clearTimeout(tt); tt = setTimeout(function () { t.hidden = true; }, bad ? 6000 : 2600); }

  /* ------------------------------------------------------------------ auth (one admin, secure session cookie) */
  var auth = null;   // {email} when signed in
  function call(method, path, body) {
    return fetch(API + path, {method: method, credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-TC': '1'}, body: body ? JSON.stringify(body) : undefined})
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) { var e = new Error(j.error || ('Server error ' + r.status)); e.status = r.status; throw e; } return j; }); });
  }

  /* ------------------------------------------------------------------ API */
  function api(method, path, body) {
    return call(method, path, body).catch(function (e) {
      if (e.status === 401) { signOut('Your session ended. Please sign in again.'); throw new Error('Signed out'); }
      throw e;
    });
  }

  /* ------------------------------------------------------------------ state */
  var D = null, LEADS = null, edit = null, draft = null, busy = false, loginStep = 'login', loginCtx = {};
  var TABS = [['dashboard', 'Dashboard'], ['packages', 'Packages'], ['destinations', 'Destinations'], ['gallery', 'Gallery'], ['enquiries', 'Enquiries'], ['settings', 'Settings']];
  function route() { var h = location.hash.slice(1).split('/'); return {tab: TABS.some(function (t) { return t[0] === h[0]; }) ? h[0] : 'dashboard', id: h[1] ? decodeURIComponent(h[1]) : null}; }
  function siteUrl(path) { return (D && D.settings.site ? D.settings.site.replace(/\/$/, '') : '..') + '/' + (path || ''); }
  function img(key, w) {
    var m = D && D.images[key]; if (!m) return '';
    var ws = m.ws || [m.fb]; var pick = ws.filter(function (x) { return x >= (w || 480); })[0] || ws[ws.length - 1];
    return '../assets/img/' + m.slug + '-' + pick + '.webp';
  }
  function save(message) {
    if (busy) return Promise.resolve(false);
    busy = true;
    return api('PUT', '/admin/data', {data: D, baseVersion: (D.meta && D.meta.version) || 0})
      .then(function (r) { D.meta = r.meta; toast(message || 'Saved'); return true; })
      .catch(function (e) { toast(e.message, true); return false; })
      .then(function (ok) { busy = false; render(); return ok; });
  }
  function publish(btn) {
    if (busy) return;
    busy = true; if (btn) { btn.disabled = true; btn.textContent = 'Publishing…'; }
    api('POST', '/admin/publish', {})
      .then(function (r) { D.meta = r.meta; toast('Website updated: ' + r.pages + ' pages in ' + r.seconds + 's. Changes appear within a minute.'); if (r.warnings && r.warnings.length) console.warn(r.warnings); })
      .catch(function (e) { toast('Publish failed: ' + e.message, true); })
      .then(function () { busy = false; render(); });
  }
  function loadAll() {
    return Promise.all([api('GET', '/admin/data'), api('GET', '/admin/leads').catch(function () { return {leads: []}; })])
      .then(function (r) { D = r[0]; LEADS = r[1].leads || []; render(); })
      .catch(function (e) { if (e.message !== 'Signed out') { $('app').innerHTML = '<div class="login"><div class="card"><h2>Could not load the admin</h2><p class="err">' + esc(e.message) + '</p><button class="btn" onclick="location.reload()">Try again</button></div></div>'; } });
  }
  function signOut(msg, local) { if (!local && auth) call('POST', '/auth/logout').catch(function () {}); auth = null; D = null; LEADS = null; loginStep = 'login'; render(); if (msg) toast(msg); }

  /* ------------------------------------------------------------------ login screens */
  function loginView() {
    var logo = '<div class="logo"><img src="../assets/img/trip-campus-logo.png" alt="Trip Campus"></div>';
    var body;
    if (loginStep === 'checking') return '<div class="boot">Loading…</div>';
    if (loginStep === 'forgot') body = '<h1>Forgot password</h1><p class="muted">For security, the admin password can only be reset on the server. Ask your developer to run:</p><pre style="background:#f3f5f2;padding:10px;border-radius:8px;overflow:auto">sudo tc-admin set-password</pre><button class="linkbtn" type="button" data-act="toLogin">Back to sign in</button>';
    else body = '<div><h1>Admin sign in</h1><p class="muted small" style="margin-top:6px">Manage packages, destinations, photos and enquiries.</p></div>' +
      (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1' ? '<p class="err">This page is not using HTTPS yet. Set up the domain and HTTPS before signing in.</p>' : '') +
      '<label class="f">Email<input id="lEmail" type="email" autocomplete="username" value="' + esc(loginCtx.email || '') + '" required></label>' +
      '<label class="f">Password<input id="lPass" type="password" autocomplete="current-password" required></label>' +
      '<p class="err" id="lErr" hidden></p><button class="btn primary" type="submit">Sign in</button><button class="linkbtn" type="button" data-act="toForgot">Forgot password?</button>';
    return '<div class="login"><form class="card" id="loginForm" novalidate>' + logo + body + '</form></div>';
  }
  function loginSubmit() {
    var err = $('lErr'), btn = document.querySelector('#loginForm .btn.primary');
    var fail = function (e) { err.textContent = e.message || String(e); err.hidden = false; btn.disabled = false; };
    btn.disabled = true; err.hidden = true;
    var email = $('lEmail').value.trim().toLowerCase(), pw = $('lPass').value; loginCtx.email = email;
    if (!email || !pw) return fail(new Error('Enter your email and password.'));
    call('POST', '/auth/login', {email: email, password: pw}).then(function (j) { auth = {email: j.email}; render(); loadAll(); }).catch(fail);
  }

  /* ------------------------------------------------------------------ shell */
  function head(title, sub, right) { return '<div class="head"><div><h1>' + esc(title) + '</h1>' + (sub ? '<p class="muted small">' + sub + '</p>' : '') + '</div><div class="row">' + (right || '') + '</div></div>'; }
  function pill(s) { return '<span class="pill ' + ({Published: 'ok', Booked: 'ok', New: 'warn', Contacted: 'off', Quoted: 'off', Draft: 'off', Lost: 'bad'}[s] || 'off') + '">' + esc(s) + '</span>'; }
  function topbar() {
    var m = D.meta || {};
    var state = m.dirty ? '<span class="dot dirty"></span><span><b>You have changes that are not on the website yet.</b> Publish when you are ready.</span>'
                        : '<span class="dot"></span><span>Website is up to date' + (m.publishedAt ? ' · published ' + esc(fmtDate(m.publishedAt)) : '') + '</span>';
    return '<div class="topbar"><div class="state">' + state + '</div><div class="row"><a class="btn sm" href="' + esc(siteUrl()) + '" target="_blank" rel="noopener">View website</a>' +
      '<button class="btn ' + (m.dirty ? 'primary' : '') + '" data-act="publish">Publish website</button></div></div>';
  }
  function shell(inner) {
    var r = route(), nNew = (LEADS || []).filter(function (l) { return l.status === 'New'; }).length;
    return '<div class="shell"><nav class="rail" aria-label="Admin"><a class="logo" href="#dashboard"><img src="../assets/img/trip-campus-logo.png" alt="Trip Campus admin"></a>' +
      TABS.map(function (t) { return '<a class="tab" href="#' + t[0] + '"' + (t[0] === r.tab ? ' aria-current="page"' : '') + '>' + t[1] + (t[0] === 'enquiries' && nNew ? '<span class="count">' + nNew + '</span>' : '') + '</a>'; }).join('') +
      '<div class="foot"><span class="small" style="opacity:.7">' + esc(auth && auth.email) + '</span><button data-act="signOut">Sign out</button></div></nav>' +
      '<main class="main">' + topbar() + inner + '</main></div>';
  }

  /* ------------------------------------------------------------------ views */
  var V = {};
  V.dashboard = function () {
    var pub = D.packages.filter(function (p) { return p.status === 'Published'; }).length;
    var nNew = LEADS.filter(function (l) { return l.status === 'New'; }).length;
    return head('Dashboard', 'Signed in as ' + esc(auth.email)) +
      '<div class="tiles"><a class="tile" href="#packages"><b>' + pub + '</b><span>Published packages</span></a><a class="tile" href="#packages"><b>' + (D.packages.length - pub) + '</b><span>Draft packages</span></a>' +
      '<a class="tile" href="#destinations"><b>' + D.destinations.length + '</b><span>Destinations</span></a><a class="tile" href="#gallery"><b>' + D.gallery.length + '</b><span>Photos</span></a>' +
      '<a class="tile" href="#enquiries"><b>' + nNew + '</b><span>New enquiries</span></a></div>' +
      '<div class="panel"><h2>Latest enquiries</h2>' + leadTable(LEADS.slice(0, 5), false) + '</div>' +
      '<div class="panel"><h2>How publishing works</h2><p class="muted small" style="margin:0">Saving a change stores it safely. The public website changes only when you press <b>Publish website</b> at the top. Publishing rebuilds every page (with SEO tags) in a few seconds.</p></div>';
  };

  /* --- packages --- */
  V.packages = function (id) {
    if (id) return packForm(id);
    var rows = D.packages.map(function (p) {
      return '<tr><td>' + (p.hero && D.images[p.hero] ? '<img class="thumb" src="' + esc(img(p.hero, 480)) + '" alt="">' : '<div class="thumb"></div>') + '</td>' +
        '<td><b>' + esc(p.name) + '</b><div class="muted small">' + esc(p.route || '') + '</div></td><td>' + esc(p.len || '') + '</td>' +
        '<td>' + (p.price ? '₹' + Number(p.price).toLocaleString('en-IN') : '<span class="muted">On request</span>') + '</td><td>' + pill(p.status) + '</td>' +
        '<td><div class="row"><a class="btn sm" href="#packages/' + encodeURIComponent(p.slug) + '">Edit</a><button class="btn sm" data-act="togglePack" data-id="' + esc(p.slug) + '">' + (p.status === 'Published' ? 'Unpublish' : 'Publish') + '</button>' +
        (p.status === 'Published' ? '<a class="btn sm" target="_blank" rel="noopener" href="' + esc(siteUrl('packages/' + p.slug + '.html')) + '">View</a>' : '') + '</div></td></tr>';
    }).join('');
    return head('Packages', 'Shown on the Packages page, the homepage and destination pages.', '<a class="btn primary" href="#packages/new">Add a package</a>') +
      '<div class="panel"><div class="scroll"><table><thead><tr><th>Photo</th><th>Package</th><th>Length</th><th>Price from</th><th>Status</th><th>Actions</th></tr></thead><tbody>' + (rows || '<tr><td colspan="6" class="empty">No packages yet.</td></tr>') + '</tbody></table></div></div>';
  };
  function newPack() { return {id: '', slug: '', status: 'Draft', name: '', place: '', t: ['', ''], len: '', ndays: '', from: '', via: '', audience: 'College groups', tags: ['train'], route: '', sum: '', facts: [], days: [''],
    inc: ['Rooms on 4-bed share basis', 'Toll, parking and taxes', 'Three unlimited meals a day (chicken is limited)', 'All entry tickets', 'Drinking water'], price: null, hero: null, inHero: false, title: '', desc: ''}; }
  function photoPicker(field, current) {
    return '<div class="picker" data-field="' + field + '"><button type="button" class="none" data-pick="" aria-pressed="' + (!current) + '">No photo</button>' +
      D.gallery.map(function (g) { return '<button type="button" data-pick="' + esc(g.key) + '" aria-pressed="' + (g.key === current) + '" title="' + esc(g.cap) + '"><img src="' + esc(img(g.key, 480)) + '" alt="' + esc(g.cap) + '" loading="lazy"></button>'; }).join('') + '</div>';
  }
  function counter(id, v, max) { return '<span class="counter' + ((v || '').length > max ? ' over' : '') + '" data-count="' + id + '" data-max="' + max + '">' + (v || '').length + '/' + max + '</span>'; }
  function packForm(id) {
    if (!draft || edit !== 'pack:' + id) { edit = 'pack:' + id; var src = D.packages.filter(function (p) { return p.slug === id; })[0]; draft = id === 'new' ? newPack() : (src ? clone(src) : null); }
    if (!draft) return head('Package not found') + '<a class="btn" href="#packages">Back to packages</a>';
    var p = draft, isNew = id === 'new';
    return head(isNew ? 'Add a package' : 'Edit package', isNew ? '' : esc(p.name), '<a class="btn" href="#packages">Back</a>') +
      '<form class="form" id="packForm" novalidate>' +
      '<div class="panel form"><h2>Basics</h2>' +
      '<div class="grid2"><label class="f">Package name<input id="pName" value="' + esc(p.name) + '" required placeholder="e.g. Dandeli + Goa by Train"></label>' +
      '<label class="f">Web address <small>tripcampus…/packages/<b id="pSlugShow">' + esc(p.slug || 'auto') + '</b>.html</small><input id="pSlug" value="' + esc(p.slug) + '" placeholder="created from the name" ' + (!isNew && D.meta && D.meta.pages && D.meta.pages.indexOf('packages/' + p.slug + '.html') > -1 ? 'title="Changing this changes the page address on Google"' : '') + '></label></div>' +
      '<div class="grid3"><label class="f">Status<select id="pStatus"><option' + (p.status === 'Published' ? ' selected' : '') + '>Published</option><option' + (p.status !== 'Published' ? ' selected' : '') + '>Draft</option></select></label>' +
      '<label class="f">Length (shown)<input id="pLen" value="' + esc(p.len) + '" placeholder="e.g. 5 days"></label>' +
      '<label class="f">Number of days<input id="pNdays" type="number" min="1" max="30" value="' + esc(p.ndays) + '"></label></div>' +
      '<div class="grid3"><label class="f">Region (small text)<input id="pPlace" value="' + esc(p.place) + '" placeholder="e.g. Karnataka · Goa"></label>' +
      '<label class="f">Starts from<input id="pFrom" value="' + esc(p.from) + '" placeholder="e.g. Thrissur"></label>' +
      '<label class="f">How the trip starts<input id="pVia" value="' + esc(p.via) + '" placeholder="e.g. by train from Thrissur"></label></div>' +
      '<div class="grid3"><label class="f">Who it is for<select id="pAud"><option' + (p.audience === 'College groups' ? ' selected' : '') + '>College groups</option><option' + (p.audience === 'Families and groups' ? ' selected' : '') + '>Families and groups</option></select></label>' +
      '<label class="f">Price from (₹ per person) <small>leave empty for "On request"</small><input id="pPrice" inputmode="numeric" value="' + esc(p.price || '') + '" placeholder="e.g. 8500"></label>' +
      '<div class="f"><span class="small muted" style="font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:12px">Travel</span><label class="check"><input type="checkbox" id="pTrain"' + (p.tags.indexOf('train') > -1 ? ' checked' : '') + '>By train</label><label class="check"><input type="checkbox" id="pBus"' + (p.tags.indexOf('bus') > -1 ? ' checked' : '') + '>By bus</label></div></div>' +
      '<label class="f">Short summary<textarea id="pSum" placeholder="One or two sentences shown on cards">' + esc(p.sum) + '</textarea></label>' +
      '<label class="f">Route <small>places separated by ·</small><input id="pRoute" value="' + esc(p.route) + '"></label>' +
      '<label class="f">Highlights <small>one per line, shown as tags</small><textarea id="pFacts">' + esc((p.facts || []).join('\n')) + '</textarea></label></div>' +
      '<div class="panel form"><h2>Day-by-day plan</h2><div id="days">' + p.days.map(function (d, i) {
        return '<div class="day"><b>Day ' + (i + 1) + '</b><textarea id="pDay' + i + '" aria-label="Day ' + (i + 1) + '">' + esc(d) + '</textarea><div class="row">' +
          (i > 0 ? '<button type="button" class="btn sm" data-act="dayUp" data-i="' + i + '" aria-label="Move day up">↑</button>' : '') +
          '<button type="button" class="btn sm danger" data-act="dayRm" data-i="' + i + '">Remove</button></div></div>';
      }).join('') + '</div><div><button type="button" class="btn" data-act="dayAdd">Add a day</button></div></div>' +
      '<div class="panel form"><h2>What is included</h2><label class="f">Included <small>one per line</small><textarea id="pInc" style="min-height:150px">' + esc((p.inc || []).join('\n')) + '</textarea></label></div>' +
      '<div class="panel form"><h2>Photo</h2><p class="muted small" style="margin:0">Pick a real trip photo from the gallery. Without a photo, the site shows a branded panel.</p>' + photoPicker('hero', p.hero) +
      '<label class="check"><input type="checkbox" id="pInHero"' + (p.inHero ? ' checked' : '') + '>Show in the homepage slider (needs a photo)</label>' +
      '<div class="grid2"><label class="f">Slider title line 1<input id="pT1" value="' + esc((p.t || [])[0] || '') + '" placeholder="e.g. Dandeli"></label><label class="f">Slider title line 2<input id="pT2" value="' + esc((p.t || [])[1] || '') + '" placeholder="e.g. & Goa"></label></div></div>' +
      '<div class="panel form"><h2>Google search listing</h2>' +
      '<label class="f">Page title ' + counter('pTitle', p.title, 60) + '<input id="pTitle" value="' + esc(p.title) + '" placeholder="e.g. Dandeli & Goa Tour by Train from Kerala – 5 Days"></label>' +
      '<label class="f">Description ' + counter('pDesc', p.desc, 158) + '<textarea id="pDesc">' + esc(p.desc) + '</textarea></label>' +
      '<div class="serp" aria-label="Preview"><div class="u">' + esc(siteUrl('packages/' + (p.slug || 'new-package') + '.html')) + '</div><div class="t" id="serpT">' + esc(p.title || p.name || 'Page title') + '</div><div class="d" id="serpD">' + esc(p.desc || p.sum || 'Description') + '</div></div></div>' +
      '<p class="err" id="pErr" hidden></p>' +
      '<div class="actions"><div class="row"><button class="btn green" type="submit">Save package</button><a class="btn" href="#packages">Cancel</a></div>' +
      (isNew ? '' : '<button type="button" class="btn danger" data-act="delPack">Delete package</button>') + '</div></form>';
  }
  function syncPack() {
    var p = draft, v = function (id) { return $(id) ? $(id).value.trim() : ''; };
    p.name = v('pName'); p.slug = slugify(v('pSlug') || p.name); p.status = v('pStatus'); p.len = v('pLen'); p.ndays = parseInt(v('pNdays'), 10) || ''; p.place = v('pPlace');
    p.from = v('pFrom'); p.via = v('pVia'); p.audience = v('pAud'); p.price = v('pPrice').replace(/\D/g, '') ? parseInt(v('pPrice').replace(/\D/g, ''), 10) : null;
    p.tags = []; if ($('pTrain').checked) p.tags.push('train'); if ($('pBus').checked) p.tags.push('bus'); if (!p.tags.length) p.tags.push('bus');
    p.sum = v('pSum'); p.route = v('pRoute'); p.facts = lines(v('pFacts')); p.inc = lines($('pInc').value);
    p.days = p.days.map(function (_, i) { return $('pDay' + i) ? $('pDay' + i).value.trim() : ''; });
    p.inHero = $('pInHero').checked; p.t = [v('pT1') || p.name, v('pT2')]; p.title = v('pTitle'); p.desc = v('pDesc');
  }
  function savePack() {
    syncPack(); var p = draft, err = $('pErr'), isNew = edit === 'pack:new', oldSlug = isNew ? null : edit.slice(5);
    var problem = !p.name ? 'Enter a package name.' : !p.slug ? 'Enter a web address.' :
      D.packages.some(function (x) { return x.slug === p.slug && x.slug !== oldSlug; }) ? 'Another package already uses the web address "' + p.slug + '".' :
      (p.status === 'Published' && !p.days.filter(Boolean).length) ? 'Add at least one day to the plan before publishing.' :
      (p.inHero && !p.hero) ? 'Pick a photo to show this package in the homepage slider.' : '';
    if (problem) { err.textContent = problem; err.hidden = false; err.scrollIntoView({block: 'center'}); return; }
    p.days = p.days.filter(Boolean); p.id = p.slug; if (!p.ndays) p.ndays = p.days.length; if (!p.len) p.len = p.days.length + ' days';
    if (isNew) D.packages.push(p);
    else {
      var i = D.packages.findIndex(function (x) { return x.slug === oldSlug; }); D.packages[i] = p;
      if (oldSlug !== p.slug) D.destinations.forEach(function (d) { d.packs = (d.packs || []).map(function (s) { return s === oldSlug ? p.slug : s; }); });
    }
    edit = draft = null;
    save('Package saved. Press Publish website when ready.').then(function (ok) { if (ok) location.hash = '#packages'; });
  }

  /* --- destinations --- */
  V.destinations = function (id) {
    if (id) return destForm(id);
    var rows = D.destinations.map(function (d) {
      var used = (d.packs || []).filter(function (s) { return D.packages.some(function (p) { return p.slug === s && p.status === 'Published'; }); }).length;
      return '<tr><td>' + (d.img && D.images[d.img] ? '<img class="thumb" src="' + esc(img(d.img, 480)) + '" alt="">' : '<div class="thumb"></div>') + '</td><td><b>' + esc(d.name) + '</b><div class="muted small">' + esc(d.hook) + '</div></td>' +
        '<td>' + esc(d.state) + '</td><td>' + used + (used ? '' : ' <span class="pill warn">hidden</span>') + '</td><td>' + pill(d.status || 'Published') + '</td><td><a class="btn sm" href="#destinations/' + encodeURIComponent(d.id) + '">Edit</a></td></tr>';
    }).join('');
    return head('Destinations', 'A destination page is shown only when at least one published package includes it.', '<a class="btn primary" href="#destinations/new">Add a destination</a>') +
      '<div class="panel"><div class="scroll"><table><thead><tr><th>Photo</th><th>Destination</th><th>State</th><th>Packages</th><th>Status</th><th></th></tr></thead><tbody>' + rows + '</tbody></table></div></div>';
  };
  function destForm(id) {
    if (!draft || edit !== 'dest:' + id) { edit = 'dest:' + id; var src = D.destinations.filter(function (d) { return d.id === id; })[0];
      draft = id === 'new' ? {id: '', status: 'Published', name: '', hook: '', state: '', type: 'Hill station', img: null, packs: [], when: '', about: '', intro: '', todo: [], tips: []} : (src ? clone(src) : null); }
    if (!draft) return head('Destination not found') + '<a class="btn" href="#destinations">Back</a>';
    var d = draft, isNew = id === 'new', types = ['Beach', 'Hill station', 'Forest & adventure', 'Heritage', 'City'];
    if (types.indexOf(d.type) < 0) types.push(d.type);
    return head(isNew ? 'Add a destination' : 'Edit destination', esc(d.name), '<a class="btn" href="#destinations">Back</a>') +
      '<form class="form" id="destForm" novalidate><div class="panel form"><h2>Basics</h2>' +
      '<div class="grid3"><label class="f">Name<input id="dName" value="' + esc(d.name) + '"></label><label class="f">Web address<input id="dId" value="' + esc(d.id) + '" placeholder="created from the name"' + (isNew ? '' : ' readonly') + '></label>' +
      '<label class="f">Status<select id="dStatus"><option' + (d.status !== 'Draft' ? ' selected' : '') + '>Published</option><option' + (d.status === 'Draft' ? ' selected' : '') + '>Draft</option></select></label></div>' +
      '<div class="grid3"><label class="f">Tagline<input id="dHook" value="' + esc(d.hook) + '" placeholder="e.g. The Party Capital"></label><label class="f">State<input id="dState" value="' + esc(d.state) + '"></label>' +
      '<label class="f">Type<select id="dType">' + types.map(function (t) { return '<option' + (t === d.type ? ' selected' : '') + '>' + esc(t) + '</option>'; }).join('') + '</select></label></div>' +
      '<label class="f">Best time to visit<input id="dWhen" value="' + esc(d.when) + '"></label>' +
      '<label class="f">About<textarea id="dAbout">' + esc(d.about) + '</textarea></label><label class="f">With Trip Campus <small>how a group experiences it</small><textarea id="dIntro">' + esc(d.intro) + '</textarea></label>' +
      '<div class="grid2"><label class="f">Things to do <small>one per line</small><textarea id="dTodo" style="min-height:140px">' + esc((d.todo || []).join('\n')) + '</textarea></label>' +
      '<label class="f">Tips for college groups <small>one per line</small><textarea id="dTips" style="min-height:140px">' + esc((d.tips || []).join('\n')) + '</textarea></label></div></div>' +
      '<div class="panel form"><h2>Packages that include it</h2><div class="checks">' + D.packages.map(function (p) {
        return '<label class="check"><input type="checkbox" class="dPack" value="' + esc(p.slug) + '"' + ((d.packs || []).indexOf(p.slug) > -1 ? ' checked' : '') + '>' + esc(p.name) + (p.status !== 'Published' ? ' <span class="pill off">Draft</span>' : '') + '</label>';
      }).join('') + '</div></div>' +
      '<div class="panel form"><h2>Photo</h2>' + photoPicker('img', d.img) + '</div><p class="err" id="dErr" hidden></p>' +
      '<div class="actions"><div class="row"><button class="btn green" type="submit">Save destination</button><a class="btn" href="#destinations">Cancel</a></div>' + (isNew ? '' : '<button type="button" class="btn danger" data-act="delDest">Delete destination</button>') + '</div></form>';
  }
  function saveDest() {
    var d = draft, v = function (id) { return $(id).value.trim(); }, isNew = edit === 'dest:new', err = $('dErr');
    d.name = v('dName'); if (isNew) d.id = slugify(v('dId') || d.name); d.status = v('dStatus'); d.hook = v('dHook'); d.state = v('dState'); d.type = v('dType'); d.when = v('dWhen');
    d.about = v('dAbout'); d.intro = v('dIntro'); d.todo = lines($('dTodo').value); d.tips = lines($('dTips').value);
    d.packs = Array.prototype.map.call(document.querySelectorAll('.dPack:checked'), function (x) { return x.value; });
    var problem = !d.name ? 'Enter a name.' : (isNew && D.destinations.some(function (x) { return x.id === d.id; })) ? 'A destination with this web address already exists.' : '';
    if (problem) { err.textContent = problem; err.hidden = false; return; }
    if (isNew) D.destinations.push(d); else D.destinations[D.destinations.findIndex(function (x) { return x.id === d.id; })] = d;
    edit = draft = null;
    save('Destination saved. Press Publish website when ready.').then(function (ok) { if (ok) location.hash = '#destinations'; });
  }

  /* --- gallery --- */
  V.gallery = function () {
    var opts = function (cur) { return '<option value="">Group photo (no destination)</option>' + D.destinations.map(function (d) { return '<option value="' + esc(d.id) + '"' + (d.id === cur ? ' selected' : '') + '>' + esc(d.name) + '</option>'; }).join(''); };
    return head('Gallery', 'Real trip photos. Tag a photo with its destination to show it on that destination page too.') +
      '<div class="panel form"><h2>Upload photos</h2><div class="drop"><input type="file" id="gFiles" accept="image/jpeg,image/png,image/webp" multiple><p class="muted small">JPG or PNG from a phone or camera. Photos are resized automatically.</p></div>' +
      '<div class="grid2"><label class="f">Caption <small>college, department or trip — used for Google image search</small><input id="gCap" placeholder="e.g. MES College BCA, Dandeli, Jan 2027"></label><label class="f">Destination<select id="gDest">' + opts('') + '</select></label></div>' +
      '<div class="progress" id="gProg" hidden><i></i></div><p class="small muted" id="gStatus"></p><div><button class="btn primary" data-act="upload">Upload</button></div></div>' +
      '<div class="panel"><h2>' + D.gallery.length + ' photos</h2><div class="gal">' + D.gallery.map(function (g, i) {
        return '<figure><img src="' + esc(img(g.key, 480)) + '" alt="' + esc(g.cap) + '" loading="lazy"><figcaption><input data-gcap="' + i + '" value="' + esc(g.cap) + '" aria-label="Caption"><select data-gdest="' + i + '" aria-label="Destination">' + opts(g.dest) + '</select>' +
          '<div class="row"><button class="btn sm" data-act="gUp" data-i="' + i + '"' + (i ? '' : ' disabled') + '>Move up</button><button class="btn sm danger" data-act="gDel" data-i="' + i + '">Delete</button></div></figcaption></figure>';
      }).join('') + '</div></div>';
  };
  function canvasBlob(c, type, q) { return new Promise(function (res) { c.toBlob(res, type, q); }); }
  function processImage(file) {
    var load = window.createImageBitmap ? createImageBitmap(file, {imageOrientation: 'from-image'}).catch(function () { return createImageBitmap(file); }) :
      new Promise(function (res, rej) { var im = new Image(); im.onload = function () { res(im); }; im.onerror = rej; im.src = URL.createObjectURL(file); });
    return load.then(function (bmp) {
      var W = bmp.width, H = bmp.height, out = [], ws = [480, 960, 1400].filter(function (w) { return w <= W; });
      if (!ws.length) ws = [W];
      var jobs = ws.map(function (w) {
        var c = document.createElement('canvas'); c.width = w; c.height = Math.round(H * w / W); c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
        return canvasBlob(c, 'image/webp', 0.74).then(function (b) {
          if (!b || b.type !== 'image/webp') throw new Error('This browser cannot create WebP images. Please upload from Chrome or Edge.');
          out.push({w: w, ext: 'webp', blob: b});
          if (w === ws[Math.min(1, ws.length - 1)]) return canvasBlob(c, 'image/jpeg', 0.8).then(function (j) { out.push({w: w, ext: 'jpg', blob: j}); });
        });
      });
      // social sharing image 1200x630, centre crop
      var og = document.createElement('canvas'); og.width = 1200; og.height = 630;
      var s = Math.max(1200 / W, 630 / H), dw = W * s, dh = H * s; og.getContext('2d').drawImage(bmp, (1200 - dw) / 2, (630 - dh) * 0.55, dw, dh);
      jobs.push(canvasBlob(og, 'image/jpeg', 0.8).then(function (b) { out.push({og: true, blob: b}); }));
      return Promise.all(jobs).then(function () { return {W: W, H: H, ws: ws, fb: ws[Math.min(1, ws.length - 1)], files: out}; });
    });
  }
  function upload() {
    var files = Array.prototype.slice.call($('gFiles').files || []), cap = $('gCap').value.trim(), dest = $('gDest').value || null;
    if (!files.length) { toast('Choose one or more photos first.', true); return; }
    if (busy) return; busy = true;
    var prog = $('gProg'), bar = prog.querySelector('i'), status = $('gStatus'), done = 0; prog.hidden = false;
    var added = [];
    var chain = Promise.resolve();
    files.forEach(function (f, n) {
      chain = chain.then(function () {
        status.textContent = 'Processing photo ' + (n + 1) + ' of ' + files.length + '…';
        return processImage(f).then(function (r) {
          var slug = 'trip-' + (slugify(cap) || 'photo').slice(0, 40) + '-' + Date.now().toString(36) + n;
          var names = r.files.map(function (x) { return x.og ? 'og/' + slug + '.jpg' : 'img/' + slug + '-' + x.w + '.' + x.ext; });
          return Promise.all(names.map(function (nm, k) {
            return fetch(API + '/admin/upload?name=' + encodeURIComponent(nm), {method: 'PUT', credentials: 'same-origin', headers: {'Content-Type': nm.slice(-4) === 'webp' ? 'image/webp' : 'image/jpeg', 'X-TC': '1'}, body: r.files[k].blob})
              .then(function (res) { if (res.status === 401) { signOut('Your session ended. Please sign in again.'); throw new Error('Signed out'); } if (!res.ok) throw new Error('Upload failed (' + res.status + ')'); });
          })).then(function () {
            D.images[slug] = {slug: slug, w: r.W, h: r.H, ws: r.ws, fb: r.fb};
            added.push({key: slug, cap: cap || 'A Trip Campus group on tour', dest: dest});
            done++; bar.style.width = (done / files.length * 100) + '%';
          });
        });
      });
    });
    chain.then(function () {
      D.gallery = added.concat(D.gallery); busy = false;
      return save(added.length + ' photo' + (added.length > 1 ? 's' : '') + ' uploaded. Publish to show them on the website.');
    }).catch(function (e) { busy = false; status.textContent = ''; toast(e.message, true); if (added.length) { D.gallery = added.concat(D.gallery); save(); } else render(); });
  }

  /* --- enquiries --- */
  var LEAD_ST = ['New', 'Contacted', 'Quoted', 'Booked', 'Lost'];
  function waLink(phone) { var d = String(phone || '').replace(/\D/g, ''); if (d.length === 10) d = '91' + d; return 'https://wa.me/' + d; }
  function leadTable(list, full) {
    if (!list.length) return '<div class="empty">No enquiries yet. They appear here when someone sends the quote form on the website.</div>';
    return '<div class="scroll"><table><thead><tr><th>Date</th><th>Name</th><th>Phone</th><th>Interested in</th>' + (full ? '<th>Group</th><th>Month</th><th>Note</th>' : '') + '<th>Status</th>' + (full ? '<th></th>' : '') + '</tr></thead><tbody>' +
      list.map(function (l) {
        return '<tr><td class="small">' + esc(fmtDate(l.createdAt)) + '</td><td><b>' + esc(l.name) + '</b>' + (full && l.source ? '<div class="muted small">' + esc(l.source) + '</div>' : '') + '</td>' +
          '<td><a href="tel:' + esc(l.phone) + '">' + esc(l.phone) + '</a><div><a class="small" target="_blank" rel="noopener" href="' + esc(waLink(l.phone)) + '">WhatsApp</a></div></td><td>' + esc(l.package || '—') + '</td>' +
          (full ? '<td>' + esc(l.size || '—') + '</td><td>' + esc(l.month || '—') + '</td><td class="small" style="max-width:260px">' + esc(l.note || '') + '</td>' : '') +
          '<td>' + (full ? '<select data-lead="' + esc(l.id) + '" aria-label="Status">' + LEAD_ST.map(function (s) { return '<option' + (s === l.status ? ' selected' : '') + '>' + s + '</option>'; }).join('') + '</select>' : pill(l.status)) + '</td>' +
          (full ? '<td><button class="btn sm danger" data-act="leadDel" data-id="' + esc(l.id) + '">Delete</button></td>' : '') + '</tr>';
      }).join('') + '</tbody></table></div>';
  }
  var leadFilter = '';
  V.enquiries = function () {
    var list = LEADS.filter(function (l) { return !leadFilter || l.status === leadFilter; });
    return head('Enquiries', 'Sent from the quote forms on the website. Each one is also emailed to the office.',
      '<select id="leadFilter" aria-label="Filter"><option value="">All statuses</option>' + LEAD_ST.map(function (s) { return '<option' + (s === leadFilter ? ' selected' : '') + '>' + s + '</option>'; }).join('') + '</select>' +
      '<button class="btn" data-act="leadRefresh">Refresh</button><button class="btn" data-act="leadCsv">Download CSV</button>') +
      '<div class="panel">' + leadTable(list, true) + '</div>';
  };

  /* --- settings --- */
  V.settings = function () {
    var s = D.settings, a = s.address || {};
    return head('Settings', 'Contact details and tracking used across the website.') +
      '<form class="form" id="setForm" novalidate><div class="panel form"><h2>Website</h2>' +
      '<label class="f">Website address <small>used in Google and sharing links, e.g. https://www.tripcampustourism.com</small><input id="sSite" value="' + esc(s.site) + '"></label>' +
      '<div class="grid2"><label class="f">Google Analytics 4 ID <small>G-XXXXXXX</small><input id="sGa4" value="' + esc(s.ga4 || '') + '"></label><label class="f">Meta Pixel ID<input id="sPixel" value="' + esc(s.metaPixel || '') + '"></label></div></div>' +
      '<div class="panel form"><h2>Contact</h2><div class="grid2"><label class="f">WhatsApp number <small>with country code, e.g. 918943299434</small><input id="sWa" value="' + esc(s.whatsapp) + '"></label>' +
      '<label class="f">Email<input id="sEmail" type="email" value="' + esc(s.email) + '"></label></div>' +
      '<label class="f">Phone numbers <small>one per line, e.g. +91 89432 99434</small><textarea id="sPhones">' + esc((s.phones || []).map(function (p) { return p.label; }).join('\n')) + '</textarea></label>' +
      '<div class="grid2"><label class="f">Street<input id="sStreet" value="' + esc(a.street) + '"></label><label class="f">Town<input id="sTown" value="' + esc(a.locality) + '"></label></div>' +
      '<div class="grid3"><label class="f">PIN code<input id="sPin" value="' + esc(a.postal) + '"></label><label class="f">State<input id="sState" value="' + esc(a.region) + '"></label><label class="f">Instagram link<input id="sIg" value="' + esc(s.instagram) + '"></label></div>' +
      '<label class="f">Google Maps link<input id="sMaps" value="' + esc(s.maps) + '"></label></div>' +
      '<div class="panel form"><h2>Homepage</h2><p class="muted small" style="margin:0">Main photo for the first slide.</p>' + photoPicker('homeHero', D.home.heroKey) +
      '<label class="f">Colleges that travelled with us <small>one per line</small><textarea id="sColleges" style="min-height:150px">' + esc((D.home.colleges || []).join('\n')) + '</textarea></label></div>' +
      '<div class="actions"><button class="btn green" type="submit">Save settings</button></div></form>' +
      '<div class="panel form"><h2>Change your password</h2><div class="grid2"><label class="f">Current password<input id="cpOld" type="password" autocomplete="current-password"></label><label class="f">New password<input id="cpNew" type="password" autocomplete="new-password"></label></div><div><button class="btn" data-act="changePw">Change password</button></div></div>';
  };
  function saveSettings() {
    var v = function (id) { return $(id).value.trim(); }, s = D.settings;
    var site = v('sSite').replace(/\/$/, '');
    if (!/^https?:\/\/[^ ]+[.:][^ ]+/.test(site)) { toast('Enter the full website address, for example https://www.tripcampustourism.com', true); return; }
    var wa = v('sWa').replace(/\D/g, ''); if (wa.length === 10) wa = '91' + wa;
    if (wa.length < 11) { toast('Enter the WhatsApp number with country code.', true); return; }
    s.site = site; s.ga4 = v('sGa4'); s.metaPixel = v('sPixel'); s.whatsapp = wa; s.email = v('sEmail'); s.instagram = v('sIg'); s.maps = v('sMaps');
    s.phones = lines($('sPhones').value).map(function (l) { var d = l.replace(/[^\d+]/g, ''); if (d.indexOf('+') !== 0) d = '+' + (d.length === 10 ? '91' + d : d); return {tel: d, label: l}; });
    s.address = {street: v('sStreet'), locality: v('sTown'), region: v('sState'), postal: v('sPin'), country: (s.address && s.address.country) || 'IN'};
    D.home.colleges = lines($('sColleges').value);
    save('Settings saved. Press Publish website when ready.');
  }

  /* ------------------------------------------------------------------ render + events */
  function render() {
    var app = $('app');
    if (!auth) { app.innerHTML = loginView(); var f = document.querySelector('#loginForm input'); if (f) f.focus(); return; }
    if (!D) { app.innerHTML = '<div class="boot">Loading content…</div>'; return; }
    var r = route();
    if (edit && !(r.id && edit === (r.tab === 'packages' ? 'pack:' : 'dest:') + r.id)) { edit = draft = null; }
    var y = window.scrollY;
    app.innerHTML = shell(V[r.tab](r.id));
    if (r.id) window.scrollTo(0, y);
  }
  function arm(b, label) { if (b.dataset.armed) return true; b.dataset.armed = '1'; b.classList.add('armed'); var old = b.textContent; b.textContent = label || 'Click again to confirm';
    setTimeout(function () { if (b.isConnected) { delete b.dataset.armed; b.classList.remove('armed'); b.textContent = old; } }, 4000); return false; }

  var ACT = {
    publish: function (b) { publish(b); },
    signOut: function () { signOut(); },
    toForgot: function () { loginStep = 'forgot'; render(); },
    toLogin: function () { loginStep = 'login'; render(); },
    togglePack: function (b) { var p = D.packages.filter(function (x) { return x.slug === b.dataset.id; })[0]; if (!p) return;
      if (p.status !== 'Published' && !(p.days || []).filter(Boolean).length) { toast('Add the day-by-day plan before publishing this package.', true); return; }
      p.status = p.status === 'Published' ? 'Draft' : 'Published'; save(p.status === 'Published' ? 'Package set to Published' : 'Package moved to drafts'); },
    dayAdd: function () { syncPack(); draft.days.push(''); render(); var t = $('pDay' + (draft.days.length - 1)); if (t) t.focus(); },
    dayRm: function (b) { syncPack(); draft.days.splice(+b.dataset.i, 1); if (!draft.days.length) draft.days.push(''); render(); },
    dayUp: function (b) { syncPack(); var i = +b.dataset.i, d = draft.days; d.splice(i - 1, 0, d.splice(i, 1)[0]); render(); },
    delPack: function (b) { if (!arm(b, 'Click again to delete')) return; var slug = edit.slice(5);
      D.packages = D.packages.filter(function (p) { return p.slug !== slug; }); D.destinations.forEach(function (d) { d.packs = (d.packs || []).filter(function (s) { return s !== slug; }); });
      edit = draft = null; save('Package deleted. Publish to remove it from the website.').then(function () { location.hash = '#packages'; }); },
    delDest: function (b) { if (!arm(b, 'Click again to delete')) return; var id = edit.slice(5);
      D.destinations = D.destinations.filter(function (d) { return d.id !== id; }); D.gallery.forEach(function (g) { if (g.dest === id) g.dest = null; });
      edit = draft = null; save('Destination deleted.').then(function () { location.hash = '#destinations'; }); },
    upload: function () { upload(); },
    gUp: function (b) { var i = +b.dataset.i, g = D.gallery; g.splice(i - 1, 0, g.splice(i, 1)[0]); save('Order saved'); },
    gDel: function (b) { if (!arm(b, 'Delete?')) return; var g = D.gallery.splice(+b.dataset.i, 1)[0];
      D.packages.forEach(function (p) { if (p.hero === g.key) { p.hero = null; p.inHero = false; } }); D.destinations.forEach(function (d) { if (d.img === g.key) d.img = null; });
      if (D.home.heroKey === g.key) D.home.heroKey = D.gallery[0] ? D.gallery[0].key : null;
      save('Photo removed. Publish to update the website.'); },
    leadRefresh: function () { api('GET', '/admin/leads').then(function (r) { LEADS = r.leads; render(); toast('Enquiries refreshed'); }).catch(function (e) { toast(e.message, true); }); },
    leadDel: function (b) { if (!arm(b, 'Delete?')) return; api('DELETE', '/admin/leads/' + encodeURIComponent(b.dataset.id)).then(function () { LEADS = LEADS.filter(function (l) { return l.id !== b.dataset.id; }); render(); toast('Enquiry deleted'); }).catch(function (e) { toast(e.message, true); }); },
    leadCsv: function () {
      var cols = ['createdAt', 'name', 'phone', 'package', 'size', 'month', 'note', 'status', 'page', 'source'];
      var csv = [cols.join(',')].concat(LEADS.map(function (l) { return cols.map(function (c) { return '"' + String(l[c] || '').replace(/"/g, '""') + '"'; }).join(','); })).join('\r\n');
      var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + csv], {type: 'text/csv'})); a.download = 'trip-campus-enquiries.csv'; a.click(); },
    changePw: function () {
      var o = $('cpOld').value, n = $('cpNew').value; if (n.length < 10) { toast('Use at least 10 characters for the new password.', true); return; }
      api('POST', '/auth/password', {current: o, 'new': n}).then(function () { $('cpOld').value = $('cpNew').value = ''; toast('Password changed. Other devices have been signed out.'); }).catch(function (e) { toast(e.message, true); }); }
  };
  document.addEventListener('click', function (e) {
    var pk = e.target.closest('[data-pick]');
    if (pk) { var box = pk.closest('.picker'), field = box.dataset.field, key = pk.dataset.pick || null;
      box.querySelectorAll('[data-pick]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === pk)); });
      if (field === 'homeHero') D.home.heroKey = key; else if (draft) draft[field] = key; return; }
    var b = e.target.closest('[data-act]'); if (!b) return;
    if (b.tagName === 'A') e.preventDefault();
    if (ACT[b.dataset.act]) ACT[b.dataset.act](b);
  });
  document.addEventListener('submit', function (e) {
    e.preventDefault();
    var id = e.target.id;
    if (id === 'loginForm') loginSubmit(); else if (id === 'packForm') savePack(); else if (id === 'destForm') saveDest(); else if (id === 'setForm') saveSettings();
  });
  document.addEventListener('input', function (e) {
    var c = document.querySelector('[data-count="' + e.target.id + '"]');
    if (c) { var n = e.target.value.length, m = +c.dataset.max; c.textContent = n + '/' + m; c.classList.toggle('over', n > m); }
    if (e.target.id === 'pTitle' || e.target.id === 'pName') { var t = $('serpT'); if (t) t.textContent = $('pTitle').value || $('pName').value || 'Page title'; }
    if (e.target.id === 'pDesc' || e.target.id === 'pSum') { var d = $('serpD'); if (d) d.textContent = $('pDesc').value || $('pSum').value || 'Description'; }
    if (e.target.id === 'pName' && edit === 'pack:new' && !$('pSlug').dataset.touched) { $('pSlug').value = slugify(e.target.value); $('pSlugShow').textContent = $('pSlug').value || 'auto'; }
    if (e.target.id === 'pSlug') { e.target.dataset.touched = '1'; $('pSlugShow').textContent = slugify(e.target.value) || 'auto'; }
  });
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.dataset.lead) { var id = t.dataset.lead, st = t.value;
      api('PATCH', '/admin/leads/' + encodeURIComponent(id), {status: st}).then(function () { LEADS.forEach(function (l) { if (l.id === id) l.status = st; }); toast('Status updated'); render(); }).catch(function (er) { toast(er.message, true); }); }
    else if (t.dataset.gcap !== undefined) { D.gallery[+t.dataset.gcap].cap = t.value.trim() || 'A Trip Campus group on tour'; save('Caption saved'); }
    else if (t.dataset.gdest !== undefined) { D.gallery[+t.dataset.gdest].dest = t.value || null; save('Destination tag saved'); }
    else if (t.id === 'leadFilter') { leadFilter = t.value; render(); }
  });
  window.addEventListener('hashchange', function () { render(); window.scrollTo(0, 0); });
  window.addEventListener('beforeunload', function (e) { if (draft) { e.preventDefault(); e.returnValue = ''; } });

  loginStep = 'checking'; render();
  call('GET', '/auth/me').then(function (j) { auth = {email: j.email}; loginStep = 'login'; render(); loadAll(); })
    .catch(function () { loginStep = 'login'; render(); });
})();
