/**
 * INLINE snippet — paste into app.js inside the main IIFE,
 * after COMP_OCR_URL is defined and before form submit handler.
 *
 * Looks for #lab-report and wires parse-report auto-fill.
 */

  // ---- Lab report auto-fill (patient tab) ----
  const LAB_PARSE_URL = (API_BASE || '') + '/api/v1/patients/parse-report';
  const labReportInput = $('#lab-report');
  const labStatus = $('#lab-status');

  function setLabStatus(msg, isError) {
    if (!labStatus) return;
    labStatus.hidden = false;
    labStatus.textContent = msg;
    labStatus.style.color = isError ? 'var(--bad)' : 'var(--pink-soft)';
  }

  function applyLabFields(fields) {
    if (!fields) return 0;
    let n = 0;
    const set = (name, val) => {
      if (val == null || !F(name)) return;
      F(name).value = val;
      F(name).dispatchEvent(new Event('input', { bubbles: true }));
      F(name).dispatchEvent(new Event('change', { bubbles: true }));
      n++;
    };
    set('age', fields.age);
    if (fields.sex) {
      const s = String(fields.sex).toLowerCase();
      const mapped = (s === 'female' || s === 'f') ? 'F' : (s === 'male' || s === 'm') ? 'M' : '';
      if (mapped) set('sex', mapped);
    }
    set('weight', fields.weight_kg);
    set('height', fields.height_cm);

    if (fields.egfr != null) {
      const egfrRadio = form.querySelector('input[name=kidneyMode][value=egfr]');
      if (egfrRadio) { egfrRadio.checked = true; egfrRadio.dispatchEvent(new Event('change', { bubbles: true })); }
      set('egfr', fields.egfr);
    } else if (fields.serum_creatinine != null) {
      const scrRadio = form.querySelector('input[name=kidneyMode][value=scr]');
      if (scrRadio) { scrRadio.checked = true; scrRadio.dispatchEvent(new Event('change', { bubbles: true })); }
      set('creatinine', fields.serum_creatinine);
    }

    set('alt', fields.alt);
    set('ast', fields.ast);
    set('bilirubin', fields.bilirubin);
    set('albumin', fields.albumin);
    updateDerived();
    return n;
  }

  if (labReportInput) {
    labReportInput.addEventListener('change', async () => {
      const file = labReportInput.files && labReportInput.files[0];
      if (!file) return;
      setLabStatus('Reading lab report…');
      try {
        requireApiKeyOrThrow();
        const fd = new FormData();
        fd.append('file', file);
        const r = await fetch(LAB_PARSE_URL, { method: 'POST', headers: apiHeaders(false), body: fd });
        if (!r.ok) throw new Error(r.status + ' ' + (await r.text().catch(() => '')).slice(0, 180));
        const data = await r.json();
        const filled = applyLabFields(data.fields || {});
        if (filled > 0) {
          setLabStatus((data.message || 'Values filled.') + ` (${filled} field(s)). Review before simulating.`);
        } else {
          setLabStatus(data.message || 'No fields detected. Enter values manually.', true);
        }
      } catch (err) {
        console.warn('Lab report parse failed:', err);
        setLabStatus('Could not parse report (' + (err && err.message ? err.message : err) + '). Enter values manually.', true);
      } finally {
        labReportInput.value = '';
      }
    });
  }
