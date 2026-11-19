/**
 * AgriSmart AI — Auth module
 * Handles login, logout, session and role-based access.
 * Uses SHA-256 (Web Crypto API) to hash passwords client-side
 * before comparing against the stored hashes.
 *
 * NOTE: In a real deployment this logic lives on the server.
 * This JS module is for a standalone frontend demo / reference.
 */

'use strict';

const Auth = (() => {

  /* ── SHA-256 via Web Crypto ─────────────────── */
  async function sha256(str) {
    const buf    = new TextEncoder().encode(str);
    const digest = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(digest))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  /* ── Session ────────────────────────────────── */
  const SESSION_KEY = 'agrismart_session';

  function getSession() {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  function setSession(user) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
  }

  function clearSession() {
    sessionStorage.removeItem(SESSION_KEY);
  }

  function isAuthenticated() {
    return !!getSession();
  }

  function currentUser() {
    return getSession();
  }

  function isAdmin() {
    const s = getSession();
    return s && s.role === 'admin';
  }

  /* ── Login ──────────────────────────────────── */
  async function login(username, password, usersMap) {
    /**
     * usersMap: { username: { password: <sha256hex>, role, name }, ... }
     * Returns { ok: true, user } on success or { ok: false, error } on failure.
     */
    if (!username || !password) {
      return { ok: false, error: 'Please enter both username and password.' };
    }
    const record = usersMap[username];
    if (!record) {
      return { ok: false, error: 'Invalid username or password.' };
    }
    const hash = await sha256(password);
    if (hash !== record.password) {
      return { ok: false, error: 'Invalid username or password.' };
    }
    const session = { username, name: record.name, role: record.role };
    setSession(session);
    return { ok: true, user: session };
  }

  /* ── Logout ─────────────────────────────────── */
  function logout() {
    clearSession();
    window.location.href = '../pages/login.html';
  }

  /* ── Guard ──────────────────────────────────── */
  function requireAuth() {
    /** Call at top of every protected page. Redirects to login if not authenticated. */
    if (!isAuthenticated()) {
      window.location.href = '../pages/login.html';
      return false;
    }
    return true;
  }

  function requireAdmin() {
    if (!requireAuth()) return false;
    if (!isAdmin()) {
      window.location.href = '../pages/overview.html';
      return false;
    }
    return true;
  }

  return { login, logout, requireAuth, requireAdmin,
           isAuthenticated, isAdmin, currentUser, sha256 };
})();
