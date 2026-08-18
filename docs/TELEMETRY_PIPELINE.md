# Telemetry Pipeline

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: Backend (FastAPI, ingestion), Hardware/Ground Station (receiver), Frontend (WebSocket consumer)

---

## Overview

The Telemetry Pipeline ingests live sensor data from the balloon receiver, streams it to active WebSocket clients (In-Flight dashboard), and archives it for postflight analysis.

**Flow**: Receiver (GPS, temperature, etc.) → FastAPI ingestion → WebSocket broadcast → Frontend dashboard + Archive

---

## Architecture

### Phases

#### 1. Pre-Flight (Receiver Offline)
- Receiver not yet operational
- Ground station testing only
- Telemetry endpoint rejects WebSocket connections (returns 403)

#### 2. In-Flight (Active Streaming)
- Receiver transmits sensor data to ground station
- Ground station forwards to STRATOS `/flights/{id}/telemetry/ingest` endpoint
- STRATOS broadcasts to all connected WebSocket clients on `/flights/{id}/telemetry`

#### 3. Post-Flight (Archive)
- Payload recovered; receiver offline
- Postflight telemetry archive ingested separately
- Stored for analysis phase

---

## Ingestion Endpoint

### POST `/flights/{id}/telemetry/ingest`

Ground station sends telemetry records.

**Authorization**: API key or service-level JWT (for MCP integrations)

**Request** (streaming JSON objects, one per line or batch):
```
POST /flights/flight_001/telemetry/ingest

{
  "timestamp": "2026-07-28T08:15:30.123Z",
  "altitude_m": 85000,
  "temperature_c": -45.2,
  "pressure_pa": 1050,
  "gps_lat": 18.2105,
  "gps_lon": -67.0945,
  "gps_accuracy_m": 15,
  "irradiance_w_m2": 1050,
  "battery_v": 4.8,
  "signal_strength_dbm": -95,
  "sub_mission": "SCRAM",
  "sensor_id": "temp_sensor_001"
}
```

**Response** (202 Accepted):
```json
{
  "success": true,
  "data": {
    "records_ingested": 1,
    "flight_id": "flight_001",
    "timestamp": "2026-07-28T08:15:30.500Z"
  }
}
```

**Behavior**:
- Returns 202 immediately (fire-and-forget)
- Records queued for broadcasting
- If flight state ≠ "In Flight", returns 409 Conflict
- No authentication required (ground station trusted IP or API key)

---

## WebSocket Streaming

### WS `/flights/{id}/telemetry`

Frontend opens persistent WebSocket to receive live telemetry.

**Connection**:
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/flights/flight_001/telemetry');

ws.onmessage = (event) => {
  const telemetry = JSON.parse(event.data);
  // Update dashboard with new altitude, temperature, etc.
  updateDashboard(telemetry);
};
```

**Message Format** (same as ingest):
```json
{
  "timestamp": "2026-07-28T08:15:30.123Z",
  "altitude_m": 85000,
  "temperature_c": -45.2,
  "pressure_pa": 1050,
  "gps_lat": 18.2105,
  "gps_lon": -67.0945,
  "gps_accuracy_m": 15,
  "irradiance_w_m2": 1050,
  "battery_v": 4.8,
  "signal_strength_dbm": -95,
  "sub_mission": "SCRAM",
  "sensor_id": "temp_sensor_001"
}
```

**Broadcast Behavior**:
- STRATOS receives telemetry record via `/ingest`
- Immediately broadcasts to all connected WebSocket clients for that flight
- Latency: ~100ms (network + processing)

**Connection Lifecycle**:
- Client connects during "In Flight" phase
- Receives all new telemetry until flight transitions to "Recovered"
- Connection auto-closes when flight state changes
- Reconnecting resumes from latest (no backfill; real-time only)

**Reconnection**:
- If connection drops, frontend should reconnect
- Dashboard shows "telemetry offline" if WebSocket disconnected for >10s

---

## Data Storage

### In-Memory Cache (During Flight)

STRATOS maintains a rolling cache of latest telemetry (last 1000 records or 1 hour, whichever smaller).

**Purpose**: Dashboard queries recent history without database roundtrip.

**Implementation**: In-memory dict keyed by flight_id.

### Persistent Archive (Post-Flight)

After flight transitions to "Recovered", telemetry archived to:
- **Option A**: PostgreSQL `telemetry_records` table
- **Option B**: External time-series DB (for future scaling)

**Fields**:
```
id: UUID
flight_id: UUID
timestamp: datetime
altitude_m: float
temperature_c: float
pressure_pa: float
gps_lat: float
gps_lon: float
gps_accuracy_m: float
irradiance_w_m2: float
battery_v: float
signal_strength_dbm: float
sub_mission: string
sensor_id: string
ingested_at: datetime (server time)
```

**Retention**: Permanent (for scientific archive).

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Flight state ≠ "In Flight" | Ingest returns 409; WebSocket connection rejected |
| Malformed telemetry record | Log error, skip record, continue broadcasting others |
| WebSocket client disconnects | Remove from broadcast list; no error |
| Receiver offline (no ingest for >5min) | Dashboard shows "no recent data" warning |
| Timestamp out of order | Accept and store (clock skew normal for receivers) |
| Duplicate records (same timestamp, sensor_id) | Deduplicate by timestamp + sensor_id; keep first |

---

## Scalability Notes

**Current** (single receiver):
- DirectFastAPI ingestion sufficient
- In-memory cache handles 100s of records/sec
- WebSocket broadcast O(n) clients

**Future** (multiple balloons, higher throughput):
- Switch to message queue (Redis Pub/Sub or RabbitMQ)
- Move archive to time-series DB (InfluxDB, TimescaleDB)
- Scale WebSocket broadcast with horizontal pod autoscaling

---

## Testing

### Simulator

Mock receiver sends telemetry records:
```bash
python test_telemetry_sim.py --flight_id flight_001 --rate 1hz --duration 600s
```

### Live Test

Connect dashboard to active flight:
```bash
npm run dev  # Frontend at localhost:3000
# Open dashboard, watch telemetry stream
```

---

## Next: Implement FastAPI handlers

- `telemetry.py`: Ingest endpoint, WebSocket handler
- `telemetry_cache.py`: In-memory cache, rollover logic
