"use client";

import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import type { TrajectoryPoint } from "@/types/chat";

// Fix Leaflet's broken default icon paths under webpack
delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Props {
  trajectory: TrajectoryPoint[];
}

function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 1) {
      map.fitBounds(positions, { padding: [24, 24] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

export default function TrajectoryMapClient({ trajectory }: Props) {
  if (!trajectory.length) return null;

  const burstIdx = trajectory.reduce(
    (maxI, pt, i) => (pt.alt > trajectory[maxI].alt ? i : maxI),
    0,
  );
  const burst = trajectory[burstIdx];
  const landing = trajectory[trajectory.length - 1];
  const launch = trajectory[0];
  const positions: [number, number][] = trajectory.map((p) => [p.lat, p.lng]);

  return (
    <MapContainer
      center={[launch.lat, launch.lng]}
      zoom={9}
      style={{ height: "400px", width: "100%", borderRadius: "8px", marginTop: "12px" }}
      scrollWheelZoom={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds positions={positions} />
      <Polyline positions={positions} pathOptions={{ color: "#3b82f6", weight: 2 }} />
      <CircleMarker
        center={[launch.lat, launch.lng]}
        radius={7}
        pathOptions={{ color: "#16a34a", fillColor: "#16a34a", fillOpacity: 1 }}
      >
        <Popup>Launch</Popup>
      </CircleMarker>
      <CircleMarker
        center={[burst.lat, burst.lng]}
        radius={7}
        pathOptions={{ color: "#f97316", fillColor: "#f97316", fillOpacity: 1 }}
      >
        <Popup>Burst: {burst.alt.toFixed(0)} m ASL</Popup>
      </CircleMarker>
      <CircleMarker
        center={[landing.lat, landing.lng]}
        radius={7}
        pathOptions={{ color: "#dc2626", fillColor: "#dc2626", fillOpacity: 1 }}
      >
        <Popup>Landing</Popup>
      </CircleMarker>
    </MapContainer>
  );
}
