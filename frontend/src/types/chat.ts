export type MessageRole = "user" | "assistant";

export interface ToolCallRecord {
  name: string;
  args: Record<string, unknown>;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: Date;
  toolCalls?: ToolCallRecord[];
}
