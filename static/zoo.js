/* =====================================================================
   CALCULADORA Z00 — animaciones e interacciones compartidas
   Solo presentación: no toca ningún formulario ni cálculo.
   ===================================================================== */
(function () {
  'use strict';

  const body = document.body;
  const THEME = body.dataset.theme || 'menu';
  const STATIC = (body.dataset.static || '/static/').replace(/\/?$/, '/');
  const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = arr => arr[Math.floor(Math.random() * arr.length)];

  /* ---------- Configuración de cada recinto ---------- */
  const THEMES = {
    menu:      { mode: 'twinkle', glow: '#ffe27a', count: 34, size: [3, 7], burst: ['🐾', '🦁', '🐘', '🦒', '🐼', '🦓'] },
    magia:     { mode: 'twinkle', chars: ['✨', '✦', '⭐'], count: 22, size: [10, 22], burst: ['✨', '🪄', '🐰', '⭐', '🎩'] },
    tropical:  { mode: 'fall', chars: ['🍃', '🌿', '🍂'], count: 14, size: [16, 26], burst: ['🌴', '🦦', '🍊', '🍃', '🥥'] },
    ajolote:   { mode: 'rise', bubble: true, count: 26, size: [8, 26], burst: ['🫧', '💗', '🦎', '💧', '🩷'] },
    desierto:  { mode: 'fall', sand: true, count: 30, size: [3, 6], burst: ['🐍', '🐫', '🌵', '☀️', '🏜️'] },
    artico:    { mode: 'fall', chars: ['❄', '❅', '❆', '•'], count: 30, size: [10, 22], color: '#ffffff', burst: ['❄️', '🐳', '🧊', '💙', '🐋'] },
    undertale: { mode: 'twinkle', glow: '#ffffff', count: 26, size: [2, 4], square: true, burst: ['❤️', '⭐', '💀', '🦴'] }
  };
  const CFG = THEMES[THEME] || THEMES.menu;

  /* ---------- 1. Partículas de fondo ---------- */
  function buildParticles() {
    const layer = document.querySelector('.zoo-particles');
    if (!layer || REDUCED) return;
    const count = window.innerWidth < 700 ? Math.round(CFG.count * 0.55) : CFG.count;
    for (let i = 0; i < count; i++) {
      const p = document.createElement('span');
      p.className = 'zoo-particle';
      const size = rand(CFG.size[0], CFG.size[1]);
      p.style.left = rand(0, 100) + 'vw';
      p.style.animationDuration = rand(CFG.mode === 'twinkle' ? 2.5 : 9, CFG.mode === 'twinkle' ? 6 : 20) + 's';
      p.style.animationDelay = -rand(0, 20) + 's';
      p.style.setProperty('--drift', rand(-80, 80) + 'px');
      p.style.setProperty('--spin', rand(-540, 540) + 'deg');

      if (CFG.mode === 'rise') p.classList.add('up');
      if (CFG.mode === 'twinkle') {
        p.classList.add('twinkle');
        p.style.top = rand(0, 100) + 'vh';
      }

      if (CFG.bubble) {
        Object.assign(p.style, {
          width: size + 'px', height: size + 'px', borderRadius: '50%',
          border: '2px solid rgba(255,255,255,.9)',
          background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,.9), rgba(255,120,176,.15) 60%, rgba(16,163,182,.12))'
        });
        p.style.setProperty('--o', rand(.45, .85));
      } else if (CFG.sand) {
        Object.assign(p.style, { width: size + 'px', height: size + 'px', borderRadius: '50%', background: pick(['#e8a73a', '#c8611e', '#f3cf8f']) });
        p.style.setProperty('--drift', rand(120, 320) + 'px');
        p.style.setProperty('--o', rand(.35, .7));
      } else if (CFG.glow) {
        Object.assign(p.style, {
          width: size + 'px', height: size + 'px',
          borderRadius: CFG.square ? '0' : '50%',
          background: CFG.glow,
          boxShadow: `0 0 ${size * 3}px ${size}px ${CFG.glow}66`
        });
        p.style.setProperty('--o', rand(.5, 1));
      } else {
        p.textContent = pick(CFG.chars);
        p.style.fontSize = size + 'px';
        if (CFG.color) { p.style.color = CFG.color; p.style.textShadow = '0 0 6px rgba(14,141,176,.6)'; }
        p.style.setProperty('--o', rand(.45, .9));
      }
      layer.appendChild(p);
    }
  }

  /* ---------- 2. Aparición al hacer scroll ---------- */
  function setupReveal() {
    const items = document.querySelectorAll('.zoo-reveal');
    if (!('IntersectionObserver' in window) || REDUCED) {
      items.forEach(el => el.classList.add('is-visible'));
      return;
    }
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
    items.forEach((el, i) => {
      if (!el.style.getPropertyValue('--delay')) el.style.setProperty('--delay', Math.min(i * 0.07, 0.35) + 's');
      io.observe(el);
    });
  }

  /* ---------- 3. Efecto "onda" en botones ---------- */
  function setupRipple() {
    document.addEventListener('pointerdown', e => {
      const btn = e.target.closest('.btn-zoo');
      if (!btn) return;
      const r = btn.getBoundingClientRect();
      const s = Math.max(r.width, r.height);
      const dot = document.createElement('span');
      dot.className = 'zoo-ripple';
      Object.assign(dot.style, { width: s + 'px', height: s + 'px', left: (e.clientX - r.left - s / 2) + 'px', top: (e.clientY - r.top - s / 2) + 'px' });
      btn.appendChild(dot);
      setTimeout(() => dot.remove(), 700);
    });
  }

  /* ---------- 4. Pantalla de carga al enviar formularios ---------- */
  function setupLoader() {
    const loader = document.getElementById('zoo-loader');
    if (!loader) return;
    document.querySelectorAll('form[data-zoo-loader]').forEach(form => {
      form.addEventListener('submit', ev => {
        // Se espera un instante: si otra validación canceló el envío, no se muestra.
        setTimeout(() => { if (!ev.defaultPrevented) loader.classList.add('show'); }, 0);
      });
    });
    window.addEventListener('pageshow', () => loader.classList.remove('show'));
  }

  /* ---------- 5. Ir directo a los resultados ---------- */
  function setupAutoScroll() {
    const target = document.querySelector('[data-zoo-scroll]');
    if (!target) return;
    setTimeout(() => {
      const y = target.getBoundingClientRect().top + window.scrollY - 86;
      window.scrollTo({ top: y, behavior: REDUCED ? 'auto' : 'smooth' });
      const res = document.querySelector('.zoo-result');
      if (res) setTimeout(() => burstFrom(res, 18), 650);
    }, 350);
  }

  /* ---------- 6. Ráfaga de emojis ---------- */
  function burstAt(x, y, n, set) {
    if (REDUCED) return;
    const emojis = set || CFG.burst;
    for (let i = 0; i < n; i++) {
      const b = document.createElement('span');
      b.className = 'zoo-burst';
      b.textContent = pick(emojis);
      const ang = rand(0, Math.PI * 2), dist = rand(60, 170);
      b.style.left = x + 'px'; b.style.top = y + 'px';
      b.style.setProperty('--dx', Math.cos(ang) * dist + 'px');
      b.style.setProperty('--dy', Math.sin(ang) * dist - 40 + 'px');
      b.style.setProperty('--rot', rand(-200, 200) + 'deg');
      b.style.fontSize = rand(16, 30) + 'px';
      document.body.appendChild(b);
      setTimeout(() => b.remove(), 1200);
    }
  }
  function burstFrom(el, n, set) {
    const r = el.getBoundingClientRect();
    burstAt(r.left + r.width / 2, r.top + Math.min(r.height / 2, 140), n, set);
  }

  /* ---------- 7. Mascotas que saltan al hacer clic ---------- */
  function setupMascots() {
    document.addEventListener('click', e => {
      const m = e.target.closest('.zoo-mascot, .zoo-hero-emojis span, [data-zoo-jump]');
      if (!m) return;
      m.classList.remove('jump'); void m.offsetWidth; m.classList.add('jump');
      burstAt(e.clientX, e.clientY, 9);
      setTimeout(() => m.classList.remove('jump'), 750);
    });
  }

  /* ---------- 8. Los "00" de la marca son ojos que te siguen ---------- */
  function setupEyes() {
    const eyes = document.querySelectorAll('.eye-o, .eye-big');
    if (!eyes.length) return;
    let raf = null;
    document.addEventListener('pointermove', e => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = null;
        eyes.forEach(eye => {
          const r = eye.getBoundingClientRect();
          const dx = e.clientX - (r.left + r.width / 2);
          const dy = e.clientY - (r.top + r.height / 2);
          const ang = Math.atan2(dy, dx);
          const max = r.width * 0.2;
          const d = Math.min(max, Math.hypot(dx, dy) / 25);
          eye.style.setProperty('--ex', Math.cos(ang) * d + 'px');
          eye.style.setProperty('--ey', Math.sin(ang) * d + 'px');
        });
      });
    });
  }

  /* ---------- 9. Mensajes flotantes ---------- */
  let toastTimer = null;
  function toast(msg, ms) {
    let t = document.getElementById('zoo-toast');
    if (!t) { t = document.createElement('div'); t.id = 'zoo-toast'; t.className = 'zoo-toast'; document.body.appendChild(t); }
    t.innerHTML = msg;
    requestAnimationFrame(() => t.classList.add('show'));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), ms || 3800);
  }

  /* ---------- 10. Animales que cruzan la pantalla ---------- */
  function runner(content, opts) {
    opts = opts || {};
    const el = document.createElement('div');
    el.className = 'zoo-runner';
    const inner = document.createElement('div');
    if (opts.img) { const im = document.createElement('img'); im.src = STATIC + opts.img; im.alt = ''; inner.appendChild(im); }
    else inner.textContent = content;
    el.appendChild(inner);
    el.style.top = (opts.top != null ? opts.top : rand(15, 85)) + 'vh';
    el.style.fontSize = (opts.size || rand(34, 60)) + 'px';
    el.style.animationDuration = (opts.dur || rand(3.2, 6.5)) + 's';
    el.style.animationDelay = (opts.delay || 0) + 's';
    if (opts.flip) el.classList.add('flip');
    document.body.appendChild(el);
    setTimeout(() => el.remove(), ((opts.dur || 7) + (opts.delay || 0) + 1) * 1000);
  }

  function estampida() {
    const animales = ['🦓', '🦒', '🐘', '🦏', '🦛', '🐆', '🐅', '🦘', '🐊', '🦩', '🐒', '🦬', '🐫', '🦦', '🐧', '🦁'];
    for (let i = 0; i < 18; i++) runner(pick(animales), { delay: rand(0, 2.6), flip: true });
    document.querySelector('.zoo-main')?.classList.add('zoo-shake-hard');
    setTimeout(() => document.querySelector('.zoo-main')?.classList.remove('zoo-shake-hard'), 500);
    toast('🚨 ¡ESTAMPIDA! Alguien dejó abiertos los recintos del zoológico 🐘🦒🦓');
  }

  /* ---------- 11. Diálogo estilo Undertale (máquina de escribir) ---------- */
  function typewriter(el, text, speed) {
    if (!el) return Promise.resolve();
    clearInterval(el._tw);
    el.textContent = '';
    let i = 0;
    return new Promise(res => {
      el._tw = setInterval(() => {
        el.textContent = text.slice(0, ++i);
        if (i >= text.length) { clearInterval(el._tw); res(); }
      }, speed || 32);
    });
  }

  function sansSpeech() {
    document.querySelector('.zoo-speech')?.remove();
    const box = document.createElement('div');
    box.className = 'zoo-speech';
    box.innerHTML = `<div class="bubble"></div><img src="${STATIC}san.gif" alt="">`;
    document.body.appendChild(box);
    const lines = [
      '* heh. así que encontraste el atajo secreto, ¿eh?',
      '* tranquilo. no le diré al profe.',
      '* pero si tu determinante da 0... la matriz se queda sin cuerpo. ¿entiendes? sin cuerpo.'
    ];
    const bubble = box.querySelector('.bubble');
    (async () => {
      for (const l of lines) { await typewriter(bubble, l, 38); await new Promise(r => setTimeout(r, 1300)); }
      box.style.transition = 'opacity .5s'; box.style.opacity = '0';
      setTimeout(() => box.remove(), 600);
    })();
  }

  /* ---------- 12. Huevos de pascua ---------- */
  function setupEasterEggs() {
    // a) Código Konami: ↑ ↑ ↓ ↓ ← → ← → B A
    const KONAMI = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let kIdx = 0;
    // b) Palabras secretas escritas fuera de los campos de texto
    let buffer = '';
    const WORDS = {
      zoo: estampida,
      capi: () => { runner('', { img: 'capi.gif', top: 72, size: 120, dur: 7 }); toast('🕶️ Capibara en modo relax. Nada le preocupa, ni siquiera una matriz singular.'); },
      beluga: () => { runner('', { img: 'zoo/be1.png', top: 40, size: 110, dur: 6, flip: true }); runner('🫧', { top: 42, size: 30, dur: 6.4, delay: .2, flip: true }); toast('🐳 ¡Una beluga se escapó del Recinto Ártico!'); },
      sans: sansSpeech,
      magia: () => { burstAt(innerWidth / 2, innerHeight / 2, 40, ['✨', '🪄', '🐰', '⭐', '🎩']); toast('🎩 ¡Abracadabra! …la inversa sigue sin existir si det(A) = 0.'); },
      ajolote: () => { for (let i = 0; i < 25; i++) runner('🫧', { top: rand(10, 90), size: rand(20, 50), dur: rand(4, 7), delay: rand(0, 1.5) }); runner('', { img: 'zoo/ajo1.png', top: 60, size: 110, dur: 6 }); toast('🦎 Los ajolotes cuentan en binario: 01000001 = ¡hola!'); }
    };
    const maxLen = Math.max(...Object.keys(WORDS).map(w => w.length));

    document.addEventListener('keydown', e => {
      const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
      kIdx = (key === KONAMI[kIdx]) ? kIdx + 1 : (key === KONAMI[0] ? 1 : 0);
      if (kIdx === KONAMI.length) { kIdx = 0; estampida(); return; }

      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) return;
      if (e.key.length !== 1) return;
      buffer = (buffer + e.key.toLowerCase()).slice(-maxLen);
      for (const w in WORDS) {
        if (buffer.endsWith(w)) { buffer = ''; WORDS[w](); break; }
      }
    });

    // c) Cinco clics rápidos en la huellita de la marca → modo huellitas
    const paw = document.querySelector('.zoo-brand .paw');
    if (paw) {
      let clicks = 0, timer = null;
      paw.addEventListener('click', e => {
        e.preventDefault();
        clicks++;
        clearTimeout(timer);
        timer = setTimeout(() => {
          if (clicks === 1) window.location.href = paw.closest('a').href;
          clicks = 0;
        }, 380);
        if (clicks >= 5) { clicks = 0; clearTimeout(timer); huellitas(); }
      });
    }
  }

  let pawMode = false;
  function huellitas() {
    if (pawMode) return;
    pawMode = true;
    toast('🐾 Modo huellitas activado: ahora dejas rastro por todo el zoológico (20 s)');
    let last = 0, flip = false;
    const onMove = e => {
      const now = performance.now();
      if (now - last < 70) return;
      last = now; flip = !flip;
      const p = document.createElement('span');
      p.className = 'zoo-paw-print';
      p.textContent = '🐾';
      p.style.left = (e.clientX + (flip ? 6 : -6)) + 'px';
      p.style.top = e.clientY + 'px';
      p.style.rotate = rand(-25, 25) + 'deg';
      document.body.appendChild(p);
      setTimeout(() => p.remove(), 1650);
    };
    document.addEventListener('pointermove', onMove);
    setTimeout(() => { document.removeEventListener('pointermove', onMove); pawMode = false; }, 20000);
  }

  /* ---------- 13. Firma para curiosos de la consola ---------- */
  function consoleArt() {
    const css = 'font: 700 14px monospace; color: #1f7a52;';
    console.log('%c\n   (\\_/)   ¿Inspeccionando el zoológico?\n   (•ᴥ•)   Prueba escribir: zoo · capi · sans · beluga · magia · ajolote\n   / >🧮   …o el código Konami ↑↑↓↓←→←→BA\n', css);
  }

  /* ---------- Arranque ---------- */
  document.addEventListener('DOMContentLoaded', () => {
    buildParticles();
    setupReveal();
    setupRipple();
    setupLoader();
    setupAutoScroll();
    setupMascots();
    setupEyes();
    setupEasterEggs();
    consoleArt();
  });

  // API pública para las páginas que la necesiten
  window.Zoo = { toast, burstAt, burstFrom, runner, estampida, typewriter };
})();
