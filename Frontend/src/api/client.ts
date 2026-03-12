/**
 * API client for Smart Medication Adherence System backend.
 * Uses VITE_API_URL in dev (proxied via Vite) or production.
 */
const API_BASE = import.meta.env.VITE_API_URL ?? '';

async function request<T>(
  path: string,
  options?: RequestInit & { params?: Record<string, string | number> }
): Promise<T> {
  const { params, ...init } = options ?? {};
  let url = `${API_BASE}${path}`;
  if (params) {
    const search = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString();
    url += (url.includes('?') ? '&' : '?') + search;
  }

  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string, params?: Record<string, string | number>) =>
    request<T>(path, { method: 'GET', params }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),

  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  upload: async <T>(path: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? `Upload failed: ${res.status}`);
    }
    return res.json() as Promise<T>;
  },
};

export function getWsUrl(patientId: number): string {
  const base = API_BASE || window.location.origin;
  const wsProtocol = base.startsWith('https') ? 'wss' : 'ws';
  const host = base ? base.replace(/^https?:\/\//, '') : window.location.host;
  return `${wsProtocol}://${host}/ws/${patientId}`;
}
