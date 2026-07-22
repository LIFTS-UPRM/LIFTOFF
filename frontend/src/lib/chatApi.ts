import { createClient } from "@/lib/supabase/client";
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

function safeLocalStorageRemove(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

function sessionKey(missionId: string): string {
  return `stratos-session-${missionId}`;
}

function makeRuntimeSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `sess_${crypto.randomUUID()}`;
  }

  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    const buf = new Uint8Array(16);
    crypto.getRandomValues(buf);
    return `sess_${Array.from(buf, (b) => b.toString(16).padStart(2, "0")).join("")}`;
  }

  throw new Error(
    "No cryptographically secure random source is available in this runtime. " +
    "Session ID cannot be generated safely.",
  );
}

function getRuntimeSessionId(missionId: string): string {
  if (typeof window === "undefined") {
    return makeRuntimeSessionId();
  }

  const key = sessionKey(missionId);
  const existing = safeLocalStorageGet(key);
  if (existing) return existing;

  const sessionId = makeRuntimeSessionId();
  safeLocalStorageSet(key, sessionId);
  return sessionId;
}

function rememberRuntimeSessionId(missionId: string, sessionId: string): void {
  if (typeof window !== "undefined" && sessionId) {
    safeLocalStorageSet(sessionKey(missionId), sessionId);
  }
}

export function clearRuntimeSessionId(missionId: string): void {
  if (typeof window !== "undefined") {
    safeLocalStorageRemove(sessionKey(missionId));
  }
}

async function getAuthHeaders(): Promise<{ Authorization: string; userId: string }> {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) {
    throw new Error("Not authenticated. Please sign in.");
  }

  return {
    Authorization: `Bearer ${session.access_token}`,
    userId: session.user.id,
  };
}

/**
 * Send a message to the STRATOS backend and return the response.
 * Throws an Error with a user-facing message on network or server failure.
 *
 * Session continuity is managed per-mission via session_id.
 * Conversation history is stored server-side; the client does not send it.
 */
export async function sendMessage(
  message: string,
  missionId: string,
): Promise<ChatApiResponse> {
  const { Authorization, userId } = await getAuthHeaders();
  const sessionId = getRuntimeSessionId(missionId);

  let res: Response;
  try {
    res = await fetch(getRuntimeEndpoint(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization,
      },
      body: JSON.stringify({
        user_id: userId,
        mission_id: missionId,
        session_id: sessionId,
        operation: "chat",
        message,
        write_intent: null,
      }),
    });
  } catch {
    throw new Error(
      "Unable to reach the STRATOS backend. Check that the server is running.",
    );
  }

  if (!res.ok) {
    let detail = `Server error ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail = typeof body.detail === "string"
          ? body.detail
          : (body.detail?.error ?? JSON.stringify(body.detail));
      }
    } catch {
      // ignore JSON parse failure
    }
    throw new Error(detail);
  }

  const data = (await res.json()) as ChatApiResponse;
  rememberRuntimeSessionId(missionId, data.session_id);
  return data;
}
