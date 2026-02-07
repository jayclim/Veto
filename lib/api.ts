import { FAKE_TRANSACTIONS, FAKE_DASHBOARD } from "./fake-data";

const API_BASE = "http://localhost:8000/api/v1";

// ── Flip to `false` when the real backend is ready ──
const USE_FAKE_DATA = true;

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  username: string
): Promise<T> {
  if (USE_FAKE_DATA) {
    // Simulate a small network delay so loading states still render
    await new Promise((r) => setTimeout(r, 300));
    return fakeFetch<T>(path, options);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-User-Username": username,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json();
}

// ── Route fake responses to match the real API contract ──
function fakeFetch<T>(path: string, options: RequestInit): T {
  const method = (options.method ?? "GET").toUpperCase();

  // GET /transactions
  if (path === "/transactions" && method === "GET") {
    return [...FAKE_TRANSACTIONS].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    ) as unknown as T;
  }

  // GET /budgets/dashboard
  if (path === "/budgets/dashboard" && method === "GET") {
    return FAKE_DASHBOARD as unknown as T;
  }

  // POST /transactions — no-op in fake mode, just echo back
  if (path === "/transactions" && method === "POST") {
    return { id: `tx-fake-${Date.now()}`, ...(JSON.parse(options.body as string)) } as unknown as T;
  }

  // DELETE /transactions/:id — no-op
  if (path.startsWith("/transactions/") && method === "DELETE") {
    return {} as unknown as T;
  }

  // POST /budgets/categories — no-op
  if (path === "/budgets/categories" && method === "POST") {
    return { id: `cat-fake-${Date.now()}`, ...(JSON.parse(options.body as string)) } as unknown as T;
  }

  throw new Error(`[fake-data] Unhandled route: ${method} ${path}`);
}
