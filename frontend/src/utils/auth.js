export const AUTH_STORAGE_KEY = 'travelai_auth';

export function loadAuth() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return { token: null, user: null };
    const parsed = JSON.parse(raw);
    return {
      token: parsed?.token || null,
      user: parsed?.user || null,
    };
  } catch {
    return { token: null, user: null };
  }
}

export function saveAuth(token, user) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token, user }));
}

export function clearAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}
