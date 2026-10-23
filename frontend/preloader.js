(() => {
  const root = document.getElementById('preloader');
  if (!root) return;
  document.body.classList.add('loading');
  const cv = root.querySelector('canvas');
  const ctx = cv.getContext('2d');
  const barFill = root.querySelector('.bar i');
  const pctEl = root.querySelector('.pct');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const DUR = reduce ? 1200 : 4200;
  const WAVE = 110, AMP = 24, STEP = 3, RUNG = 13;
  const THICK = 8;

  let W = 0, H = 0, raf = 0, loaded = document.readyState === 'complete';
  addEventListener('load', () => { loaded = true; }, { once: true });

  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    W = innerWidth; H = innerHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  addEventListener('resize', resize);

  const ease = t => 1 - Math.pow(1 - t, 3);
  const clamp01 = t => t < 0 ? 0 : t > 1 ? 1 : t;
  const smooth = t => { t = clamp01(t); return t * t * (3 - 2 * t); };

  function helix(ax, ay, bx, by, f, phase, taperStart, taperEnd) {
    if (f <= 0) return;
    const dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy);
    const ux = dx / L, uy = dy / L, px = -uy, py = ux;
    const len = L * f, k = (2 * Math.PI) / WAVE;
    const ampAt = s => AMP * smooth(s / taperStart) * smooth((L - s) / taperEnd);

    for (let strand = 0; strand < 2; strand++) {
      const off = strand * Math.PI;
      for (let pass = 0; pass < 2; pass++) {
        ctx.beginPath();
        let pen = false;
        for (let s = 0; s <= len; s += STEP) {
          const a = k * s + phase + off;
          const front = Math.cos(a) > 0;
          if (front !== !!pass) { pen = false; continue; }
          const w = Math.sin(a) * ampAt(s);
          const x = ax + ux * s + px * w, y = ay + uy * s + py * w;
          pen ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
          pen = true;
        }
        const col = strand ? '247,198,217' : '255,255,255';
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.strokeStyle = `rgba(${col},${pass ? 0.18 : 0.06})`; ctx.lineWidth = THICK * 3.5; ctx.stroke();
        ctx.strokeStyle = `rgba(${col},${pass ? 0.95 : 0.35})`; ctx.lineWidth = pass ? THICK : THICK * 0.65; ctx.stroke();
      }
    }

    for (let s = RUNG; s <= len; s += RUNG) {
      const a = k * s + phase, amp = ampAt(s);
      const w1 = Math.sin(a) * amp, w2 = -w1, depth = Math.cos(a);
      const cx = ax + ux * s, cy = ay + uy * s;
      const alpha = 0.25 + 0.45 * Math.abs(depth);
      ctx.strokeStyle = `rgba(247,198,217,${alpha})`; ctx.lineWidth = 1.8;
      ctx.beginPath(); ctx.moveTo(cx + px * w1, cy + py * w1); ctx.lineTo(cx + px * w2, cy + py * w2); ctx.stroke();
      ctx.fillStyle = `rgba(255,255,255,${0.4 + 0.5 * Math.max(depth, 0)})`;
      ctx.beginPath(); ctx.arc(cx + px * w1, cy + py * w1, THICK * 0.6 + depth, 0, 6.283); ctx.fill();
      ctx.beginPath(); ctx.arc(cx + px * w2, cy + py * w2, THICK * 0.6 - depth, 0, 6.283); ctx.fill();
    }

    if (f < 1) glow(ax + ux * len, ay + uy * len, 26, 0.55);
  }

  function glow(x, y, r, a) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(255,255,255,${a})`);
    g.addColorStop(0.4, `rgba(247,198,217,${a * 0.5})`);
    g.addColorStop(1, 'rgba(247,198,217,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
  }

  const t0 = performance.now();
  function frame(now) {
    const el = now - t0, p = clamp01(el / DUR);
    const shown = loaded ? p : Math.min(p, 0.92);
    const pct = Math.round(shown * 100);
    barFill.style.width = pct + '%';
    pctEl.textContent = pct + '%';

    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter';
    const cx = W / 2, cy = H / 2 + 30, phase = el * 0.004;
    const arms = ease(clamp01(p / 0.45));
    const stem = ease(clamp01((p - 0.5) / 0.5));

    helix(0, 0, cx, cy, arms, phase, 60, 90);
    helix(W, 0, cx, cy, arms, -phase + Math.PI, 60, 90);
    if (p > 0.38) {
      const m = Math.sin(Math.PI * clamp01((p - 0.38) / 0.3));
      glow(cx, cy, 40 + 70 * m, 0.35 + 0.5 * m);
    }
    helix(cx, cy, cx, H + 40, stem, phase * 1.2, 90, 1);
    ctx.globalCompositeOperation = 'source-over';

    if (shown >= 1) return finish();
    raf = requestAnimationFrame(frame);
  }

  function finish() {
    root.classList.add('done');
    document.body.classList.remove('loading');
    removeEventListener('resize', resize);
    dispatchEvent(new Event('preloader:done'));

    setTimeout(() => { cv.width = cv.height = 0; root.remove(); }, 800);
  }

  raf = requestAnimationFrame(frame);
})();
