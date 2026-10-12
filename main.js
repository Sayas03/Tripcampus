/* Trip Campus — small, dependency-free site script */
(function(){
  var C = window.TC_CONFIG || {}, WA = C.whatsapp || '918943299434';
  var $ = function(s, r){ return (r||document).querySelector(s) }, $$ = function(s, r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)) };

  /* local preview (opened from disk): clean folder links like packages/ need index.html */
  if(location.protocol === 'file:') $$('a[href]').forEach(function(a){ var h = a.getAttribute('href'); if(!/^[a-z]+:|^#|^\/\//i.test(h) && /(^|\/)(#.*)?$/.test(h)) a.setAttribute('href', h.replace(/(#.*)?$/, function(m){ return 'index.html' + m })) });

  /* ---- campaign attribution (ROAS): keep UTM / click ids for the session ---- */
  var SKEY = 'tc_src';
  try{
    var q = new URLSearchParams(location.search), keep = {};
    ['utm_source','utm_medium','utm_campaign','utm_content','gclid','fbclid'].forEach(function(k){ if(q.get(k)) keep[k] = q.get(k) });
    if(Object.keys(keep).length) sessionStorage.setItem(SKEY, JSON.stringify(keep));
  }catch(e){}
  function source(){
    try{ var s = JSON.parse(sessionStorage.getItem(SKEY) || 'null'); if(!s) return '';
      return [s.utm_source, s.utm_medium, s.utm_campaign].filter(Boolean).join(' / ') || (s.gclid ? 'google ads' : s.fbclid ? 'meta ads' : '');
    }catch(e){ return '' }
  }

  /* ---- analytics: GA4 + Meta Pixel load only when IDs are set in config.js ---- */
  function track(name, params){
    params = params || {};
    window.dataLayer = window.dataLayer || []; window.dataLayer.push(Object.assign({event: name}, params));
    if(window.gtag) window.gtag('event', name, params);
    if(window.fbq){ if(name === 'generate_lead' || name === 'whatsapp_click') window.fbq('track', 'Lead', params); else if(name === 'call_click') window.fbq('track', 'Contact', params) }
  }
  if(C.ga4){
    var g = document.createElement('script'); g.async = true; g.src = 'https://www.googletagmanager.com/gtag/js?id=' + C.ga4; document.head.appendChild(g);
    window.dataLayer = window.dataLayer || []; window.gtag = function(){ dataLayer.push(arguments) }; gtag('js', new Date()); gtag('config', C.ga4);
  }
  if(C.metaPixel){
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', C.metaPixel); fbq('track', 'PageView');
  }

  /* ---- WhatsApp links: add page context + campaign source to the prefilled message ---- */
  function waUrl(text){
    var src = source(); if(src) text += '\n(Source: ' + src + ')';
    return 'https://wa.me/' + WA + '?text=' + encodeURIComponent(text);
  }
  /* ---- "Get a quote" buttons: ask name + phone first, save the enquiry, then open WhatsApp ---- */
  var GATE = {hero: 1, card: 1, 'pack-top': 1, band: 1, dest: 1, 'iv-top': 1, guide: 1};
  var DONE = 'tc_lead';
  function seen(){ try{ return sessionStorage.getItem(DONE) === '1' }catch(e){ return false } }
  function saveLead(d){
    if(!C.api) return;
    var url = C.api.replace(/\/$/, '') + '/enquiry', body = JSON.stringify(d), ok = false;
    try{ ok = !!(navigator.sendBeacon && navigator.sendBeacon(url, new Blob([body], {type: 'application/json'}))) }catch(e){}
    if(!ok){ try{ fetch(url, {method: 'POST', keepalive: true, headers: {'Content-Type': 'application/json'}, body: body}).catch(function(){}) }catch(e){} }
  }
  var qd;
  function quoteDialog(a){
    var msg = a.dataset.wa || 'Hi Trip Campus, I would like a quote.';
    var m = msg.match(/(?:for the|share the) (.+?) (?:package|itinerary)/), pkg = m ? m[1] : '';
    if(!qd){
      qd = document.createElement('dialog'); qd.className = 'qd'; qd.setAttribute('aria-labelledby', 'qdH');
      qd.innerHTML = '<button type="button" class="qd-x" aria-label="Close">×</button><form class="form" novalidate method="dialog">' +
        '<h2 id="qdH">Get your quote</h2><p class="qd-p"></p>' +
        '<label>Your name<input name="name" autocomplete="name" required></label>' +
        '<label>Mobile number<input name="phone" type="tel" inputmode="tel" autocomplete="tel" required></label>' +
        '<label>Group size<input name="size" inputmode="numeric" placeholder="e.g. 45"></label>' +
        '<p class="err" role="alert" hidden></p>' +
        '<button class="btn btn-wa" type="submit">Continue on WhatsApp</button>' +
        '<a class="qd-skip" href="#" data-skip="">Skip, open WhatsApp now</a></form>';
      document.body.appendChild(qd);
      qd.querySelector('.qd-x').onclick = function(){ qd.close() };
      qd.addEventListener('click', function(e){ if(e.target === qd) qd.close() });
    }
    var f = qd.querySelector('form'), err = qd.querySelector('.err');
    qd.querySelector('.qd-p').textContent = (pkg ? pkg + ' – ' : '') + 'Trip Campus will send the itinerary and price on WhatsApp.';
    err.hidden = true;
    function go(text){ qd.close(); window.open(waUrl(text), '_blank', 'noopener'); track('whatsapp_click', {location: a.dataset.loc, page: location.pathname}) }
    f.onsubmit = function(e){
      e.preventDefault();
      var name = f.elements.name.value.trim(), phone = f.elements.phone.value.trim(), size = f.elements.size.value.trim();
      var bad = !name ? 'Please enter your name.' : phone.replace(/\D/g, '').length < 10 ? 'Please enter a mobile number with at least 10 digits.' : '';
      err.hidden = !bad; err.textContent = bad;
      if(bad){ f.elements[!name ? 'name' : 'phone'].focus(); return }
      saveLead({name: name, phone: phone, size: size, package: pkg, note: msg, page: location.pathname, source: source()});
      track('generate_lead', {form: 'quote-popup', package: pkg, page: location.pathname});
      try{ sessionStorage.setItem(DONE, '1') }catch(e){}
      go(msg + '\nName: ' + name + '\nPhone: ' + phone + (size ? '\nGroup size: ' + size : ''));
    };
    qd.querySelector('.qd-skip').onclick = function(e){ e.preventDefault(); go(msg) };
    qd.showModal(); f.elements.name.focus();
  }

  document.addEventListener('click', function(e){
    var a = e.target.closest('a'); if(!a) return;
    if(a.dataset.wa !== undefined && !a.closest('form') && GATE[a.dataset.loc] && !seen() && window.HTMLDialogElement){
      e.preventDefault(); quoteDialog(a); return;
    }
    if(a.dataset.wa !== undefined && !a.closest('form')){
      a.href = waUrl(a.dataset.wa || ('Hi Trip Campus, I found you on your website (' + document.title.split('|')[0].trim() + '). Please share details.'));
      track('whatsapp_click', {location: a.dataset.loc || 'link', page: location.pathname});
    } else if(a.href.indexOf('tel:') === 0){
      track('call_click', {location: a.dataset.loc || 'link', page: location.pathname});
    }
  });

  /* ---- mobile menu ---- */
  var mb = $('#menuBtn'), sh = $('#sheet');
  if(mb) mb.addEventListener('click', function(){
    var o = sh.hidden; sh.hidden = !o; mb.setAttribute('aria-expanded', String(o)); document.body.style.overflow = o ? 'hidden' : '';
  });

  /* ---- hero slider (CSS scroll-snap; JS only for dots, thumbs, arrows) ---- */
  var track_ = $('#slides');
  if(track_){
    var slides = $$('.slide', track_), dots = $$('#dots button'), thumbs = $$('#thumbs button'), cur = 0;
    function go(i){ i = (i + slides.length) % slides.length; track_.scrollTo({left: slides[i].offsetLeft, behavior: 'smooth'}) }
    function mark(i){
      cur = i; start();
      dots.forEach(function(d, k){ d.setAttribute('aria-current', k === i ? 'true' : 'false') });
      $$('.js-count').forEach(function(c){ c.textContent = String(i + 1).padStart(2, '0') });
      var bar = $('#hBar'); if(bar) bar.style.width = ((i + 1) / slides.length * 100) + '%';
      thumbs.forEach(function(t, k){ var off = (k - i + slides.length) % slides.length; t.hidden = off === 0 || off > 4; t.style.order = off });
    }
    var io = new IntersectionObserver(function(es){ es.forEach(function(en){ if(en.isIntersecting && en.intersectionRatio > .6) mark(slides.indexOf(en.target)) }) }, {root: track_, threshold: [.6]});
    slides.forEach(function(s){ io.observe(s) });
    dots.forEach(function(d, k){ d.addEventListener('click', function(){ go(k) }) });
    thumbs.forEach(function(t, k){ t.addEventListener('click', function(){ go(k) }) });
    var p = $('#hPrev'), n = $('#hNext');
    if(p) p.addEventListener('click', function(){ go(cur - 1) });
    if(n) n.addEventListener('click', function(){ go(cur + 1) });
    document.addEventListener('keydown', function(e){
      if(!matchMedia('(min-width:1024px)').matches || /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) return;
      if(e.key === 'ArrowRight') go(cur + 1); if(e.key === 'ArrowLeft') go(cur - 1);
    });
    /* autoplay: next slide every 6s; pauses on hover over text or controls, touch, keyboard focus, hidden tab or when scrolled away */
    var AUTO = 6000, timer = null, hold = false, inView = true, reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var hero = track_.closest('.hero'), ld = document.createElement('i'); ld.className = 'hero-loader'; ld.setAttribute('aria-hidden', 'true'); hero.appendChild(ld);
    function stop(){ clearTimeout(timer); ld.classList.remove('run') }
    function start(){
      stop(); if(reduce || hold || !inView || document.hidden || slides.length < 2) return;
      void ld.offsetWidth; ld.style.animationDuration = AUTO + 'ms'; ld.classList.add('run');
      timer = setTimeout(function(){ go(cur + 1) }, AUTO);
    }
    function pause(){ hold = true; stop() }
    function resume(){ hold = false; start() }
    $$('.slide-body > div, .thumbs, .h-arrows', hero).forEach(function(el){ el.addEventListener('mouseenter', pause); el.addEventListener('mouseleave', resume) });
    hero.addEventListener('focusin', pause); hero.addEventListener('focusout', function(e){ if(!hero.contains(e.relatedTarget)) resume() });
    track_.addEventListener('touchstart', pause, {passive: true});
    track_.addEventListener('touchend', function(){ setTimeout(resume, 1500) }, {passive: true});
    document.addEventListener('visibilitychange', start);
    new IntersectionObserver(function(es){ inView = es[0].isIntersecting; start() }, {threshold: .3}).observe(hero);
    mark(0);
  }

  /* ---- filters (packages and gallery) ---- */
  $$('[data-filter-group]').forEach(function(group){
    var target = $(group.dataset.filterGroup), items = $$('[data-tags]', target), count = $(group.dataset.count || '#none');
    group.addEventListener('click', function(e){
      var b = e.target.closest('.filter'); if(!b) return;
      $$('.filter', group).forEach(function(x){ x.setAttribute('aria-pressed', String(x === b)) });
      var v = b.dataset.v, n = 0;
      items.forEach(function(it){ var show = !v || (' ' + it.dataset.tags + ' ').indexOf(' ' + v + ' ') > -1; it.hidden = !show; if(show) n++ });
      if(count) count.textContent = n + (n === 1 ? ' package' : ' packages');
      track('filter_use', {filter: v || 'all', page: location.pathname});
    });
  });

  /* ---- lightbox ---- */
  var lb = $('#lb');
  if(lb){
    document.addEventListener('click', function(e){
      var b = e.target.closest('[data-full]'); if(!b) return;
      e.preventDefault();
      var img = $('#lbImg'); img.src = b.dataset.full; img.alt = b.dataset.cap || ''; $('#lbCap').textContent = b.dataset.cap || '';
      if(lb.showModal) lb.showModal(); else lb.setAttribute('open', '');
    });
    lb.addEventListener('click', function(e){ if(e.target === lb || e.target.closest('.lb-x')) lb.close() });
  }

  /* ---- enquiry forms -> WhatsApp (lead) ---- */
  $$('form[data-enquiry]').forEach(function(f){
    var err = $('.err', f);
    f.addEventListener('submit', function(e){
      e.preventDefault();
      var v = function(n){ var el = f.elements[n]; return el ? el.value.trim() : '' };
      var name = v('name'), phone = v('phone').replace(/[^\d+]/g, '');
      var msg = !name ? 'Please enter your name.' : phone.replace(/\D/g, '').length < 10 ? 'Please enter a phone number with at least 10 digits.' : '';
      err.hidden = !msg; err.textContent = msg;
      if(msg){ f.elements[!name ? 'name' : 'phone'].focus(); return }
      var L = ['Hi Trip Campus, I would like a quote.'];
      [['Name','name'],['Phone','phone'],['Package','package'],['Group size','size'],['Travel month','month'],['Boarding point','from'],['Note','note']].forEach(function(p){
        var x = v(p[1]); if(x && x !== 'Not sure yet') L.push(p[0] + ': ' + x);
      });
      track('generate_lead', {form: f.dataset.enquiry, package: v('package') || '', page: location.pathname});
      /* save the enquiry in the admin and email the office (AWS API), then open WhatsApp as before */
      if(C.api && !v('website')){
        /* sendBeacon still delivers when the phone switches to the WhatsApp app straight away */
        saveLead({name: name, phone: v('phone'), package: v('package'), size: v('size'), month: v('month'), note: v('note'), page: location.pathname, source: source()});
        try{ sessionStorage.setItem(DONE, '1') }catch(e){}
      }
      window.open(waUrl(L.join('\n')), '_blank', 'noopener');
    });
  });

  var y = $('#year'); if(y) y.textContent = new Date().getFullYear();
})();
