/**
 * AgriSmart AI — Auth module
 * Calls the FastAPI backend at http://localhost:8000
 * Stores JWT token in localStorage so it persists across pages.
 */

'use strict';

const API_URL = 'http://localhost:8000';

const Auth = (() => {

  const TOKEN_KEY   = 'agrismart_token';
  const SESSION_KEY = 'agrismart_session';

  /* ── Session storage ────────────────────────── */
  function getSession() {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  function setSession(user, token) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearSession() {
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(TOKEN_KEY);
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function isAuthenticated() {
    return !!(getSession() && getToken());
  }

  function currentUser() {
    return getSession();
  }

  function isAdmin() {
    const s = getSession();
    return s && s.role === 'admin';
  }

  /* ── Login — calls FastAPI /api/auth/login ──── */
  async function login(username, password) {
    if (!username || !password) {
      return { ok: false, error: 'Please enter both username and password.' };
    }
    try {
      const resp = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (resp.ok) {
        const data = await resp.json();
        const user = { username: data.username, name: data.name, role: data.role };
        setSession(user, data.access_token);
        return { ok: true, user };
      } else if (resp.status === 401) {
        return { ok: false, error: 'Invalid username or password.' };
      } else {
        return { ok: false, error: `Server error (${resp.status}). Try again.` };
      }
    } catch (e) {
      return { ok: false, error: 'Cannot reach API server. Make sure it is running on port 8000.' };
    }
  }

  /* ── API call helper ────────────────────────── */
  async function apiFetch(path, options = {}) {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    };
    return fetch(`${API_URL}${path}`, { ...options, headers });
  }

  /* ── Logout ─────────────────────────────────── */
  function logout() {
    clearSession();
    window.location.href = 'login.html';
  }

  /* ── Guards ─────────────────────────────────── */
  function requireAuth() {
    if (!isAuthenticated()) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  }

  function requireAdmin() {
    if (!requireAuth()) return false;
    if (!isAdmin()) {
      window.location.href = 'overview.html';
      return false;
    }
    return true;
  }

  /* ── SHA-256 (kept for compatibility) ────────── */
  async function sha256(str) {
    const buf    = new TextEncoder().encode(str);
    const digest = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(digest))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  return {
    login, logout, requireAuth, requireAdmin,
    isAuthenticated, isAdmin, currentUser,
    getToken, apiFetch, sha256,
  };
})();
