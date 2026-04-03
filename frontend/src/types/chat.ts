export type MessageRole = "user" | "assistant";

<<<<<<< Updated upstream
=======
export interface TrajectoryPoint {
  lat: number;
  lng: number;
  alt: number;
}

export interface ToolCallRecord {
  name: string;
  args: Record<string, unknown>;
}

>>>>>>> Stashed changes
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: Date;
<<<<<<< Updated upstream
=======
  toolCalls?: ToolCallRecord[];
  trajectory?: TrajectoryPoint[];
>>>>>>> Stashed changes
}
