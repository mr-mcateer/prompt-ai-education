/* Stack launch page: scroll sequences + data-driven sections. No libraries. */
(function () {
  'use strict';
  const S = window.STORY || {};
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches && !/[?&]motion/.test(location.search);
  if (/[?&]flat/.test(location.search)) document.documentElement.classList.add('flat'); // review aid: tracks collapse to one screen
  const $ = (q, el = document) => el.querySelector(q);
  const $$ = (q, el = document) => Array.from(el.querySelectorAll(q));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const AX = ['fit', 'air', 'service', 'cable', 'look', 'build'];

  /* ------------------------------------------------------------ scroll sequences */
  class Seq {
    constructor(track) {
      this.track = track;
      this.name = track.dataset.seq;
      this.n = parseInt(track.dataset.frames, 10) || 0;
      track.style.setProperty('--h', track.dataset.height || 400);
      this.canvas = $('canvas.seq', track);
      this.ctx = this.canvas.getContext('2d', { alpha: false });
      this.caps = $$('.cap', track);
      this.bar = $('.progress i', track);
      this.frames = new Array(this.n);
      this.loaded = 0;
      this.cur = -1;
      this.progress = 0;
      this.pending = null;
      this.sized = false;
      if (!this.n || reduced) { track.classList.add('no-seq'); this.caps.forEach((c) => c.classList.add('on')); if (this.caps.length) this.caps.forEach((c, i) => c.classList.toggle('on', i === 0)); return; }
      const dpr = Math.min(devicePixelRatio || 1, 2);
      const big = Math.max(innerWidth, innerHeight) * dpr > 1100;
      this.dir = big ? `seq/${this.name}/` : `seq/${this.name}_900/`;
      this.probeSmall();
      this.resize();
      addEventListener('resize', () => this.resize(), { passive: true });
      this.loadAll();
    }
    probeSmall() {
      // if the _900 set does not exist, fall back to the full set
      if (this.dir.endsWith('_900/')) {
        const im = new Image();
        im.onerror = () => { this.dir = `seq/${this.name}/`; this.frames = new Array(this.n); this.loaded = 0; this.loadAll(); };
        im.src = this.dir + 'f000.webp';
      }
    }
    src(i) { return this.dir + 'f' + String(i).padStart(3, '0') + '.webp'; }
    load(i) {
      if (this.frames[i]) return;
      const im = new Image();
      im.decoding = 'async';
      im.onload = () => { this.loaded++; if (i === this.want || this.cur < 0) this.draw(true); };
      im.src = this.src(i);
      this.frames[i] = im;
    }
    loadAll() {
      // first frame, then every 8th, then every 4th, then the rest: a coarse scrub works early
      const order = [0];
      for (const step of [8, 4, 2, 1]) for (let i = 0; i < this.n; i += step) if (!order.includes(i)) order.push(i);
      let k = 0;
      const pump = () => { for (let j = 0; j < 6 && k < order.length; j++, k++) this.load(order[k]); if (k < order.length) setTimeout(pump, 40); };
      pump();
    }
    resize() {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      const w = this.track.clientWidth, h = $('.sticky', this.track).clientHeight;
      this.canvas.width = Math.round(w * dpr); this.canvas.height = Math.round(h * dpr);
      this.sized = true; this.cur = -1; this.draw(true);
    }
    nearest(i) {
      // nearest loaded frame so the scrub never shows black while frames stream in
      for (let d = 0; d < this.n; d++) {
        const a = this.frames[i - d], b = this.frames[i + d];
        if (a && a.complete && a.naturalWidth) return a;
        if (b && b.complete && b.naturalWidth) return b;
      }
      return null;
    }
    draw(force) {
      const i = clamp(Math.round(this.progress * (this.n - 1)), 0, this.n - 1);
      this.want = i;
      if (!force && i === this.cur) return;
      const im = this.nearest(i);
      if (!im) return;
      const c = this.canvas, ctx = this.ctx;
      ctx.fillStyle = '#0a0a0b'; ctx.fillRect(0, 0, c.width, c.height);
      // contain: the frame is square, the product is centred with margin, edges are page-black
      const s = Math.min(c.width / im.naturalWidth, c.height / im.naturalHeight) * (c.width < c.height ? 1.08 : 1.0);
      const dw = im.naturalWidth * s, dh = im.naturalHeight * s;
      const shift = c.width > 900 * (devicePixelRatio || 1) ? c.width * (parseFloat(this.track.dataset.shift) || 0) : 0; // keep clear of the side captions on wide screens
      ctx.drawImage(im, (c.width - dw) / 2 + shift, (c.height - dh) / 2 - (c.width < c.height ? c.height * 0.04 : 0), dw, dh);
      this.cur = i;
    }
    update() {
      const r = this.track.getBoundingClientRect();
      const total = r.height - innerHeight;
      const p = total > 0 ? clamp(-r.top / total, 0, 1) : 0;
      this.progress = p;
      if (this.bar) this.bar.style.width = (p * 100).toFixed(2) + '%';
      for (const c of this.caps) {
        const a = parseFloat(c.dataset.from), b = parseFloat(c.dataset.to);
        c.classList.toggle('on', p >= a && p < b);
      }
      if (r.bottom > 0 && r.top < innerHeight) this.draw(false);
    }
  }
  const seqs = $$('.track').map((t) => new Seq(t));
  let ticking = false;
  const onScroll = () => { if (ticking) return; ticking = true; requestAnimationFrame(() => { seqs.forEach((s) => s.n && !reduced && s.update()); ticking = false; }); };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ------------------------------------------------------------ reveal on scroll */
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px' });
  const rv = (el) => { el.classList.add('rv'); io.observe(el); };

  /* ------------------------------------------------------------ data sections */
  const P = S.product || {};
  const counts = P.counts || {};
  const mt = P.machine_time || {};
  const sz = P.outside_size_mm || {};

  // stats
  const stats = $('#stats');
  if (stats) {
    const rows = [
      [counts.bends ?? 0, 'bends'], [counts.welds ?? 0, 'welds'],
      [counts.plasma_parts, 'plasma-cut steel plates'], [counts.laser_parts, 'laser-cut birch parts'],
      [counts.printed_parts, `printed parts: 20 brackets, ${counts.caps ? counts.caps + ' caps, ' : ''}3 cradles, 2 stops`], [counts.m4_bolts, 'M4 bolts, one hex key'],
      [sz.w ? `${Math.round(sz.w)} x ${sz.d} x ${sz.h}` : null, 'mm outside, router not counted'],
      [counts.magnets, 'magnets, in 8 pairs, hold the front on'],
    ].filter((r) => r[0] != null);
    stats.innerHTML = rows.map(([b, s]) => `<li class="rv ${String(b).length > 6 ? 'wide' : ''}"><b>${esc(b)}</b><span>${esc(s)}</span></li>`).join('');
    $$('li', stats).forEach(rv);
  }

  // machines
  const mach = $('#machines');
  if (mach) {
    const M = S.machines || [];
    const plates = (mt.print_hours_per_plate || []);
    const look = [
      { pic: 'img/kit_steel.webp', meta: ['14 ga mild steel', '1.71 mm kerf', `${counts.plasma_parts || 2} plates`] },
      { pic: 'img/kit_birch.webp', meta: ['6 mm Baltic birch', '0.2 mm kerf', `${counts.laser_parts || 8} parts`] },
      { pic: 'img/kit_print.webp', meta: ['PETG', `${plates.length || 4} plates`, mt.print_hours_total ? mt.print_hours_total + ' total' : ''] },
    ];
    mach.innerHTML = M.map((m, i) => `
      <article class="machine rv">
        <img src="${(look[i] || look[2]).pic}" alt="${esc(m.name)}" loading="lazy">
        <div class="body"><h3>${esc(m.name)}</h3><p>${esc(m.role)}</p>
        <div class="meta">${(look[i] || look[2]).meta.filter(Boolean).map((x) => `<span>${esc(x)}</span>`).join('')}</div></div>
      </article>`).join('');
    $$('.machine', mach).forEach(rv);
  }

  // gallery
  const gal = $('#gallery');
  if (gal) {
    const G = S.gallery || [
      ['hero_open', 'The grille off and set beside the box. On the box, eight magnet pairs hold it 15 mm off the devices.', true],
      ['close_carrier', 'A front bracket nose. The magnet sits in the printed part, not on bare steel.'],
      ['close_corner', 'A printed bracket bolted to the plate with two M4. The birch level rests on it, located by pegs.'],
      ['close_cap', 'Outside, a charcoal cap covers each plasma slot. Its spigot centres it in the slot, and two black flanged button heads clamp cap, steel and bracket.'],
      ['service', 'Grille off. The Mac mini M4 sits on the top level and slides straight out by hand. Nothing else moves.'],
      ['close_cords', 'Every cord drops behind the birch spine into the tray.'],
      ['close_button', 'Under the Mac mini M4. Its power button is on the underside, and the cradle leaves that corner open.'],
      ['tray', 'Three power bricks on a birch tray in the bottom bay, DC leads forward.'],
      ['rear', 'The open back. Every cable leaves from one corner.', true],
      ['brick_out', 'Unplug a brick and it slides out the back. The levels stay put.'],
    ];
    gal.innerHTML = G.map((g) => `<figure class="${g[2] ? 'wide ' : ''}rv"><img src="img/${g[0]}.webp" alt="${esc(g[1])}" loading="lazy"><figcaption>${esc(g[1])}</figcaption></figure>`).join('');
    $$('figure', gal).forEach(rv);
  }

  // rounds: chart + strip + detail
  const T = (S.timeline || []).filter((r) => r.scores && typeof r.scores.total === 'number' && !/^FROZEN/i.test(r.id));
  const strip = $('#strip'), chart = $('#chart'), detail = $('#round-detail');
  let sel = -1;
  function roundCard(r, i) {
    const sc = r.scores || {};
    const axes = AX.map((a) => `<i data-s="${sc[a] ?? 0}" style="--s:${sc[a] ?? 0}" title="${a} ${sc[a] ?? '-'}"></i>`).join('');
    return `<article class="rc ${r.line === 'C' ? 'c' : ''}" data-i="${i}" tabindex="0">
      <div class="im">${r.img ? `<img src="${r.img}" alt="${esc(r.title)}" loading="lazy">` : `<span>no picture</span>`}${r.img_note ? `<span class="note">${esc(r.img_note)}</span>` : ''}</div>
      <div class="b"><div class="v"><span>${esc(r.id)}</span><b>${sc.total ?? '-'}<small>/60</small></b></div>
      <h4>${esc(r.title)}</h4><p>${esc(r.change)}</p><div class="axes6">${axes}</div></div></article>`;
  }
  function showRound(i) {
    sel = i; const r = T[i]; if (!r || !detail) return;
    $$('.rc', strip).forEach((c) => c.classList.toggle('sel', +c.dataset.i === i));
    $$('.pt', chart).forEach((c) => c.classList.toggle('sel', +c.dataset.i === i));
    const sc = r.scores || {};
    const vals = AX.map((a) => sc[a]).filter((v) => typeof v === 'number');
    const lo = Math.min(...vals), hi = Math.max(...vals);
    detail.innerHTML = `
      <div class="rd-pic">${r.img ? `<img src="${r.img}" alt="${esc(r.title)}">` : ''}</div>
      <div>
        <h3>${esc(r.id)}: ${esc(r.title)}</h3>
        <div class="meta">${esc(r.date || '')} &middot; ${r.line === 'C' ? 'flat plates + printed brackets' : 'bent steel body + birch'} &middot; ${r.kept ? 'kept' : 'not kept'}</div>
        <p><b>Changed:</b> ${esc(r.change)}</p>
        <p><b>The critic found:</b> ${esc(r.result)}</p>
        <div class="scores">${AX.map((a) => `<div><b class="${sc[a] === lo && lo < hi ? 'lo' : (sc[a] >= 8 ? 'hi' : '')}">${sc[a] ?? '-'}</b>${a}</div>`).join('')}</div>
        ${r.lesson ? `<p class="lesson">${esc(r.lesson)}</p>` : ''}
      </div>`;
    const card = $(`.rc[data-i="${i}"]`, strip);
    if (card && document.activeElement !== document.body) card.scrollIntoView({ block: 'nearest', inline: 'center', behavior: reduced ? 'auto' : 'smooth' });
  }
  if (strip && T.length) {
    strip.innerHTML = `<div class="pad"></div>` + T.map(roundCard).join('') + `<div class="pad"></div>`;
    strip.addEventListener('click', (e) => { const c = e.target.closest('.rc'); if (c) showRound(+c.dataset.i); });
    strip.addEventListener('keydown', (e) => { const c = e.target.closest('.rc'); if (c && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); showRound(+c.dataset.i); } });
    $('.strip-nav .prev')?.addEventListener('click', () => strip.scrollBy({ left: -600, behavior: 'smooth' }));
    $('.strip-nav .next')?.addEventListener('click', () => strip.scrollBy({ left: 600, behavior: 'smooth' }));
  }
  if (chart && T.length) {
    const W = 1000, H = 300, L = 36, R = 16, Tp = 20, B = 44;
    const x = (i) => L + (i / (T.length - 1)) * (W - L - R);
    const y = (v) => Tp + (1 - (v - 30) / 30) * (H - Tp - B);
    const segs = []; let cur = null;
    T.forEach((r, i) => { if (!cur || cur.line !== r.line) { cur = { line: r.line, pts: [] }; segs.push(cur); } cur.pts.push([x(i), y(r.scores.total)]); });
    // join the main line's last point to the C line's first point with the C colour
    for (let k = 1; k < segs.length; k++) segs[k].pts.unshift(segs[k - 1].pts[segs[k - 1].pts.length - 1]);
    const path = (pts) => pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
    const grid = [30, 40, 50, 60].map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text class="lbl" x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${v}</text>`).join('');
    const pts = T.map((r, i) => `<circle class="pt ${r.line === 'C' ? 'c' : ''}" data-i="${i}" cx="${x(i)}" cy="${y(r.scores.total)}" r="5"><title>${esc(r.id)}: ${r.scores.total}/60</title></circle>`).join('');
    const every = T.length > 14 ? 2 : 1;
    const labels = T.map((r, i) => (i % every === 0 || i === T.length - 1) ? `<text class="lbl" x="${x(i)}" y="${H - 14}" text-anchor="middle">${esc(r.id)}</text>` : '').join('');
    chart.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Critic total per round, 30 to 60">
      <g class="grid">${grid}</g>
      <line class="gate" x1="${L}" x2="${W - R}" y1="${y(48)}" y2="${y(48)}"/><text class="gate-t" x="${W - R}" y="${y(48) - 6}" text-anchor="end">8 on every axis = 48</text>
      ${segs.map((s) => `<path class="trace ${s.line === 'C' ? 'c' : ''}" d="${path(s.pts)}"/>`).join('')}
      ${pts}<g class="axis">${labels}</g></svg>`;
    $$('.trace', chart).forEach((p) => { const len = p.getTotalLength(); p.style.setProperty('--len', len); });
    const cio = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { chart.classList.add('drawn'); cio.disconnect(); } }), { threshold: 0.4 });
    cio.observe(chart);
    chart.addEventListener('click', (e) => { const c = e.target.closest('.pt'); if (c) showRound(+c.dataset.i); });
    const note = $('#chart-note');
    if (note) note.innerHTML = `<span><i></i>bent steel body + birch (v0.2 to v1.1)</span><span><i class="c"></i>flat plates + printed brackets (C1 to C2R7)</span><span>click a point or a card</span>`;
    const por = T.findIndex((r) => r.id === (S.meta && S.meta.plan_of_record));
    showRound(por >= 0 ? por : T.length - 1);
  }

  // concepts
  const cg = $('#concepts-grid');
  if (cg) {
    const CC = S.concepts || [];
    const top = Math.max(...CC.map((c) => c.scores?.total ?? 0));
    cg.innerHTML = CC.map((c) => { const win = c.winner || (c.scores?.total === top); return `
      <article class="concept ${win ? 'win' : ''} rv">
        ${c.img ? `<img src="${c.img}" alt="${esc(c.name)}" loading="lazy">` : ''}
        <div class="body">${win ? '<span class="win-tag">Winner</span>' : ''}<div class="v"><span>${esc(c.id)}</span><b>${c.scores?.total ?? '-'}<small style="font-size:11px;color:var(--cream-2)">/60</small></b></div>
        <h3>${esc(c.name)}</h3><p>${esc(c.body || c.paragraph)}</p></div></article>`; }).join('');
    $$('.concept', cg).forEach(rv);
  }

  // forks
  const fl = $('#forks-list');
  if (fl) {
    fl.innerHTML = (S.forks || []).map((f, i) => `
      <details class="fork rv" ${i === 0 ? 'open' : ''}>
        <summary><span class="n">${String(i + 1).padStart(2, '0')}</span><span>${esc(f.question)}</span><span class="chev">+</span></summary>
        <div class="opts" style="${(f.options || []).length > 2 ? 'grid-template-columns:repeat(auto-fit,minmax(220px,1fr))' : ''}">${(f.options || []).map((o) => { const ch = o.name === f.chosen || (f.chosen && o.name.toLowerCase().startsWith(f.chosen.toLowerCase().slice(0, 12))); return `
          <div class="opt ${ch ? 'chosen' : ''}">
            <h4>${esc(o.name)}</h4>${o.img ? `<img src="${o.img}" alt="${esc(o.name)}" loading="lazy">` : ''}
            <ul>${(o.pros || []).map((p) => `<li>${esc(p)}</li>`).join('')}${(o.cons || []).map((p) => `<li class="con">${esc(p)}</li>`).join('')}</ul>
            ${(o.fact || o.score_or_fact) ? `<div class="fact">${esc(o.fact || o.score_or_fact)}</div>` : ''}
          </div>`; }).join('')}</div>
        <p class="why"><b>Why:</b> ${esc(f.why)}</p>
      </details>`).join('');
    $$('.fork', fl).forEach(rv);
  }

  // critic
  const C = S.critic || {};
  if ($('#critic-how')) $('#critic-how').textContent = C.how || '';
  if ($('#axes')) $('#axes').innerHTML = (C.axes || []).map((a) => `<li><b>${esc(a.name)}</b><span>${esc(a.def || a.definition)}</span></li>`).join('');
  const scb = $('#scorecard');
  const byId = (id) => (S.timeline || []).find((r) => r.id === id);
  if (!C.final && byId('C2R5')) {
    C.final = { label: 'C2R5, the plan of record', note: 'first read on realistic renders, 44 of 60', scores: byId('C2R5').scores };
    if (byId('v1.1')) C.previous = { label: 'v1.1, bent steel body', scores: byId('v1.1').scores };
  }
  if (scb && C.final) {
    const f = C.final, p = C.previous || {};
    scb.innerHTML = `<h3>${esc(f.label || 'Final')}</h3><div class="sub">${esc(f.note || '')}</div>
      ${AX.map((a) => `<div class="sc-row"><span class="lbl">${a}</span><div class="bar">${p.scores ? `<i class="prev" style="--s:${p.scores[a] ?? 0}"></i>` : ''}<i style="--s:${f.scores[a] ?? 0}"></i></div><span class="n">${f.scores[a] ?? '-'}</span></div>`).join('')}
      <div class="total"><span>total</span><b>${f.scores.total}<small style="font-size:12px;color:var(--cream-2)"> / 60</small></b></div>
      ${p.scores ? `<div class="legend"><span><i></i>${esc(f.label)}</span><span><i class="prev"></i>${esc(p.label)} (${p.scores.total})</span></div>` : ''}`;
    const bars = $$('.sc-row .bar i', scb);
    bars.forEach((b) => { const s = b.style.getPropertyValue('--s'); b.style.setProperty('--s', 0); b.dataset.s = s; });
    const sio = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { bars.forEach((b) => b.style.setProperty('--s', b.dataset.s)); sio.disconnect(); } }), { threshold: 0.3 });
    sio.observe(scb);
  }

  // lessons
  const lg = $('#lessons-grid');
  if (lg) { lg.innerHTML = (S.lessons || []).map((l) => `<li class="rv"><h3>${esc(l.title)}</h3><p>${esc(l.body)}</p></li>`).join(''); $$('li', lg).forEach(rv); }

  // kit
  if ($('#devices')) $('#devices').innerHTML = (P.holds || P.devices || []).map((d) => `<li>${esc(d.device || d.name)}<span>${esc(d.size_mm || d.size || '')}</span></li>`).join('');
  const K = S.kit || {};
  if ($('#kitlist')) {
    const rows = [];
    (K.steel || []).forEach((k) => rows.push([k.part + ', steel', `${k.qty} x ${k.size_mm}`]));
    (K.birch || []).forEach((k) => rows.push([k.part + ', birch', `${k.qty} x ${k.size_mm}`]));
    (K.printed || []).forEach((k) => rows.push([k.part + ', PETG', `${k.qty}${k.g_each ? ` x ${k.g_each} g` : ''}`]));
    (K.hardware || []).forEach((k) => rows.push([k.item, k.qty]));
    if (Array.isArray(K)) K.forEach((k) => rows.push([k.item, k.qty]));
    $('#kitlist').innerHTML = rows.map(([a, b]) => `<li>${esc(a)}<span>${esc(b)}</span></li>`).join('') + (K.tools ? `<li>Tools<span>${esc(K.tools.join(', '))}</span></li>` : '');
  }
  if ($('#steps')) $('#steps').innerHTML = (S.build_steps || []).map((s) => `<li>${esc(typeof s === 'string' ? s : s.text)}</li>`).join('');

  // section heads reveal
  $$('.sec-head, .scorecard, .round-detail').forEach(rv);
})();
