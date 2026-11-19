/**
 * AgriSmart AI — App bootstrap
 * Runs on every protected page:
 *  1. Auth guard
 *  2. Renders sidebar user info + active nav
 *  3. Wires logout button
 *  4. Mobile sidebar toggle
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  /* ── 1. Auth guard ──────────────────────────── */
  if (!Auth.requireAuth()) return;
  const user = Auth.currentUser();

  /* ── 2. Sidebar user pill ───────────────────── */
  UI.renderSidebarUser(user);

  /* ── 3. Active nav ──────────────────────────── */
  const pageId = document.body.dataset.page || '';
  UI.setActiveNav(pageId);

  /* ── 4. Hide User Management for non-admin ──── */
  if (user.role !== 'admin') {
    document.querySelectorAll('[data-page="user-management"]')
      .forEach(el => el.style.display = 'none');
  }

  /* ── 5. Logout ──────────────────────────────── */
  document.querySelectorAll('.btn-logout').forEach(btn => {
    btn.addEventListener('click', () => Auth.logout());
  });

  /* ── 6. Mobile sidebar toggle ───────────────── */
  const sidebar  = document.querySelector('.sidebar');
  const overlay  = document.querySelector('.sidebar-overlay');
  const menuBtn  = document.querySelector('.menu-toggle');

  function openSidebar()  { sidebar?.classList.add('open');  overlay?.classList.add('open'); }
  function closeSidebar() { sidebar?.classList.remove('open'); overlay?.classList.remove('open'); }

  menuBtn?.addEventListener('click', openSidebar);
  overlay?.addEventListener('click', closeSidebar);

  /* ── 7. Hero ────────────────────────────────── */
  const heroEl = document.getElementById('hero');
  if (heroEl) {
    const trained = parseInt(heroEl.dataset.trained || '0', 10);
    heroEl.innerHTML = UI.hero(user.name, trained);
  }

  /* ── 8. Expanders ───────────────────────────── */
  UI.initExpanders();
});
