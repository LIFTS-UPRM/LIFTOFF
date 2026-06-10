import type { TrajectoryArtifact, WriteResult } from "@/types/chat";

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
const DEFAULT_RUNTIME_USER_ID = "stratos-local-user";

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

function safeLocalStorageGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeLocalStorageSet(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // storage blocked — value won't persist but the request still works
  }
}

function getStoredValue(key: string, fallback: string): string {
  if (typeof window === "undefined") {
    return fallback;
  }

  return safeLocalStorageGet(key) || fallback;
}

function makeRuntimeSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `sess_${crypto.randomUUID()}`;
  }

  // randomUUID unavailable (very old runtime) — fall back to getRandomValues, which is CSPRNG.
  // Never use Math.random() for a session identifier.
  const buf = new Uint8Array(16);
  crypto.getRandomValues(buf);
  return `sess_${Array.from(buf, (b) => b.toString(16).padStart(2, "0")).join("")}`;
}

function getRuntimeSessionId(): string {
  if (typeof window === "undefined") {
    return makeRuntimeSessionId();
  }

  const existing = safeLocalStorageGet(RUNTIME_SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const sessionId = makeRuntimeSessionId();
  safeLocalStorageSet(RUNTIME_SESSION_STORAGE_KEY, sessionId);
  return sessionId;
}

function rememberRuntimeSessionId(sessionId: string): void {
  if (typeof window !== "undefined" && sessionId) {
    safeLocalStorageSet(RUNTIME_SESSION_STORAGE_KEY, sessionId);
  }
}

/**
 * Send a message to the STRATOS backend and return the response.
 * Throws an Error with a user-facing message on network or server failure.
 *
 * Client-supplied history is not forwarded — the runtime contract rejects it.
 * Server-side session continuity is managed via session_id.
 */
export async function sendMessage(
  message: string,
  missionId: string,
): Promise<ChatApiResponse> {
  let res: Response;

  try {
    const endpoint = getRuntimeEndpoint();
    res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: getStoredValue(RUNTIME_USER_STORAGE_KEY, DEFAULT_RUNTIME_USER_ID),
        mission_id: missionId,
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
