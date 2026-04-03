"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import type { Message } from "@/types/chat";
import styles from "./MessageList.module.css";
import TrajectoryMap from "./TrajectoryMap";

// ─── Helpers ──────────────────────────────────────────────────
function formatUtcTime(date: Date): string {
  return (
    date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }) + " UTC"
  );
}

<<<<<<< Updated upstream
=======
// ─── Tool call display ─────────────────────────────────────────
const TOOL_LABELS: Record<string, string> = {
  get_surface_weather:            "Surface Weather",
  get_winds_aloft:                "Winds Aloft",
  check_notam_airspace:           "NOTAM Check",
  astra_list_balloons:            "Balloon Catalog",
  astra_list_parachutes:          "Parachute Catalog",
  astra_calculate_nozzle_lift:    "Nozzle Lift",
  astra_calculate_balloon_volume: "Balloon Volume",
  astra_run_simulation:           "Monte Carlo Simulation",
  hab_list_hardware:              "HAB Hardware Catalog",
  hab_get_elevation:              "Elevation Lookup",
  hab_calculate_nozzle_lift:      "Nozzle Lift (HAB)",
  hab_calculate_balloon_volume:   "Balloon Volume (HAB)",
  hab_run_simulation:             "HAB Trajectory Simulation",
};

function getArgSummary(name: string, args: Record<string, unknown>): string {
  switch (name) {
    case "get_surface_weather":
    case "get_winds_aloft":
    case "check_notam_airspace":
      return `${args.latitude}°, ${args.longitude}°`;
    case "astra_calculate_nozzle_lift":
    case "astra_calculate_balloon_volume":
      return `${args.balloon_model} · ${args.gas_type}`;
    case "astra_run_simulation":
    case "hab_run_simulation":
      return `${args.balloon_model} · ${args.num_runs ?? 5} runs`;
    default:
      return "";
  }
}

function ToolCallsSection({ toolCalls }: { toolCalls: ToolCallRecord[] }) {
  if (!toolCalls.length) return null;
  return (
    <details className={styles.toolCalls}>
      <summary className={styles.toolCallsSummary}>
        <span className={styles.toolCallsChevron}>▸</span>
        <span className={styles.toolCallsLabel}>
          {toolCalls.length} tool{toolCalls.length !== 1 ? "s" : ""} used
        </span>
      </summary>
      <ul className={styles.toolCallsList}>
        {toolCalls.map((tc, i) => {
          const summary = getArgSummary(tc.name, tc.args);
          return (
            <li key={i} className={styles.toolCallItem}>
              <span className={styles.toolCallDot} />
              <span className={styles.toolCallName}>
                {TOOL_LABELS[tc.name] ?? tc.name}
              </span>
              {summary && (
                <span className={styles.toolCallArgs}>{summary}</span>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}

>>>>>>> Stashed changes
// ─── Message components ────────────────────────────────────────
function AssistantMessage({ message }: { message: Message }) {
  return (
    <div className={styles.assistantCard}>
      <div className={styles.assistantHeader}>
        <span className={styles.assistantLabel}>STRATOS AI</span>
        <span className={styles.assistantTime}>{formatUtcTime(message.createdAt)}</span>
      </div>
      <p className={styles.assistantText}>{message.content}</p>
<<<<<<< Updated upstream
=======
      {message.trajectory && message.trajectory.length > 0 && (
        <TrajectoryMap trajectory={message.trajectory} />
      )}
      {message.toolCalls && message.toolCalls.length > 0 && (
        <ToolCallsSection toolCalls={message.toolCalls} />
      )}
>>>>>>> Stashed changes
    </div>
  );
}

function UserMessage({ message }: { message: Message }) {
  return (
    <div className={styles.userRow}>
      <div className={styles.userBubble}>
        <p className={styles.userText}>{message.content}</p>
      </div>
    </div>
  );
}

// ─── Typing indicator ─────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className={styles.assistantCard}>
      <div className={styles.assistantHeader}>
        <span className={styles.assistantLabel}>STRATOS AI</span>
      </div>
      <div className={styles.typingDots}>
        <span className={styles.dot} style={{ animationDelay: "0ms" }} />
        <span className={styles.dot} style={{ animationDelay: "160ms" }} />
        <span className={styles.dot} style={{ animationDelay: "320ms" }} />
      </div>
    </div>
  );
}

// ─── Empty state (no suggestions — they live above the input) ──
function EmptyState() {
  return (
    <div className={styles.emptyState}>
      <div className={styles.emptyInner}>
        <div className={styles.emptyLogoWrap}>
          <Image
            src="/assets/STRATOS_LOGO_SVG/Color.svg"
            alt="STRATOS"
            width={52}
            height={52}
            priority
          />
        </div>
        <p className={styles.emptyLabel}>STRATOS Mission Chat</p>
        <p className={styles.emptySubtitle}>
          Ask anything about telemetry, trajectory, or flight data.
        </p>
      </div>
    </div>
  );
}

// ─── Main ──────────────────────────────────────────────────────
interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export default function MessageList({
  messages,
  isLoading = false,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className={styles.container}>
      {messages.length === 0 && !isLoading ? (
        <EmptyState />
      ) : (
        <div className={styles.feed}>
          {messages.map((msg) =>
            msg.role === "user"
              ? <UserMessage key={msg.id} message={msg} />
              : <AssistantMessage key={msg.id} message={msg} />
          )}
          {isLoading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
