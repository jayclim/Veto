const API_BASE = "http://localhost:8000/api/v1";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  username: string
): Promise<T> {
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
