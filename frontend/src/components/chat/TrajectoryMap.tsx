import dynamic from "next/dynamic";
import type { TrajectoryPoint } from "@/types/chat";

interface TrajectoryMapProps {
  trajectory: TrajectoryPoint[];
}

const TrajectoryMapClient = dynamic(
  () => import("./TrajectoryMapClient"),
  { ssr: false },
);

export default function TrajectoryMap({ trajectory }: TrajectoryMapProps) {
  if (!trajectory || trajectory.length < 2) return null;
  return <TrajectoryMapClient trajectory={trajectory} />;
}
