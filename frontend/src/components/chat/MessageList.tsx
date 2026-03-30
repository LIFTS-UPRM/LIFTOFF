"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import type { Message } from "@/types/chat";
import styles from "./MessageList.module.css";

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

// ─── Message components ────────────────────────────────────────
function AssistantMessage({ message }: { message: Message }) {
  return (
    <div className={styles.assistantCard}>
      <div className={styles.assistantHeader}>
        <span className={styles.assistantLabel}>STRATOS AI</span>
        <span className={styles.assistantTime}>{formatUtcTime(message.createdAt)}</span>
      </div>
      <p className={styles.assistantText}>{message.content}</p>
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
