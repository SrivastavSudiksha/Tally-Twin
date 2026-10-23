(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const form = $('#twin-form');

  const API_BASE = (typeof window.DT_API_URL === 'string' && window.DT_API_URL)
    ? window.DT_API_URL.replace(/\/+$/, '')
    : '';
  const API_KEY = (typeof window.DT_API_KEY === 'string' && window.DT_API_KEY)
    ? window.DT_API_KEY
    : (typeof localStorage !== 'undefined' ? (localStorage.getItem('DT_API_KEY') || '') : '');
  function apiHeaders(json) {
    const h = {};
    if (json) h['Content-Type'] = 'application/json';
    if (API_KEY) h['X-API-Key'] = API_KEY;
    return h;
  }
  function requireApiKeyOrThrow() {
    if (!API_KEY) {
      throw new Error(
        'No API key configured. Set localStorage.setItem("DT_API_KEY", "your-key") ' +
        'or window.DT_API_KEY before running a simulation.'
      );
    }
  }
  const SIM_URL = (API_BASE || '') + '/api/v1/simulations/run';
  const COMP_OCR_URL = (API_BASE || '') + '/api/v1/drugs/composition-from-image';

  const F = n => form.elements[n];
  const num = n => { const v = parseFloat(F(n)?.value); return Number.isFinite(v) ? v : null; };

  Body.init($('#body-canvas'));

  const tabs = $$('[role=tab]', form), ink = $('.tab-ink', form);
  function selectTab(id) {
    tabs.forEach(t => {
      const on = t.id === id;
      t.setAttribute('aria-selected', on);
      $('#' + t.getAttribute('aria-controls')).hidden = !on;
      if (on) { ink.style.left = t.offsetLeft + 'px'; ink.style.width = t.offsetWidth + 'px'; }
    });
    Body.focus(id === 't-drug' ? 'none' : '');
  }
  tabs.forEach(t => t.addEventListener('click', () => selectTab(t.id)));
  $('#to-drug').onclick = () => selectTab('t-drug');
  $('#to-patient').onclick = () => selectTab('t-patient');
  addEventListener('preloader:done', () => selectTab('t-patient'));
  requestAnimationFrame(() => selectTab('t-patient'));

  const PHENO = ['Unknown', 'Poor', 'Intermediate', 'Normal', 'Rapid', 'Ultrarapid'];
  ['cyp2d6', 'cyp2c19', 'cyp2c9'].forEach(n => F(n).innerHTML = PHENO.map(p => `<option value="${p.toLowerCase()}">${p}</option>`).join(''));

const star = () => Object.assign(document.createElement('span'), { className: 'req', textContent: '*', ariaHidden: 'true' });
$$('[required], [name=egfr]', form).forEach(el => {
  const label = el.closest('label');
  const text = label && [...label.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
  if (!text) return;
  const wrap = document.createElement('span');
  wrap.textContent = text.textContent.trim();
  wrap.append(star());
  text.replaceWith(wrap);
});

const DRUG_PH = { name: 'e.g. ibuprofen', smiles: 'e.g. CC(C)Cc1ccc(cc1)C(C)C(=O)O' };
$$('input[name=idMode]', form).forEach(r => r.addEventListener('change', () => {
  F('drug').placeholder = DRUG_PH[r.value];
  F('drug').value = '';
}));

  const compRows = $('#comp-rows');
  const compStatus = $('#comp-status');
  const compImage = $('#comp-image');

  function addCompRow(v = {}) {
    const row = document.createElement('div');
    row.className = 'comp-row';
    row.innerHTML = `<input placeholder="Ingredient name" aria-label="Ingredient name" value="${esc(v.name || '')}">
      <input placeholder="e.g. 400" aria-label="Strength" type="text" inputmode="decimal" value="${esc(v.strength || '')}">
      <input placeholder="mg" aria-label="Unit" value="${esc(v.unit || 'mg')}">
      <button type="button" class="icon-btn" aria-label="Remove ingredient">×</button>`;
    row.lastElementChild.onclick = () => {
      row.remove();
      if (!compRows.children.length) addCompRow();
      syncCompositionHidden();
    };
    $$('input', row).forEach(inp => inp.addEventListener('input', syncCompositionHidden));
    compRows.append(row);
    syncCompositionHidden();
    return row;
  }

  function getCompositionRows() {
    return $$('.comp-row', compRows).map(r => {
      const [n, s, u] = $$('input', r);
      return {
        name: (n.value || '').trim(),
        strength: (s.value || '').trim(),
        unit: (u.value || '').trim() || 'mg',
      };
    }).filter(x => x.name);
  }

  function compositionToText(rows) {
    return rows.map(r => {
      if (r.strength) return `${r.name} ${r.strength} ${r.unit}`.trim();
      return r.name;
    }).join(', ');
  }

  function syncCompositionHidden() {
    const rows = getCompositionRows();
    const hidden = $('#composition-hidden') || F('composition');
    if (hidden) hidden.value = compositionToText(rows);
  }

  function parseCompositionText(text) {

    const parts = String(text || '').split(/[,;\n]+/).map(s => s.trim()).filter(Boolean);
    const rows = [];
    for (const p of parts) {
      const m = p.match(/^(.+?)\s+(\d+(?:\.\d+)?)\s*(mg|g|mcg|µg|%|ml|mL)?$/i);
      if (m) rows.push({ name: m[1].trim(), strength: m[2], unit: (m[3] || 'mg') });
      else rows.push({ name: p, strength: '', unit: 'mg' });
    }
    return rows.length ? rows : [{ name: text.trim(), strength: '', unit: 'mg' }];
  }

  function setCompositionRows(rows) {
    compRows.innerHTML = '';
    (rows && rows.length ? rows : [{}]).forEach(addCompRow);
    syncCompositionHidden();
  }

  $('#add-comp').onclick = () => addCompRow().querySelector('input').focus();
  addCompRow();

  if (compImage) {
    compImage.addEventListener('change', async () => {
      const file = compImage.files && compImage.files[0];
      if (!file) return;
      if (compStatus) { compStatus.hidden = false; compStatus.textContent = 'Reading image…'; }
      try {
        const fd = new FormData();
        fd.append('file', file);
        const r = await fetch(COMP_OCR_URL, { method: 'POST', body: fd });
        if (r.ok) {
          const data = await r.json();
          if (data.composition) {
            setCompositionRows(parseCompositionText(data.composition));
            if (compStatus) compStatus.textContent = data.source === 'ocr'
              ? 'Composition rows filled from image — review and edit.'
              : 'Suggestion applied — review the table.';
          } else if (compStatus) {
            compStatus.textContent = data.message || 'No text detected. Add ingredients in the table.';
          }
        } else if (compStatus) {
          compStatus.textContent = 'Could not read image. Add ingredients in the table.';
        }
      } catch (err) {
        if (compStatus) compStatus.textContent = 'OCR unavailable — add ingredients in the table.';
      }
    });
  }

  const egfrCalc = (scr, age, sex) => {
    if (!scr || !age || !sex) return null;
    const f = sex === 'F', k = f ? 0.7 : 0.9, a = f ? -0.241 : -0.302;
    return 142 * Math.min(scr / k, 1) ** a * Math.max(scr / k, 1) ** -1.2 * 0.9938 ** age * (f ? 1.012 : 1);
  };
  const getEgfr = () => F('kidneyMode').value === 'egfr' ? num('egfr') : egfrCalc(num('creatinine'), num('age'), F('sex').value);
  function updateDerived() {
    const w = num('weight'), h = num('height');
    form.elements.bmi.value = w && h ? (w / (h / 100) ** 2).toFixed(1) : '–';
    const e = getEgfr();
    form.elements.egfrOut.value = e ? Math.round(e) + ' mL/min/1.73m²' : '–';
    const preg = $('input[value=pregnancy]', form);
    preg.disabled = F('sex').value === 'M';
    if (preg.disabled) preg.checked = false;
  }
  form.addEventListener('input', updateDerived);
  $$('input[name=kidneyMode]', form).forEach(r => r.addEventListener('change', () => {
    const e = r.value === 'egfr' && r.checked;
    $('.k-scr', form).hidden = e; $('.k-egfr', form).hidden = !e;
    F('creatinine').required = !e; F('egfr').required = e;
    updateDerived();
  }));

  form.addEventListener('focusin', e => {
    const box = e.target.closest('[data-organ]');
    $$('fieldset.lit', form).forEach(f => f.classList.remove('lit'));
    if (box && box.tagName === 'FIELDSET') box.classList.add('lit');
    Body.focus(box ? box.dataset.organ : '');
  });

  const meds = $('#meds');
  function addMed(v = {}) {
    const row = document.createElement('div');
    row.className = 'med';
    row.innerHTML = `<input placeholder="Medicine name" aria-label="Medicine name" value="${esc(v.name || '')}">
      <input placeholder="Dose (mg)" aria-label="Dose in mg" type="number" min="0" step="any" value="${esc(v.dose || '')}">
      <input placeholder="Times/day" aria-label="Times per day" type="number" min="1" max="12" value="${esc(v.freq || '')}">
      <button type="button" class="icon-btn" aria-label="Remove medicine">×</button>`;
    row.lastElementChild.onclick = () => row.remove();
    meds.append(row);
    return row;
  }
  $('#add-med').onclick = () => addMed().firstElementChild.focus();
  addMed();

  const tagBox = $('#allergy-tags'), tagInput = $('#allergy-input'), allergies = new Set();
  function renderTags() {
    $$('.tag', tagBox).forEach(t => t.remove());
    allergies.forEach(a => {
      const t = document.createElement('span');
      t.className = 'tag';
      t.innerHTML = `${esc(a)}<button type="button" aria-label="Remove ${esc(a)}">×</button>`;
      t.lastChild.onclick = () => { allergies.delete(a); renderTags(); };
      tagBox.insertBefore(t, tagInput);
    });
  }
  tagInput.addEventListener('keydown', e => {
    if ((e.key === 'Enter' || e.key === ',') && tagInput.value.trim()) {
      e.preventDefault(); allergies.add(tagInput.value.trim().toLowerCase()); tagInput.value = ''; renderTags();
    } else if (e.key === 'Backspace' && !tagInput.value && allergies.size) {
      allergies.delete([...allergies].pop()); renderTags();
    }
  });

const condBoxes = $$('input[name=conditions]', form);
condBoxes.forEach(cb => cb.addEventListener('change', () => {
  if (!cb.checked) return;
  if (cb.value === 'none') condBoxes.forEach(o => { if (o !== cb) o.checked = false; });
  else condBoxes.find(o => o.value === 'none').checked = false;
}));

  function buildPayload() {
    if (tagInput.value.trim()) { allergies.add(tagInput.value.trim().toLowerCase()); tagInput.value = ''; renderTags(); }
    return {
      patient: {
        age: num('age'), sex: F('sex').value, weight_kg: num('weight'), height_cm: num('height'),
        bmi: parseFloat(form.elements.bmi.value) || null,
        kidney: { creatinine_mg_dl: F('kidneyMode').value === 'scr' ? num('creatinine') : null, egfr: getEgfr() },
        liver: { alt: num('alt'), ast: num('ast'), bilirubin: num('bilirubin'), albumin: num('albumin') },
        conditions: $$('input[name=conditions]:checked', form).map(c => c.value).filter(v => v !== 'none'),
        medicines: $$('.med', meds).map(r => { const [n, d, f] = $$('input', r); return { name: n.value.trim(), dose_mg: parseFloat(d.value) || null, per_day: parseInt(f.value) || null }; }).filter(m => m.name),
        allergies: [...allergies],
        lifestyle: { smoking: F('smoking').value, alcohol: F('alcohol').value },
        genetics: { cyp2d6: F('cyp2d6').value, cyp2c19: F('cyp2c19').value, cyp2c9: F('cyp2c9').value },
        qtc_ms: num('qtc'),
      },
      drug: {
        identifier: F('drug').value.trim(), identifier_type: F('idMode').value,
        dose_mg: num('dose'), route: F('route').value, per_day: num('freq'), duration_days: num('duration'),
        composition_rows: getCompositionRows(),
        composition: compositionToText(getCompositionRows()) || null,
      },
    };
  }

  function validate(p) {
    $$('[aria-invalid]', form).forEach(el => el.removeAttribute('aria-invalid'));
    const bad = [];
    const need = ['age', 'sex', 'weight', 'alt', 'ast', F('kidneyMode').value === 'scr' ? 'creatinine' : 'egfr', 'drug', 'dose', 'freq', 'duration'];
    need.forEach(n => { if (!F(n).value || !F(n).checkValidity()) { F(n).setAttribute('aria-invalid', 'true'); bad.push(n); } });
    if (!p.drug.composition_rows || !p.drug.composition_rows.length) {
      bad.push('composition');
      $$('.comp-row input', form).forEach(el => el.setAttribute('aria-invalid', 'true'));
    }
    if (!p.patient.medicines.length && !F('noMeds').checked) bad.push('medicines');
    if (!p.patient.allergies.length && !F('noAllergies').checked) bad.push('allergies');
    return bad;
  }
  const NAMES = { age: 'age', sex: 'sex', weight: 'weight', alt: 'ALT', ast: 'AST', creatinine: 'creatinine', egfr: 'eGFR', drug: 'drug', composition: 'composition (ingredients / strength)', dose: 'dose', freq: 'frequency', duration: 'duration', medicines: 'current medicines (or tick "Takes no medicines")', allergies: 'allergies (or tick "No known allergies")' };

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const p = buildPayload(), bad = validate(p), err = $('.form-error', form);
    if (bad.length) {
      err.hidden = false;
      err.textContent = 'Fill in ' + bad.map(b => NAMES[b]).join(', ') + ' to run the simulation.';
      const patientSide = bad.some(b => !['drug', 'dose', 'freq', 'duration'].includes(b));
      selectTab(patientSide ? 't-patient' : 't-drug');
      return;
    }
    err.hidden = true;
    Body.setSpeed(4);
    try {
      let report;
      try {
        requireApiKeyOrThrow();
        const backendBody = toBackendPayload(p);
        const r = await fetch(SIM_URL + '?persist=true', {
          method: 'POST',
          headers: apiHeaders(true),
          body: JSON.stringify(backendBody),
        });
        if (!r.ok) throw new Error(r.status + ' ' + (await r.text().catch(() => '')));
        const data = await r.json();

        const raw = data.report || data;
        window.__lastSimId = data.simulation_id || null;
        report = fromBackendReport(raw, p);
      } catch (apiErr) {
        console.warn('API unavailable:', apiErr);
        const allowDemo = (typeof window.DT_ALLOW_DEMO === 'boolean')
          ? window.DT_ALLOW_DEMO
          : (typeof localStorage !== 'undefined' && localStorage.getItem('DT_ALLOW_DEMO') === 'true');
        if (!allowDemo) {
          throw new Error(
            'API unavailable (' + (apiErr && apiErr.message ? apiErr.message : apiErr) +
            '). Demo mode is off. Set localStorage DT_API_KEY and ensure the backend is running, ' +
            'or set localStorage DT_ALLOW_DEMO=true only for non-clinical demos.'
          );
        }
        console.warn('Using DEMO model — not for clinical use');
        report = await new Promise(res => setTimeout(() => res(demoReport(p)), 700));
      }
      renderReport(report, p);
    } catch (x) {
      err.hidden = false; err.textContent = `The simulation service did not respond (${x.message}). Check API URL and try again.`;
    } finally { Body.setSpeed(1); }
  });

  function toBackendPayload(p) {
    const P = p.patient, D = p.drug;
    const freqMap = { 1: 'OD', 2: 'BD', 3: 'TDS', 4: 'QID' };
    const per = D.per_day || 1;
    const frequency = freqMap[per] || ('every ' + Math.round(24 / per) + ' hours');
    const sex = P.sex === 'F' ? 'female' : P.sex === 'M' ? 'male' : 'other';
    const smoke = (P.lifestyle && P.lifestyle.smoking) || 'never';
    const alcohol = (P.lifestyle && P.lifestyle.alcohol) || 'none';
    return {
      patient: {
        age: P.age,
        sex,
        weight_kg: P.weight_kg,
        height_cm: P.height_cm || null,
        serum_creatinine: P.kidney && P.kidney.creatinine_mg_dl != null ? P.kidney.creatinine_mg_dl : null,
        egfr: P.kidney && P.kidney.egfr != null ? P.kidney.egfr : null,
        alt: P.liver && P.liver.alt != null ? P.liver.alt : null,
        ast: P.liver && P.liver.ast != null ? P.liver.ast : null,
        bilirubin: P.liver && P.liver.bilirubin != null ? P.liver.bilirubin : null,
        albumin: P.liver && P.liver.albumin != null ? P.liver.albumin : null,
        conditions: P.conditions || [],
        current_medicines: (P.medicines || []).map(m => ({
          name: m.name,
          dose_mg: m.dose_mg || 1,
          frequency: freqMap[m.per_day] || (m.per_day ? String(m.per_day) + 'x daily' : 'OD'),
        })),
        allergies: P.allergies || [],
        smoking: smoke === 'current',
        alcohol: alcohol === 'heavy' ? 'heavy' : alcohol === 'moderate' ? 'moderate' : 'none',
        cyp2d6: P.genetics && P.genetics.cyp2d6 !== 'unknown' ? P.genetics.cyp2d6 : null,
        cyp2c19: P.genetics && P.genetics.cyp2c19 !== 'unknown' ? P.genetics.cyp2c19 : null,
        cyp2c9: P.genetics && P.genetics.cyp2c9 !== 'unknown' ? P.genetics.cyp2c9 : null,
        qtc_ms: P.qtc_ms || null,
      },
      drug: {
        identifier: D.identifier,
        dose_mg: D.dose_mg,
        route: D.route === 'iv' ? 'iv' : 'oral',
        frequency,
        duration_days: D.duration_days || 1,
        composition: D.composition || null,
        composition_rows: D.composition_rows || null,
      },
    };
  }

  function fromBackendReport(r, p) {
    const riskMap = { 'Safe': 'safe', 'Caution': 'caution', 'High Risk': 'high' };
    const confMap = { 'High': 'high', 'Medium': 'medium', 'Low': 'low' };
    const pk = r.pharmacokinetic_results || {};
    const mp = pk.metrics_patient || {};
    const curve = (arr) => (arr || []).map(pt => pt.concentration);
    const dt = 0.5;
    const organs = { kidneys: 0, liver: 0, heart: 0 };
    (r.organ_flags || []).forEach(f => {
      const lv = f.risk_level === 'high' ? 2 : f.risk_level === 'moderate' ? 1 : 0;
      const o = (f.organ || '').toLowerCase();
      if (o.includes('kidney')) organs.kidneys = Math.max(organs.kidneys, lv);
      else if (o.includes('liver')) organs.liver = Math.max(organs.liver, lv);
      else if (o.includes('heart') || o.includes('qt')) organs.heart = Math.max(organs.heart, lv);
    });
    const doseVerdict = (r.dose_assessment && r.dose_assessment.standard_dose_assessment) || 'appropriate';
    const dose = {
      verdict: doseVerdict === 'too_high' ? 'higher' : doseVerdict === 'too_low' ? 'lower' : 'ok',
      text: (r.dose_assessment && r.dose_assessment.rationale) || (r.dose_assessment && r.dose_assessment.suggested_adjustment_range) || '',
      range: null,
    };
    const ddi = (r.drug_drug_interactions || []).map(i => ({
      med: i.interacting_drug,
      type: i.interaction_type,
      severity: i.severity,
      mechanism: i.mechanism,
    }));
    if (!ddi.length && (p.patient.medicines || []).length) {
      p.patient.medicines.forEach(m => ddi.push({ med: m.name, type: '–', severity: 'Not assessed', mechanism: 'No rule matched' }));
    }
    const adverse = (r.adverse_effects || []).map(a => ({ name: a.effect, p: a.probability }));
    const contra = (r.contraindications || []).map(c => ({
      text: c.message || c.matched_item,
      severity: c.severity === 'contraindicated' ? 2 : 1,
    }));
    const params = ((r.explainability && r.explainability.top_patient_parameters) || []).map(x => ({
      name: x.param || x.name,
      weight: x.impact != null ? x.impact : (x.weight || 0),
    }));
    const confItems = Object.entries((r.confidence_and_quality && r.confidence_and_quality.per_prediction_scores) || {}).map(([n, s]) => [n, s]);
    const mol = (r.drug_profile && r.drug_profile.molecular_properties) || {};
    const dp = r.drug_profile || {};
    const drug = {
      mw: mol.molecular_weight != null ? mol.molecular_weight + ' g/mol' : '–',
      logP: mol.logp != null ? String(mol.logp) : '–',
      solubility: mol.tpsa != null ? 'TPSA ' + mol.tpsa : '–',
      targets: (dp.known_targets || []).join(', ') || '–',
      pathway: (dp.metabolism_pathways || []).join(', ') || '–',
      cyps: (dp.cyp_enzymes || []).join(', ') || '–',
      composition: (p.drug && p.drug.composition) || null,
    };
    const pp = r.patient_profile || {};
    return {
      demo: false,
      summary: {
        risk: riskMap[r.risk_level] || 'caution',
        confidence: confMap[r.overall_confidence] || 'medium',
      },
      patient: {
        rows: [
          ['Age', (pp.age || p.patient.age) + ' y'],
          ['Sex', (pp.sex || p.patient.sex) === 'female' || p.patient.sex === 'F' ? 'Female' : 'Male'],
          ['Weight', (pp.weight_kg || p.patient.weight_kg) + ' kg'],
          ['BMI', pp.bmi != null ? pp.bmi : (p.patient.bmi ?? '–')],
          ['ALT / AST', `${pp.alt ?? p.patient.liver?.alt ?? '–'} / ${pp.ast ?? p.patient.liver?.ast ?? '–'} U/L`],
          ['Medicines', (p.patient.medicines || []).length || 'None'],
          ['Allergies', (p.patient.allergies || []).join(', ') || 'None'],
        ],
        derived: [
          ['Clearance factor', String(pp.clearance_adjustment_factor ?? '–')],
          ['eGFR category', `${pp.egfr != null ? Math.round(pp.egfr) : '–'} · ${pp.egfr_category || ''}`],
          ['Liver capacity', pp.liver_capacity_score != null ? Math.round(pp.liver_capacity_score * 100) + '% of normal' : '–'],
        ],
      },
      drug,
      pk: {
        dt,
        avg: curve(pk.average_person_curve),
        patient: curve(pk.patient_curve),
        mec: pk.therapeutic_window_low || 0,
        toxic: pk.toxic_threshold || (mp.cmax ? mp.cmax * 1.8 : 1),
        cmax: mp.cmax || 0,
        tmax: mp.tmax_h || 0,
        thalf: mp.half_life_h || 0,
        auc: mp.auc || 0,
        accumulation: mp.accumulation_factor || 1,
      },
      dose,
      ddi,
      adverse: adverse.length ? adverse : null,
      organs,
      contraindications: contra,
      explain: {
        params: params.length ? params : [{ name: 'Model defaults', weight: 1 }],
        substructures: null,
      },
      confidence: {
        items: confItems.length ? confItems : [['Overall', 0.7]],
        warning: ((r.confidence_and_quality && r.confidence_and_quality.data_quality_warnings) || []).join(' ') || null,
      },
    };
  }

  const NSAIDS = ['ibuprofen', 'naproxen', 'diclofenac', 'ketorolac', 'indomethacin', 'celecoxib', 'aspirin', 'meloxicam'];
  const DDI_RULES = [
    [['warfarin'], NSAIDS, 'Pharmacodynamic', 'Major', 'Additive bleeding risk'],
    [['clopidogrel'], ['omeprazole', 'esomeprazole'], 'Metabolic (CYP2C19)', 'Moderate', 'Reduced activation of clopidogrel'],
    [['simvastatin', 'atorvastatin'], ['clarithromycin', 'itraconazole', 'ketoconazole'], 'Metabolic (CYP3A4)', 'Major', 'Raised statin levels, myopathy risk'],
    [['metformin'], ['cimetidine'], 'Transporter (OCT2)', 'Minor', 'Reduced renal clearance of metformin'],
  ];
  function demoReport(p) {
    const P = p.patient, D = p.drug, name = D.identifier.toLowerCase();
    const egfr = P.kidney.egfr || 90;

    let liver = 1; const uln = 40, worst = Math.max(P.liver.alt || 0, P.liver.ast || 0) / uln;
    if (worst > 5) liver *= 0.5; else if (worst > 3) liver *= 0.7; else if (worst > 1.5) liver *= 0.9;
    if (P.liver.bilirubin > 3) liver *= 0.6; else if (P.liver.bilirubin > 1.2) liver *= 0.85;
    if (P.liver.albumin && P.liver.albumin < 3.5) liver *= 0.9;
    if (P.conditions.includes('liver')) liver *= 0.8;
    if (P.lifestyle.alcohol === 'heavy') liver *= 0.9;

    const base = { vdkg: 0.7, th: 6, F: D.route === 'iv' ? 1 : 0.8, ka: 1.2 };
    const Vavg = base.vdkg * 70, CLavg = (Math.LN2 / base.th) * Vavg;
    const renal = Math.min(egfr, 120) / 100, size = (P.weight_kg / 70) ** 0.75;
    const CLp = CLavg * size * (0.5 * renal + 0.5 * liver), Vp = base.vdkg * P.weight_kg;
    const tau = 24 / D.per_day, hours = Math.min(D.duration_days * 24, 96), dt = 0.25;
    const curve = (CL, V) => {
      const k = CL / V, out = new Float32Array(Math.floor(hours / dt) + 1);
      for (let i = 0; i < out.length; i++) {
        const t = i * dt; let c = 0;
        for (let td = 0; td <= t && td < D.duration_days * 24; td += tau) {
          const s = t - td;
          c += D.route === 'iv' ? (D.dose_mg / V) * Math.exp(-k * s)
            : (base.F * D.dose_mg * base.ka / (V * (base.ka - k))) * (Math.exp(-k * s) - Math.exp(-base.ka * s));
        }
        out[i] = c;
      }
      return out;
    };
    const avg = curve(CLavg, Vavg), pat = curve(CLp, Vp);
    let cmax = 0, tmax = 0, c1 = 0; pat.forEach((c, i) => { if (c > cmax) cmax = c; if (i * dt < tau && c > c1) { c1 = c; tmax = i * dt; } });
    const avgMax = Math.max(...avg), cssAvg = base.F * D.dose_mg / (CLavg * tau);
    const mec = 0.5 * cssAvg, toxic = 1.5 * avgMax;
    let auc = 0; const n24 = Math.min(pat.length - 1, 24 / dt);
    for (let i = 0; i < n24; i++) auc += (pat[i] + pat[i + 1]) * dt / 2;
    const kp = CLp / Vp, accum = 1 / (1 - Math.exp(-kp * tau)), ratio = CLavg / CLp;

    let dose;
    if (ratio > 1.25) dose = { verdict: 'higher', text: 'The standard dose is higher than this patient needs.', range: [D.dose_mg / ratio * 0.9, D.dose_mg / ratio * 1.1] };
    else if (ratio < 0.8) dose = { verdict: 'lower', text: 'The standard dose is lower than this patient needs.', range: [D.dose_mg / ratio * 0.9, D.dose_mg / ratio * 1.1] };
    else dose = { verdict: 'ok', text: 'The standard dose looks appropriate for this patient.', range: null };

    const qtcLimit = P.sex === 'F' ? 470 : 450;
    const organs = {
      kidneys: egfr < 30 ? 2 : egfr < 60 ? 1 : 0,
      liver: worst > 5 || P.liver.bilirubin > 3 ? 2 : worst > 3 || liver < 0.8 ? 1 : 0,
      heart: P.qtc_ms > 500 ? 2 : (P.qtc_ms > qtcLimit || P.conditions.includes('heart')) ? 1 : 0,
    };

    const contra = [];
    P.allergies.forEach(a => {
      const hit = name.includes(a) || a.includes(name) || (a.includes('penicillin') && /cillin$/.test(name)) || (a.includes('sulfa') && name.startsWith('sulfa')) || (a.includes('nsaid') && NSAIDS.includes(name));
      if (hit) contra.push({ text: `Allergy match: ${a}`, severity: 2 });
    });
    const isNsaid = NSAIDS.includes(name);
    if (isNsaid && (P.conditions.includes('kidney') || egfr < 30)) contra.push({ text: 'NSAID with kidney disease or eGFR below 30', severity: 2 });
    if (isNsaid && P.conditions.includes('heart')) contra.push({ text: 'NSAID with heart disease: fluid retention and CV risk', severity: 1 });
    if (P.conditions.includes('pregnancy') && (isNsaid || name === 'warfarin' || /pril$/.test(name) || /sartan$/.test(name))) contra.push({ text: 'Avoid in pregnancy', severity: 2 });
    if (name === 'metformin' && egfr < 30) contra.push({ text: 'Metformin is contraindicated below eGFR 30', severity: 2 });

    const ddi = P.medicines.map(m => {
      const mn = m.name.toLowerCase();
      const r = DDI_RULES.find(([a, b]) => (a.includes(name) && b.includes(mn)) || (b.includes(name) && a.includes(mn)));
      return r ? { med: m.name, type: r[2], severity: r[3], mechanism: r[4] } : { med: m.name, type: '–', severity: 'Not assessed', mechanism: 'Needs the interaction model' };
    });

    const sev = Math.max(...Object.values(organs), ...contra.map(c => c.severity), 0);
    const risk = sev === 2 || cmax > toxic || ratio > 1.6 ? 'high' : sev === 1 || ratio > 1.25 || ratio < 0.8 ? 'caution' : 'safe';
    const lr = v => Math.abs(Math.log(v || 1));
    const contrib = [['Kidney function', lr(0.5 * renal + 0.5)], ['Liver capacity', lr(0.5 + 0.5 * liver)], ['Body weight', lr(size)], ['Age', lr(P.age > 65 ? 0.9 : 1)]];
    const tot = contrib.reduce((s, c) => s + c[1], 0) || 1;
    const stage = egfr >= 90 ? 'G1 normal' : egfr >= 60 ? 'G2 mildly reduced' : egfr >= 45 ? 'G3a' : egfr >= 30 ? 'G3b' : egfr >= 15 ? 'G4 severe' : 'G5 failure';
    return {
      demo: true,
      summary: { risk, confidence: 'low' },
      patient: {
        rows: [['Age', P.age + ' y'], ['Sex', P.sex === 'F' ? 'Female' : 'Male'], ['Weight', P.weight_kg + ' kg'], ['BMI', P.bmi ?? '–'], ['ALT / AST', `${P.liver.alt} / ${P.liver.ast} U/L`], ['Medicines', P.medicines.length || 'None'], ['Allergies', P.allergies.join(', ') || 'None']],
        derived: [['Clearance', `${CLp.toFixed(1)} L/h (avg ${CLavg.toFixed(1)})`], ['eGFR category', `${Math.round(egfr)} · ${stage}`], ['Liver capacity', `${Math.round(liver * 100)}% of normal`]],
      },
      drug: null,
      pk: { dt, avg: [...avg], patient: [...pat], mec, toxic, cmax, tmax, thalf: Math.LN2 / kp, auc, accumulation: accum },
      dose, ddi, adverse: null, organs, contraindications: contra,
      explain: { params: contrib.map(([n, v]) => ({ name: n, weight: v / tot })).sort((a, b) => b.weight - a.weight), substructures: null },
      confidence: { items: [['Pharmacokinetics', 0.35], ['Organ flags', 0.7], ['Contraindications', 0.6], ['Interactions', 0.2]], warning: 'Demo model with generic drug parameters. Connect the trained model for drug-specific predictions.' },
    };
  }

  const rep = $('#report');
  const RISK = { safe: 'Safe', caution: 'Caution', high: 'High risk' };
  const SEVP = s => /major|high|2/i.test(s) ? 'bad' : /moder|1/i.test(s) ? 'warn' : /minor|0/i.test(s) ? 'ok' : 'na';
  const kv = rows => `<dl class="kv">${rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;
  const pending = what => `<p class="muted">${what} will appear here once the model is connected.</p>`;
  let pkData = null;

  function renderReport(r, p) {
    pkData = r.pk;
    Body.clearOrgans();
    Object.entries(r.organs || {}).forEach(([o, l]) => Body.setOrgan(o, l));
    const pk = r.pk, f2 = v => v < 10 ? v.toFixed(2) : v.toFixed(1);
    const organRow = (k, l) => `<li><span>${k}</span><span class="pill ${['ok', 'warn', 'bad'][l]}">${['Clear', 'Watch', 'Flag'][l]}</span></li>`;
    rep.innerHTML = `
      <h2>Report for ${esc(p.drug.identifier)}</h2>
      <p class="sub">${esc(p.drug.dose_mg)} mg ${p.drug.route === 'iv' ? 'IV' : 'oral'}, ${esc(p.drug.per_day)}× daily for ${esc(p.drug.duration_days)} days.
        <button type="button" class="primary" id="dl-pdf" style="margin-left:12px;padding:8px 16px;font-size:14px">Download PDF report</button>
      </p>
      ${r.demo ? '<div class="demo-banner" role="alert"><strong>DEMO DATA — NOT A PREDICTION</strong><br>API unreachable; client-side illustrative model only. Do not use for clinical decisions.</div>' : '<p class="disclaimer-line">Research tool only. Individualized PK-based risk estimate — not a medical device.</p>'}
      ${r.confidence && r.confidence.warning && /default|not in parameter|novel|generic/i.test(r.confidence.warning) ? '<div class="demo-banner" role="alert" style="border-color:var(--warn);background:rgba(255,210,138,.15)"><strong>LOW CONFIDENCE — GENERIC PARAMETERS</strong><br>Drug not fully covered in the knowledge base. Do not use these numbers for dosing decisions.</div>' : ''}
      <div class="summary">
        <div><div class="k">Risk level</div><div class="big ${r.summary.risk}">${RISK[r.summary.risk]}</div></div>
        <div><div class="k">Overall confidence</div><div class="conf">${esc(r.summary.confidence[0].toUpperCase() + r.summary.confidence.slice(1))}</div></div>
      </div>
      <div class="rgrid">
        <article class="card span8"><h3>Concentration over time</h3>
          <div class="pk-wrap"><canvas id="pk"></canvas></div>
          <div class="pk-legend"><span><i style="background:#fff;opacity:.6"></i>Average person</span><span><i style="background:var(--pink)"></i>This patient</span><span><i style="background:rgba(155,231,196,.6);height:8px"></i>Therapeutic window</span><span><i style="background:var(--bad)"></i>Toxic threshold</span></div>
        </article>
        <article class="card span4"><h3>Pharmacokinetics</h3>
          <div class="stats">
            <div class="stat"><b>${f2(pk.cmax)}</b><span>Cmax, mg/L</span></div>
            <div class="stat"><b>${pk.tmax.toFixed(1)} h</b><span>Tmax after first dose</span></div>
            <div class="stat"><b>${pk.thalf.toFixed(1)} h</b><span>Half-life</span></div>
            <div class="stat"><b>${f2(pk.auc)}</b><span>AUC 0–24, mg·h/L</span></div>
            <div class="stat"><b>${pk.accumulation.toFixed(2)}×</b><span>Accumulation on repeat dosing</span></div>
          </div>
        </article>
        <article class="card span4"><h3>Dose assessment</h3>
          <p style="margin:0 0 8px">${esc(r.dose.text)}</p>
          ${r.dose.range ? `<p class="muted">Indicative range: ${Math.round(r.dose.range[0])}–${Math.round(r.dose.range[1])} mg per dose.</p>` : '<p class="muted">No adjustment suggested.</p>'}
        </article>
        <article class="card span4"><h3>Patient snapshot</h3>${kv(r.patient.rows)}<h3 style="margin-top:16px">Derived</h3>${kv(r.patient.derived)}</article>
        <article class="card span4"><h3>Organ flags</h3>
          <ul class="flags">${organRow('Liver', r.organs.liver)}${organRow('Kidney', r.organs.kidneys)}${organRow('Heart / QT', r.organs.heart)}</ul>
          <h3 style="margin-top:18px">Contraindications</h3>
          ${r.contraindications.length ? `<ul class="flags">${r.contraindications.map(c => `<li><span>${esc(c.text)}</span><span class="pill ${c.severity > 1 ? 'bad' : 'warn'}">${c.severity > 1 ? 'Avoid' : 'Caution'}</span></li>`).join('')}</ul>` : '<p class="muted">No allergy or condition conflicts found.</p>'}
        </article>
        <article class="card span6"><h3>Drug-drug interactions</h3>
          ${r.ddi.length ? `<table><thead><tr><th>Current medicine</th><th>Type</th><th>Severity</th><th>Mechanism</th></tr></thead><tbody>${r.ddi.map(d => `<tr><td>${esc(d.med)}</td><td>${esc(d.type)}</td><td><span class="pill ${SEVP(d.severity)}">${esc(d.severity)}</span></td><td>${esc(d.mechanism)}</td></tr>`).join('')}</tbody></table>` : '<p class="muted">No current medicines to check.</p>'}
        </article>
        <article class="card span6"><h3>Adverse effect risk</h3>
          ${r.adverse ? `<div class="bars">${r.adverse.map(a => bar(a.name, a.p, Math.round(a.p * 100) + '%')).join('')}</div>` : pending('Top 5 predicted side effects')}
        </article>
        <article class="card span6"><h3>What moved the result</h3>
          <div class="bars">${r.explain.params.map(x => bar(x.name, x.weight, Math.round(x.weight * 100) + '%')).join('')}</div>
          <h3 style="margin-top:18px">Toxicity-linked structures</h3>
          ${r.explain.substructures ? `<ul class="flags">${r.explain.substructures.map(s => `<li><span>${esc(s.name)}</span><span>${esc(s.effect)}</span></li>`).join('')}</ul>` : pending('Structural alerts')}
        </article>
        <article class="card span6"><h3>Drug profile</h3>
          ${r.drug ? kv([['Molecular weight', r.drug.mw], ['logP', r.drug.logP], ['Solubility', r.drug.solubility], ['Targets', r.drug.targets], ['Metabolism', r.drug.pathway], ['CYP enzymes', r.drug.cyps]].concat(r.drug.composition ? [['Composition', r.drug.composition]] : [])) : pending('Molecular weight, logP, solubility, targets and CYP pathway')}
          <h3 style="margin-top:18px">Confidence and data quality</h3>
          <div class="bars">${r.confidence.items.map(([n, s]) => bar(n, s, Math.round(s * 100) + '%')).join('')}</div>
          ${r.confidence.warning ? `<p class="muted" style="margin-top:12px">${esc(r.confidence.warning)}</p>` : ''}
        </article>
      </div>`;
    rep.hidden = false;
    drawPK();
    new ResizeObserver(drawPK).observe($('#pk'));
    rep.scrollIntoView({ behavior: 'smooth' });
    const dl = $('#dl-pdf');
    if (dl) {
      dl.onclick = async () => {
        const sid = window.__lastSimId;
        if (!sid) {
          alert('PDF available after a successful API run (simulation must be persisted).');
          return;
        }
        try {
          dl.disabled = true; dl.textContent = 'Generating…';
          const r = await fetch((API_BASE || '') + '/api/v1/simulations/' + sid + '/pdf', {
            headers: apiHeaders(false),
          });
          if (!r.ok) throw new Error(r.status + ' ' + (await r.text().catch(() => '')));
          const blob = await r.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = 'digital_twin_report_' + sid + '.pdf';
          document.body.appendChild(a); a.click(); a.remove();
          URL.revokeObjectURL(url);
        } catch (err) {
          alert('Could not download PDF: ' + err.message);
        } finally {
          dl.disabled = false; dl.textContent = 'Download PDF report';
        }
      };
    }
  }
  const bar = (name, v, label) => `<div class="barrow"><span>${esc(name)}</span><span class="track"><span class="fill" style="width:${Math.max(2, Math.min(100, v * 100))}%"></span></span><span class="v">${label}</span></div>`;

  function drawPK() {
    const cv = $('#pk'); if (!cv || !pkData) return;
    const { avg, patient, mec, toxic, dt } = pkData;
    const dpr = Math.min(devicePixelRatio || 1, 2), r = cv.getBoundingClientRect(), W = r.width, H = r.height;
    cv.width = W * dpr; cv.height = H * dpr;
    const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const L = 44, B = 26, T = 8, R = 8, pw = W - L - R, ph = H - T - B;
    const maxY = Math.max(toxic * 1.15, ...patient, ...avg), maxT = (patient.length - 1) * dt;
    const X = t => L + (t / maxT) * pw, Y = v => T + ph - (v / maxY) * ph;
    c.font = '12px "Bricolage Grotesque", system-ui'; c.fillStyle = 'rgba(255,255,255,.6)';
    c.strokeStyle = 'rgba(255,255,255,.12)'; c.lineWidth = 1;
    for (let i = 0; i <= 4; i++) { const v = maxY * i / 4, y = Y(v); c.beginPath(); c.moveTo(L, y); c.lineTo(W - R, y); c.stroke(); c.textAlign = 'right'; c.fillText(v.toFixed(v < 10 ? 1 : 0), L - 6, y + 4); }
    const stepT = maxT > 48 ? 24 : 12; c.textAlign = 'center';
    for (let t = 0; t <= maxT; t += stepT) c.fillText(t + ' h', X(t), H - 6);
    c.fillStyle = 'rgba(155,231,196,.12)'; c.fillRect(L, Y(toxic), pw, Y(mec) - Y(toxic));
    c.strokeStyle = 'rgba(255,122,147,.9)'; c.setLineDash([5, 4]); c.beginPath(); c.moveTo(L, Y(toxic)); c.lineTo(W - R, Y(toxic)); c.stroke(); c.setLineDash([]);
    const plot = (arr, col, w, dash) => { c.strokeStyle = col; c.lineWidth = w; c.setLineDash(dash); c.beginPath(); arr.forEach((v, i) => i ? c.lineTo(X(i * dt), Y(v)) : c.moveTo(X(0), Y(v))); c.stroke(); c.setLineDash([]); };
    plot(avg, 'rgba(255,255,255,.6)', 1.5, [4, 4]);
    c.shadowColor = '#f7c6d9'; c.shadowBlur = 10; plot(patient, '#f7c6d9', 2.2, []); c.shadowBlur = 0;
  }

  const links = $$('.nav nav a');
  const navIO = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id));
  }), { rootMargin: '-45% 0px -50% 0px' });
  $$('main > section').forEach(s => navIO.observe(s));
  links.forEach(a => a.addEventListener('click', e => { if (a.hash === '#report' && rep.hidden) { e.preventDefault(); selectTab('t-drug'); $('#simulate').scrollIntoView({ behavior: 'smooth' }); } }));
})();
