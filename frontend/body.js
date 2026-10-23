const Body = (() => {
  const RING = 24;
  const RING_EVERY = 4;
  let seed = 11;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

  const pts = [];
  const samples = [];
  const tubes = [];
  const deco = [];
  const nerves = [];
  const mains = [];

  const add = (x, y, z) => { pts.push(x, y, z); return pts.length / 3 - 1; };
  const norm = v => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; };
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const cr = (p0, p1, p2, p3, t) => {
    const t2 = t * t, t3 = t2 * t;
    return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
  };

  function tube(nodes, ds = 0.016) {

    const sm = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      const P0 = nodes[i - 1] || nodes[i], P1 = nodes[i], P2 = nodes[i + 1], P3 = nodes[i + 2] || nodes[i + 1];
      const len = Math.hypot(P2[0] - P1[0], P2[1] - P1[1], P2[2] - P1[2]);
      const steps = Math.max(2, Math.ceil(len / ds));
      for (let s = i ? 1 : 0; s <= steps; s++) {
        const u = s / steps, v = [];
        for (let k = 0; k < 5; k++) v.push(cr(P0[k], P1[k], P2[k], P3[k], u));
        sm.push(v);
      }
    }

    const first = samples.length;
    for (let i = 0; i < sm.length; i++) {
      const a = sm[Math.max(0, i - 1)], b = sm[Math.min(sm.length - 1, i + 1)];
      const t = norm([b[0] - a[0], b[1] - a[1], b[2] - a[2]]);
      const up = Math.abs(t[2]) > 0.75 ? [0, 1, 0] : [0, 0, 1];
      const n = norm(cross(t, up)), bb = norm(cross(t, n));
      const [x, y, z] = sm[i], rx = Math.max(sm[i][3], 0.002), rz = Math.max(sm[i][4], 0.002);
      const S = { c: [x, y, z], rx, rz, n, b: bb,
        ci: add(x, y, z),
        ni: add(x + n[0] * rx, y + n[1] * rx, z + n[2] * rx),
        bi: add(x + bb[0] * rz, y + bb[1] * rz, z + bb[2] * rz) };
      samples.push(S);
      if (i % RING_EVERY === 2) {
        deco.push(pts.length / 3);
        for (let j = 0; j < RING; j++) {
          const th = (j / RING) * Math.PI * 2, cs = Math.cos(th) * rx, sn = Math.sin(th) * rz;
          add(x + n[0] * cs + bb[0] * sn, y + n[1] * cs + bb[1] * sn, z + n[2] * cs + bb[2] * sn);
        }
      }
    }
    tubes.push([first, sm.length]);
    return [first, sm.length];
  }

  function line(arr, colour, main = 0) {
    const start = pts.length / 3;
    for (const p of arr) add(p[0], p[1], p[2]);
    nerves.push([start, arr.length, colour, main]);
    if (main) mains.push(nerves.length - 1);
  }

  const head = [];
  for (let i = 0; i <= 14; i++) {
    const th = (i / 14) * Math.PI, r = Math.sin(th);

    const jaw = 1 - 0.18 * Math.max(0, -Math.cos(th));
    head.push([0, 0.80 + 0.125 * Math.cos(th), 0.004, 0.092 * r * jaw, 0.108 * r]);
  }
  tube(head, 0.012);
  tube([[0, 0.70, -0.01, 0.042, 0.044], [0, 0.66, -0.006, 0.046, 0.046], [0, 0.60, 0, 0.06, 0.054]]);
  const TORSO = [
    [0, 0.62, 0, 0.07, 0.06], [0, 0.595, 0, 0.15, 0.085], [0, 0.565, 0, 0.205, 0.105],
    [0, 0.50, 0.004, 0.205, 0.118], [0, 0.40, 0.008, 0.188, 0.122], [0, 0.29, 0.004, 0.162, 0.112],
    [0, 0.17, 0, 0.142, 0.098], [0, 0.07, 0, 0.152, 0.098], [0, -0.03, -0.004, 0.168, 0.102],
    [0, -0.10, 0, 0.17, 0.1], [0, -0.16, 0.004, 0.13, 0.08], [0, -0.19, 0.004, 0.05, 0.04]];
  const torso = tube(TORSO);
  const arm = s => [[s * 0.15, 0.54, 0, 0.04, 0.045], [s * 0.2, 0.525, 0, 0.056, 0.058], [s * 0.232, 0.46, -0.004, 0.056, 0.056],
    [s * 0.25, 0.36, -0.008, 0.047, 0.048], [s * 0.262, 0.22, -0.01, 0.038, 0.04],
    [s * 0.272, 0.16, -0.004, 0.04, 0.04], [s * 0.284, 0.04, 0.012, 0.033, 0.03],
    [s * 0.294, -0.07, 0.022, 0.025, 0.021], [s * 0.3, -0.12, 0.026, 0.032, 0.016],
    [s * 0.302, -0.19, 0.03, 0.022, 0.012], [s * 0.3, -0.23, 0.03, 0.006, 0.005]];
  const leg = s => [[s * 0.07, 0.0, 0, 0.07, 0.07], [s * 0.085, -0.1, 0.004, 0.088, 0.09], [s * 0.094, -0.24, 0.006, 0.078, 0.08],
    [s * 0.098, -0.40, 0.004, 0.06, 0.062], [s * 0.1, -0.51, 0, 0.048, 0.05],
    [s * 0.1, -0.62, -0.012, 0.052, 0.054], [s * 0.1, -0.76, -0.006, 0.038, 0.04],
    [s * 0.1, -0.88, 0, 0.026, 0.028], [s * 0.1, -0.93, 0.004, 0.028, 0.028]];
  const foot = s => [[s * 0.1, -0.925, -0.01, 0.03, 0.028], [s * 0.1, -0.95, 0.04, 0.034, 0.02],
    [s * 0.1, -0.962, 0.1, 0.03, 0.013], [s * 0.1, -0.966, 0.14, 0.006, 0.005]];
  const limbs = [];
  for (const s of [1, -1]) { limbs.push(tube(arm(s))); limbs.push(tube(leg(s))); tube(foot(s), 0.014); }

  const at = (sm, a, b) => {
    const { c, n, b: bb, rx, rz } = sm;
    return [c[0] + n[0] * rx * a + bb[0] * rz * b, c[1] + n[1] * rx * a + bb[1] * rz * b, c[2] + n[2] * rx * a + bb[2] * rz * b];
  };
  function follow([first, count], colour, offN, offB, wob, phase, twigs = true) {
    const out = [];
    for (let i = 0; i < count; i++) out.push(at(samples[first + i], offN + Math.sin(i * 0.18 + phase) * wob, offB));
    line(out, colour, 1);
    if (!twigs) return;

    for (let i = 6; i < count - 4; i += 5) {
      if (rnd() < 0.45) continue;
      const side = rnd() < 0.5 ? -1 : 1, len = 0.25 + rnd() * 0.25, tw = [];
      for (let k = 0; k <= 6; k++) {
        const f = k / 6, sm = samples[first + Math.min(count - 1, i + k)];
        tw.push(at(sm, offN + side * f * len, offB + f * len * 0.5 * side));
      }
      line(tw, colour);
    }
  }
  follow(torso, 0, 0.06, -0.6, 0.02, 0, false);
  follow(torso, 1, -0.06, -0.6, 0.02, 1.5, false);
  follow(torso, 0, 0.3, 0.3, 0.04, 0.4, false);
  follow(torso, 1, -0.3, 0.3, 0.04, 2.2, false);
  limbs.forEach((l, i) => { follow(l, 0, 0.25, 0.15, 0.06, i); follow(l, 1, -0.25, -0.15, 0.06, i + 2); });

  const torsoR = y => {
    for (let i = 0; i < TORSO.length - 1; i++) {
      const a = TORSO[i], b = TORSO[i + 1];
      if (y <= a[1] && y >= b[1]) { const u = (a[1] - y) / (a[1] - b[1]); return [a[3] + (b[3] - a[3]) * u, a[4] + (b[4] - a[4]) * u]; }
    }
    return [0.15, 0.1];
  };
  for (let y = 0.47, i = 0; y > 0.22; y -= 0.05, i++) {
    const [rx, rz] = torsoR(y);
    for (const s of [1, -1]) {
      const arc = [];
      for (let k = 0; k <= 16; k++) {
        const a = -Math.PI / 2 + (k / 16) * Math.PI * 0.9;
        arc.push([s * Math.cos(a) * rx * 0.8, y - Math.sin((k / 16) * Math.PI) * 0.025, Math.sin(a) * rz * 0.8]);
      }
      line(arc, (i + (s > 0 ? 0 : 1)) % 2);
    }
  }

  for (const s of [1, -1]) {
    line([[0, 0.56, -0.06], [s * 0.08, 0.565, -0.03], [s * 0.16, 0.56, -0.01], [s * 0.205, 0.555, 0.01]], 0);
    line([[0, 0.55, -0.055], [s * 0.08, 0.55, -0.01], [s * 0.16, 0.55, 0.0], [s * 0.2, 0.545, -0.01]], 1);
    line([[0, -0.08, -0.06], [s * 0.04, -0.075, -0.03], [s * 0.085, -0.065, -0.01]], 0);
    line([[0, -0.085, -0.055], [s * 0.04, -0.09, 0.0], [s * 0.08, -0.075, 0.02]], 1);
  }

  line([[0.004, 0.6, -0.035], [0.004, 0.65, -0.032], [0.004, 0.72, -0.02]], 0, 1);
  line([[-0.004, 0.6, -0.035], [-0.004, 0.65, -0.032], [-0.004, 0.72, -0.02]], 1, 1);
  for (let c = 0; c < 6; c++) {
    const arc = [], tilt = rnd() * Math.PI, ph0 = 0.5 + rnd() * 0.8, th0 = rnd() * Math.PI * 2;
    for (let k = 0; k < 40; k++) {
      const th = th0 + k * 0.16, ph = ph0 + Math.sin(k * 0.3 + tilt) * 0.35;
      arc.push([Math.sin(ph) * Math.cos(th) * 0.064, 0.825 + Math.cos(ph) * 0.08, 0.004 + Math.sin(ph) * Math.sin(th) * 0.078]);
    }
    line(arc, c % 2);
  }

  const ORGANS = {
    brain:   { p: [0, 0.83, 0], r: 0.07, label: 'Brain' },
    heart:   { p: [0.035, 0.40, 0.05], r: 0.045, label: 'Heart / QT' },
    liver:   { p: [-0.07, 0.26, 0.045], r: 0.06, label: 'Liver' },
    kidneyL: { p: [0.07, 0.15, -0.045], r: 0.032, label: 'Kidney' },
    kidneyR: { p: [-0.07, 0.15, -0.045], r: 0.032, label: '' },
  };
  const organKeys = Object.keys(ORGANS);
  for (const k of organKeys) ORGANS[k].i = add(...ORGANS[k].p);
  const state = {};
  organKeys.forEach(k => state[k] = { level: 0, focus: 0, target: 0 });
  const alias = { kidneys: ['kidneyL', 'kidneyR'], heart: ['heart'], liver: ['liver'], brain: ['brain'] };

  const G = new Float32Array(pts);
  const N = G.length / 3;
  const S = new Float32Array(N * 3);
  const SMP = Int32Array.from(samples.flatMap(s => [s.ci, s.ni, s.bi]));
  const TUBES = Int32Array.from(tubes.flat());
  const DECO = Int32Array.from(deco);
  const NERVES = Int32Array.from(nerves.flat());
  const pulses = Array.from({ length: 24 }, () => ({ path: mains[(rnd() * mains.length) | 0], t: rnd(), v: 0.05 + rnd() * 0.07 }));
  const maxCount = Math.max(...tubes.map(t => t[1]));
  const edge = new Float32Array(maxCount * 4);
  pts.length = 0; samples.length = 0; deco.length = 0; nerves.length = 0;

  let cv, ctx, W = 0, H = 0, dpr = 1, angle = 0.4, vel = 0, dragging = false, lastX = 0, lastT = 0;
  let speed = 1, tilt = 0.06, raf = 0, visible = true;

  function project() {
    const ca = Math.cos(angle), sa = Math.sin(angle), ct = Math.cos(tilt), st = Math.sin(tilt);
    const scale = H * 0.45, cx = W * 0.5, cy = H * 0.5;
    for (let j = 0; j < N * 3; j += 3) {
      const x = G[j], y = G[j + 1], z = G[j + 2];
      const x1 = x * ca + z * sa, z1 = -x * sa + z * ca;
      const y2 = y * ct - z1 * st, z2 = y * st + z1 * ct;
      const p = 3.5 / (3.5 - z2);
      S[j] = cx + x1 * scale * p; S[j + 1] = cy - y2 * scale * p; S[j + 2] = z2;
    }
  }

  function tubeEdges(t) {
    const first = TUBES[t * 2], count = TUBES[t * 2 + 1];
    for (let i = 0; i < count; i++) {
      const k = (first + i) * 3;
      const c = SMP[k] * 3, n = SMP[k + 1] * 3, b = SMP[k + 2] * 3;
      const pa = SMP[(first + Math.max(0, i - 1)) * 3] * 3, pb = SMP[(first + Math.min(count - 1, i + 1)) * 3] * 3;
      let ax = S[pb] - S[pa], ay = S[pb + 1] - S[pa + 1];
      const l = Math.hypot(ax, ay) || 1; ax /= l; ay /= l;
      const ex = -ay, ey = ax;
      const Nx = S[n] - S[c], Ny = S[n + 1] - S[c + 1], Bx = S[b] - S[c], By = S[b + 1] - S[c + 1];
      const th = Math.atan2(Bx * ex + By * ey, Nx * ex + Ny * ey), cs = Math.cos(th), sn = Math.sin(th);
      const vx = Nx * cs + Bx * sn, vy = Ny * cs + By * sn, o = i * 4;
      edge[o] = S[c] - vx; edge[o + 1] = S[c + 1] - vy; edge[o + 2] = S[c] + vx; edge[o + 3] = S[c + 1] + vy;
    }
    return count;
  }

  function tracePolygon(count) {
    const px = i => i < count ? edge[i * 4 + 2] : edge[(2 * count - 1 - i) * 4];
    const py = i => i < count ? edge[i * 4 + 3] : edge[(2 * count - 1 - i) * 4 + 1];
    const M = count * 2;
    ctx.moveTo((px(M - 1) + px(0)) / 2, (py(M - 1) + py(0)) / 2);
    for (let i = 0; i < M; i++) {
      const j = (i + 1) % M;
      ctx.quadraticCurveTo(px(i), py(i), (px(i) + px(j)) / 2, (py(i) + py(j)) / 2);
    }
    ctx.closePath();
  }

  function drawOutline() {
    const T = TUBES.length / 2;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.beginPath();
    for (let t = 0; t < T; t++) tracePolygon(tubeEdges(t));

    ctx.strokeStyle = 'rgba(247,198,217,0.10)'; ctx.lineWidth = 22; ctx.stroke();
    ctx.strokeStyle = 'rgba(247,198,217,0.28)'; ctx.lineWidth = 8; ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,1)'; ctx.lineWidth = 3; ctx.stroke();

    ctx.globalCompositeOperation = 'destination-out';
    ctx.fillStyle = '#000';
    for (let t = 0; t < T; t++) { ctx.beginPath(); tracePolygon(tubeEdges(t)); ctx.fill(); }

    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = 'rgba(255,255,255,0.025)';
    for (let t = 0; t < T; t++) { ctx.beginPath(); tracePolygon(tubeEdges(t)); ctx.fill(); }
  }

  function drawRings() {
    for (let pass = 0; pass < 2; pass++) {
      ctx.beginPath();
      for (let r = 0; r < DECO.length; r++) {
        const p0 = DECO[r];
        for (let j = 0; j < RING; j++) {
          const a = (p0 + j) * 3, b = (p0 + (j + 1) % RING) * 3;
          if ((S[a + 2] + S[b + 2] > 0) !== !!pass) continue;
          ctx.moveTo(S[a], S[a + 1]); ctx.lineTo(S[b], S[b + 1]);
        }
      }
      ctx.strokeStyle = pass ? 'rgba(255,255,255,0.07)' : 'rgba(255,255,255,0.025)';
      ctx.lineWidth = 1; ctx.stroke();
    }
  }

  const COL = ['255,90,122', '143,216,255'];
  function drawNerves() {
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    for (let c = 0; c < 2; c++) {
      for (let pass = 0; pass < 2; pass++) {
        ctx.beginPath();
        for (let n = 0; n < NERVES.length; n += 4) {
          if (NERVES[n + 2] !== c) continue;
          const s = NERVES[n], len = NERVES[n + 1];
          let pen = false;
          for (let k = 0; k < len; k++) {
            const q = (s + k) * 3, front = S[q + 2] > -0.02;
            if (front !== !!pass) { pen = false; continue; }
            pen ? ctx.lineTo(S[q], S[q + 1]) : ctx.moveTo(S[q], S[q + 1]);
            pen = true;
          }
        }
        const a = pass ? 1 : 0.35;
        ctx.strokeStyle = `rgba(${COL[c]},${0.16 * a})`; ctx.lineWidth = 5; ctx.stroke();
        ctx.strokeStyle = `rgba(${COL[c]},${0.85 * a})`; ctx.lineWidth = pass ? 1.4 : 1; ctx.stroke();
      }
    }
  }

  function dot(x, y, r, rgb, a) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(255,255,255,${a})`);
    g.addColorStop(0.35, `rgba(${rgb},${a * 0.7})`);
    g.addColorStop(1, `rgba(${rgb},0)`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
  }

  function drawPulses(dt) {
    for (const p of pulses) {
      p.t = (p.t + p.v * dt * speed) % 1;
      const n = p.path * 4, s = NERVES[n], len = NERVES[n + 1];
      const q = (s + Math.floor(p.t * (len - 1))) * 3;
      dot(S[q], S[q + 1], 7, COL[NERVES[n + 2]], S[q + 2] > 0 ? 0.9 : 0.35);
    }
  }

  const LVL = ['247,198,217', '255,210,138', '255,90,122'];
  function drawOrgans(time) {
    const scale = H * 0.45;
    ctx.font = '500 12px "Bricolage Grotesque", system-ui, sans-serif';
    for (const k of organKeys) {
      const o = ORGANS[k], st = state[k], q = o.i * 3;
      st.focus += (st.target - st.focus) * 0.12;
      const beat = st.level ? 0.5 + 0.5 * Math.sin(time * 0.006) : 0;
      const a = 0.3 + 0.5 * st.focus + 0.45 * (st.level > 0) + 0.2 * beat;
      const r = o.r * scale * (1.1 + 0.6 * st.focus + 0.3 * (st.level > 0) + 0.2 * beat);
      const lit = st.focus > 0.3 || st.level > 0;
      dot(S[q], S[q + 1], r, LVL[st.level], Math.min(a, 1) * (lit || S[q + 2] > -0.03 ? 1 : 0.55));
      if (lit) dot(S[q], S[q + 1], r * 0.45, LVL[st.level], 0.9);
      if (lit && o.label) {
        ctx.fillStyle = `rgba(255,255,255,${Math.max(st.focus, st.level ? 0.85 : 0)})`;
        const side = S[q] > W / 2 ? 1 : -1;
        ctx.textAlign = side > 0 ? 'left' : 'right';
        ctx.fillText(o.label, S[q] + side * (r + 6), S[q + 1] + 4);
      }
    }
  }

  function frame(now) {
    const dt = Math.min((now - (lastT || now)) / 1000, 0.05); lastT = now;
    if (!dragging) { vel += (0.35 * speed - vel) * 0.02; angle += vel * dt; }
    project();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.clearRect(0, 0, W, H);
    drawOutline();
    ctx.globalCompositeOperation = 'lighter';
    drawRings(); drawNerves(); drawPulses(dt); drawOrgans(now);
    ctx.globalCompositeOperation = 'source-over';
    raf = visible ? requestAnimationFrame(frame) : 0;
  }

  function resize() {
    const r = cv.getBoundingClientRect();
    dpr = Math.min(devicePixelRatio || 1, 2);
    W = r.width; H = r.height;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
  }

  function init(canvas) {
    cv = canvas; ctx = cv.getContext('2d');
    resize();
    new ResizeObserver(resize).observe(cv);
    new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible && !raf) { lastT = 0; raf = requestAnimationFrame(frame); }
    }).observe(cv);
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) speed = 0.25;
    cv.addEventListener('pointerdown', e => { dragging = true; lastX = e.clientX; cv.setPointerCapture(e.pointerId); cv.classList.add('drag'); });
    cv.addEventListener('pointermove', e => {
      if (!dragging) return;
      const d = (e.clientX - lastX) * 0.01; lastX = e.clientX; angle += d; vel = d * 30;
    });
    const up = () => { dragging = false; cv.classList.remove('drag'); };
    cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
    raf = requestAnimationFrame(frame);
  }

  const keys = name => alias[name] || [];
  return {
    init,
    focus(name) { organKeys.forEach(k => state[k].target = 0); keys(name).forEach(k => state[k].target = 1); },
    setOrgan(name, level) { keys(name).forEach(k => state[k].level = level); },
    clearOrgans() { organKeys.forEach(k => state[k].level = 0); },
    setSpeed(s) { speed = s; },
    stats: () => ({ points: N, bytes: G.byteLength + S.byteLength + SMP.byteLength + TUBES.byteLength + DECO.byteLength + NERVES.byteLength + edge.byteLength }),
  };
})();
