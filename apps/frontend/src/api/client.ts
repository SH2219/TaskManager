const TOKEN_KEY = "taskmanager_token";

/** Render/production API origin. Empty = same-origin / Vite proxy. */
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function apiUrl(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(apiUrl(path), { ...options, headers });
  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    let message = response.statusText || "Request failed";
    if (typeof detail === "string") message = detail;
    else if (Array.isArray(detail)) {
      message = detail
        .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item)))
        .join(", ");
    }
    throw new Error(message);
  }

  return data as T;
}
