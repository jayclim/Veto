import { FAKE_TRANSACTIONS, FAKE_DASHBOARD } from "./fake-data";

const API_BASE = "http://localhost:8000/api/v1";

// ── Flip to `false` when the real backend is ready ──
// ── Flip to `false` when the real backend is ready ──
const USE_FAKE_DATA = false;

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  username: string
): Promise<T> {
  //   if (USE_FAKE_DATA) {
  //     // Simulate a small network delay so loading states still render
  //     await new Promise((r) => setTimeout(r, 300));
  //     // return fakeFetch<T>(path, options);
  //   }

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

// ── Onboarding API ──────────────────────────────────────────────

export interface OnboardingStatus {
  needs_onboarding: boolean;
}

export interface OnboardingCompleteRequest {
  monthly_income: number;
  budget_strategy: string;
  needs_pct?: number;
  wants_pct?: number;
  savings_pct?: number;
}

export interface OnboardingCompleteResponse {
  success: boolean;
  transactions_created: number;
  rules_created: number;
}

export async function checkOnboardingStatus(
  username: string
): Promise<OnboardingStatus> {
  return apiFetch<OnboardingStatus>("/onboarding/status", {}, username);
}

export async function completeOnboarding(
  data: OnboardingCompleteRequest,
  username: string
): Promise<OnboardingCompleteResponse> {
  return apiFetch<OnboardingCompleteResponse>(
    "/onboarding/complete",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
    username
  );
}

// Chat API types and function
export interface ChatRequest {
  message: string;
  conversationHistory?: Array<{ role: string; content: string }>;
}

export interface ActionResult {
  type: string;
  success: boolean;
  details?: Record<string, unknown>;
  error?: string;
}

export interface ChatResponse {
  id: string;
  role: string;
  content: string;
  timestamp: string;
  actions: ActionResult[];
}

export async function sendChatMessage(
  message: string,
  conversationHistory: Array<{ role: string; content: string }>,
  username: string
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(
    "/chat",
    {
      method: "POST",
      body: JSON.stringify({
        message,
        conversationHistory,
      }),
    },
    username
  );
}

export interface StreamEvent {
  type: "token" | "actions" | "done";
  content?: string;
  actions?: ActionResult[];
}

export async function sendChatMessageStream(
  message: string,
  conversationHistory: Array<{ role: string; content: string }>,
  username: string,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Username": username,
    },
    body: JSON.stringify({ message, conversationHistory }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;

      try {
        const event: StreamEvent = JSON.parse(trimmed.slice(6));
        onEvent(event);
      } catch {
        // skip malformed lines
      }
    }
  }
}
