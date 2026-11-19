/**
 * AgriSmart AI — UI utilities
 * Reusable DOM helpers used across all pages.
 */

'use strict';

const UI = (() => {

  /* ── Badge ──────────────────────────────────── */
  function badge(label, kind) {
    return `<span class="badge badge-${kind}">${label}</span>`;
  }

  /* ── Confidence bars ────────────────────────── */
  function confBars(items) {
    /**
     * items: Array of { label: string, value: number 0-1 }
     * Returns HTML string; bars animate on next frame.
     */
    const rows = items.map(({ label, value }) => {
      const pct = Math.max(0, Math.min(1, value)) * 100;
      return `
        <div class="conf-bar-row">
          <div class="conf-bar-label" title="${label}">${label}</div>
          <div class="conf-bar-track">
            <div class="conf-bar-fill" data-width="${pct.toFixed(1)}"></div>
          </div>
          <div class="conf-bar-val">${pct.toFixed(1)}%</div>
        </div>`;
    }).join('');
    return `<div class="conf-bars">${rows}</div>`;
  }

  function animateBars(container) {
    /** Trigger bar fill animation after inserting confBars HTML into DOM. */
    requestAnimationFrame(() => {
      (container || document).querySelectorAll('.conf-bar-fill[data-width]').forEach(el => {
        const w = el.dataset.width;
        requestAnimationFrame(() => { el.style.width = w + '%'; });
      });
    });
  }

  /* ── Result card ────────────────────────────── */
  function resultCard(big, sub, conf = null) {
    const confHtml = conf !== null
      ? `<div class="result-conf">Model confidence: ${conf}</div>`
      : '';
    return `
      <div class="result-card">
        <div class="result-big">${big}</div>
        <div class="result-sub">${sub}</div>
        ${confHtml}
      </div>`;
  }

  /* ── Alert ──────────────────────────────────── */
  function alert(msg, type = 'info') {
    const icons = { error:'❌', success:'✅', info:'ℹ️', warning:'⚠️' };
    return `<div class="alert alert-${type}">${icons[type] || ''} ${msg}</div>`;
  }

  /* ── Spinner ────────────────────────────────── */
  function spinner() {
    return '<span class="spinner"></span>';
  }

  /* ── Feature card ───────────────────────────── */
  function featureCard(icon, title, desc, trained) {
    const pill = trained
      ? badge('✓ Trained', 'ok')
      : badge('Not trained', 'warn');
    return `
      <div class="feature-card">
        <div class="feature-icon">${icon}</div>
        <div class="feature-title">${title}</div>
        <div class="feature-desc">${desc}</div>
        ${pill}
      </div>`;
  }

  /* ── Hero banner ────────────────────────────── */
  function hero(userName, trainedCount) {
    return `
      <div class="ag-hero">
        <h1>🌱 AgriSmart AI</h1>
        <p>Explainable ML decision support for sustainable agriculture —
           recommend crops, estimate yields and detect plant disease.</p>
        <div class="ag-stats">
          <span class="ag-stat">3 modules</span>
          <span class="ag-stat">${trainedCount}/3 models trained</span>
          <span class="ag-stat">Hello, ${userName} 👋</span>
        </div>
      </div>`;
  }

  /* ── Callout ────────────────────────────────── */
  function callout(html) {
    return `<div class="callout">${html}</div>`;
  }

  /* ── Metric tile ────────────────────────────── */
  function metricTile(label, value) {
    return `
      <div class="metric-tile">
        <div class="metric-label">${label}</div>
        <div class="metric-value">${value}</div>
      </div>`;
  }

  /* ── Page heading ───────────────────────────── */
  function pageHeading(icon, title, caption) {
    return `
      <div class="page-title">${icon} ${title}</div>
      <div class="page-caption">${caption}</div>`;
  }

  /* ── Expander ───────────────────────────────── */
  function initExpanders(root) {
    (root || document).querySelectorAll('.expander').forEach(exp => {
      const header = exp.querySelector('.expander-header');
      if (!header) return;
      header.addEventListener('click', () => exp.classList.toggle('open'));
    });
  }

  /* ── File drop zone ─────────────────────────── */
  function initFileDrop(dropEl, inputEl, onFile) {
    if (!dropEl || !inputEl) return;
    dropEl.addEventListener('click', () => inputEl.click());
    inputEl.addEventListener('change', e => {
      if (e.target.files[0]) onFile(e.target.files[0]);
    });
    dropEl.addEventListener('dragover', e => { e.preventDefault(); dropEl.classList.add('drag-over'); });
    dropEl.addEventListener('dragleave', ()  => dropEl.classList.remove('drag-over'));
    dropEl.addEventListener('drop', e => {
      e.preventDefault();
      dropEl.classList.remove('drag-over');
      if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]);
    });
  }

  /* ── Sidebar: active nav link ───────────────── */
  function setActiveNav(pageId) {
    document.querySelectorAll('.nav-link').forEach(a => {
      a.classList.toggle('active', a.dataset.page === pageId);
    });
  }

  /* ── Build sidebar user pill ────────────────── */
  function renderSidebarUser(user) {
    const roleKind = user.role === 'admin' ? 'admin' : 'viewer';
    const el = document.getElementById('sidebar-user');
    if (!el) return;
    el.innerHTML = `
      <div class="sidebar-user-label">Signed in as</div>
      <div class="sidebar-user-name">${user.name}</div>
      ${badge(user.role.toUpperCase(), roleKind)}`;
  }

  /* ── Toast notification ─────────────────────── */
  function toast(msg, type = 'success', duration = 3000) {
    const t = document.createElement('div');
    t.className = `alert alert-${type}`;
    Object.assign(t.style, {
      position: 'fixed', bottom: '1.5rem', right: '1.5rem',
      zIndex: 9999, maxWidth: '340px',
      boxShadow: '0 6px 20px rgba(0,0,0,.14)',
      animation: 'fadeSlideIn .25s ease',
    });
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), duration);
  }

  return {
    badge, confBars, animateBars, resultCard, alert,
    spinner, featureCard, hero, callout, metricTile,
    pageHeading, initExpanders, initFileDrop,
    setActiveNav, renderSidebarUser, toast,
  };
})();
