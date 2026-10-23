/**
 * Lab report upload + auto-fill patch for Digital Twin / Tally Twin frontend.
 *
 * HOW TO MERGE into app.js:
 * 1. Ensure index.html has the upload UI (see index_lab_upload_snippet.html)
 * 2. Paste this block near the top of the IIFE after API helpers, OR
 *    include as a separate script AFTER app.js and call LabReportAutofill.init(form)
 */

const LabReportAutofill = (() => {
  function init(form, opts = {}) {
    const $ = (s, r = document) => r.querySelector(s);
    const API_BASE = (typeof window.DT_API_URL === 'string' && window.DT_API_URL)
      ? window.DT_API_URL.replace(/\/+$/, '')
      : '';
    const API_KEY = (typeof window.DT_API_KEY === 'string' && window.DT_API_KEY)
      ? window.DT_API_KEY
      : (typeof localStorage !== 'undefined' ? (localStorage.getItem('DT_API_KEY') || '') : '');

    const PARSE_URL = (API_BASE || '') + '/api/v1/patients/parse-report';
    const input = opts.input || $('#lab-report');
    const statusEl = opts.status || $('#lab-status');
    if (!input || !form) {
      console.warn('LabReportAutofill: missing #lab-report input or form');
      return;
    }

    function apiHeaders() {
      const h = {};
      if (API_KEY) h['X-API-Key'] = API_KEY;
      return h;
    }

    function setStatus(msg, isError) {
      if (!statusEl) return;
      statusEl.hidden = false;
      statusEl.textContent = msg;
      statusEl.style.color = isError ? 'var(--bad, #ff7a93)' : 'var(--pink-soft, #fbe3ec)';
    }

    function setField(name, value) {
      const el = form.elements[name];
      if (!el || value == null || value === '') return false;
      el.value = value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }

    function applyFields(fields) {
      if (!fields) return 0;
      let n = 0;

      if (fields.age != null && setField('age', fields.age)) n++;

      if (fields.sex) {
        const s = String(fields.sex).toLowerCase();
        // Frontend uses F / M
        const mapped = s === 'female' || s === 'f' ? 'F' : s === 'male' || s === 'm' ? 'M' : '';
        if (mapped && setField('sex', mapped)) n++;
      }

      if (fields.weight_kg != null && setField('weight', fields.weight_kg)) n++;
      if (fields.height_cm != null && setField('height', fields.height_cm)) n++;

      // Kidney: prefer explicit eGFR; else creatinine + switch mode
      if (fields.egfr != null) {
        const egfrRadio = form.querySelector('input[name=kidneyMode][value=egfr]');
        if (egfrRadio) {
          egfrRadio.checked = true;
          egfrRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
        if (setField('egfr', fields.egfr)) n++;
      } else if (fields.serum_creatinine != null) {
        const scrRadio = form.querySelector('input[name=kidneyMode][value=scr]');
        if (scrRadio) {
          scrRadio.checked = true;
          scrRadio.dispatchEvent(new Event('change', { bubbles: true }));
        }
        if (setField('creatinine', fields.serum_creatinine)) n++;
      }

      if (fields.alt != null && setField('alt', fields.alt)) n++;
      if (fields.ast != null && setField('ast', fields.ast)) n++;
      if (fields.bilirubin != null && setField('bilirubin', fields.bilirubin)) n++;
      if (fields.albumin != null && setField('albumin', fields.albumin)) n++;

      return n;
    }

    input.addEventListener('change', async () => {
      const file = input.files && input.files[0];
      if (!file) return;

      setStatus('Reading lab report…');
      try {
        if (!API_KEY) {
          throw new Error(
            'No API key. Run: localStorage.setItem("DT_API_KEY","dev-local-key-change-me")'
          );
        }

        const fd = new FormData();
        fd.append('file', file);

        const r = await fetch(PARSE_URL, {
          method: 'POST',
          headers: apiHeaders(),
          body: fd,
        });

        if (!r.ok) {
          const t = await r.text().catch(() => '');
          throw new Error(r.status + ' ' + t.slice(0, 200));
        }

        const data = await r.json();
        const fields = data.fields || {};
        const filled = applyFields(fields);

        // Trigger BMI / eGFR derived outputs if form has updateDerived
        form.dispatchEvent(new Event('input', { bubbles: true }));

        if (filled > 0) {
          setStatus(
            (data.message || 'Values filled from report.') +
              ` (${filled} field(s)). Please review before simulating.`
          );
        } else {
          setStatus(
            data.message || 'No fields detected. Enter values manually.',
            true
          );
        }

        if (data.warnings && data.warnings.length) {
          console.info('Lab report warnings:', data.warnings);
        }
      } catch (err) {
        console.warn('Lab report parse failed:', err);
        setStatus(
          'Could not parse report (' + (err.message || err) + '). Enter values manually.',
          true
        );
      } finally {
        // allow re-upload of same file
        input.value = '';
      }
    });
  }

  return { init };
})();

// Auto-init when DOM ready and form exists
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('twin-form');
    if (form && document.getElementById('lab-report')) {
      LabReportAutofill.init(form);
    }
  });
}
