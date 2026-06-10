import type { Message, TrajectoryArtifact, WriteResult } from "@/types/chat";

export interface ChatApiResponse {
  response: string;
  source: string;
  session_id: string;
  mission_id: string;
  tool_calls?: Array<{ name: string; args: Record<string, unknown> }>;
  trajectory_artifact?: TrajectoryArtifact | null;
  write_result?: WriteResult | null;
}

const RUNTIME_SESSION_STORAGE_KEY = "stratos-runtime-session-id";
const RUNTIME_USER_STORAGE_KEY = "stratos-runtime-user-id";
const RUNTIME_MISSION_STORAGE_KEY = "stratos-runtime-mission-id";
const DEFAULT_RUNTIME_USER_ID = "stratos-local-user";
const DEFAULT_RUNTIME_MISSION_ID = "aero";

function getRuntimeEndpoint(): string {
  const configuredBase = process.env.NEXT_PUBLIC_BACKEND_URL?.trim();
  if (configuredBase) {
    return `${configuredBase.replace(/\/$/, "")}/runtime/request`;
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    const isLocalDevHost = hostname === "localhost" || hostname === "127.0.0.1";

    if (isLocalDevHost && (protocol === "http:" || protocol === "https:")) {
      return "http://127.0.0.1:8000/runtime/request";
    }
  }

  return "/api/runtime/request";
}

function getStoredValue(key: string, fallback: string): string {
  if (typeof window === "undefined") {
    return fallback;
  }

  return window.localStorage.getItem(key) || fallback;
}

function makeRuntimeSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `sess_${crypto.randomUUID()}`;
  }

  return `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
}

function getRuntimeSessionId(): string {
  if (typeof window === "undefined") {
    return makeRuntimeSessionId();
  }

  const existing = window.localStorage.getItem(RUNTIME_SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const sessionId = makeRuntimeSessionId();
  window.localStorage.setItem(RUNTIME_SESSION_STORAGE_KEY, sessionId);
  return sessionId;
}

function rememberRuntimeSessionId(sessionId: string): void {
  if (typeof window !== "undefined" && sessionId) {
    window.localStorage.setItem(RUNTIME_SESSION_STORAGE_KEY, sessionId);
  }
}

/**
 * Send a message to the STRATOS backend and return the response.
 * Throws an Error with a user-facing message on network or server failure.
 */
export async function sendMessage(
  message: string,
  history: Message[] = [],
): Promise<ChatApiResponse> {
  void history;

  let res: Response;

  try {
    const endpoint = getRuntimeEndpoint();
    res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: getStoredValue(RUNTIME_USER_STORAGE_KEY, DEFAULT_RUNTIME_USER_ID),
        mission_id: getStoredValue(
          RUNTIME_MISSION_STORAGE_KEY,
          DEFAULT_RUNTIME_MISSION_ID,
        ),
        session_id: getRuntimeSessionId(),
        operation: "chat",
        message,
        write_intent: null,
      }),
    });
  } catch {
    throw new Error(
      "Unable to reach the STRATOS backend. Check that the server is running."
    );
  }

  if (!res.ok) {
    let detail = `Server error ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // ignore JSON parse failure - keep the status-code message
    }
    throw new Error(detail);
  }

  const data = (await res.json()) as ChatApiResponse;
  rememberRuntimeSessionId(data.session_id);
  return data;
}
