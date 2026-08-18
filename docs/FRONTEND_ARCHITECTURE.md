# Frontend Architecture

**Status**: Architecture specification  
**Last Updated**: 2026-07-22  
**Audience**: Frontend developers (React/Next.js), Frontend leads

---

## Overview

STRATOS frontend is a Next.js 16 / React 19 / TypeScript monorepo with two primary views:

1. **Chat** (`/chat`) — AI copilot interface for mission planning/control
2. **Dashboard** (`/dashboard`) — Real-time telemetry visualization during "In Flight" phase

Both share mission context, auth, and API layer. Deployment: single Next.js instance serving both routes.

---

## Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout, auth wrapper
│   │   ├── page.tsx            # Login page
│   │   ├── chat/
│   │   │   └── page.tsx        # Chat interface
│   │   ├── dashboard/
│   │   │   └── page.tsx        # Telemetry dashboard
│   │   ├── missions/
│   │   │   ├── page.tsx        # Mission list
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Mission detail
│   │   └── globals.css
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── InputBox.tsx
│   │   ├── Dashboard/
│   │   │   ├── TelemetryView.tsx
│   │   │   ├── AltitudeChart.tsx
│   │   │   ├── MapView.tsx
│   │   │   └── StatusBar.tsx
│   │   └── Common/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts       # Axios/fetch wrapper with auth
│   │   │   ├── missions.ts     # Mission endpoints
│   │   │   ├── chat.ts         # Chat endpoint
│   │   │   └── telemetry.ts    # Telemetry WebSocket
│   │   ├── auth/
│   │   │   ├── supabaseClient.ts
│   │   │   └── useAuth.ts      # React hook
│   │   └── utils/
│   │       ├── formatters.ts   # Date, number formatting
│   │       └── validators.ts
│   ├── types/
│   │   ├── chat.ts
│   │   ├── mission.ts
│   │   ├── flight.ts
│   │   ├── telemetry.ts
│   │   └── api.ts
│   └── hooks/
│       ├── useMission.ts       # Fetch mission, revalidate
│       ├── useChat.ts          # Chat message state
│       ├── useTelemetry.ts     # WebSocket telemetry stream
│       └── useAuth.ts          # Auth state, logout
├── public/
│   └── (images, icons)
├── package.json
├── tsconfig.json
├── next.config.js
└── .env.local
```

---

## Core Pages

### Login (`/`)

**Purpose**: Authenticate user

**Components**:
- Email input
- Password input
- "Sign In" button
- Link to signup (if allowed)

**Flow**:
1. User enters email/password
2. Calls `supabaseClient.auth.signIn()`
3. On success, stores token in localStorage
4. Redirects to `/missions`

---

### Mission List (`/missions`)

**Purpose**: Browse available missions

**Components**:
- Mission table/list (name, state, team size, last updated)
- Filters (state=Planning|Ready|Active|Complete)
- Create mission button
- Search bar

**Flow**:
1. Page loads, fetches `/missions?limit=20&offset=0`
2. Displays list with pagination
3. User clicks mission → navigates to `/chat?mission_id={id}`

---

### Chat (`/chat`)

**Purpose**: AI-assisted mission planning/control

**Required Params**:
- `mission_id`: UUID (query param)
- Optional: `flight_id` (if active flight exists)

**Layout**:
```
┌─────────────────────────────────┐
│ Header (Mission: ASCENT)         │
├──────────────┬──────────────────┤
│ Sidebar      │ Main Chat Area   │
│ • Flights    │ ┌──────────────┐ │
│ • Team       │ │ Messages     │ │
│ • Skills     │ │ ............ │ │
│              │ │ ............ │ │
│              │ │ ............ │ │
│              │ ├──────────────┤ │
│              │ │ Input Box    │ │
│              │ │ [Message..] ▶ │ │
│              │ └──────────────┘ │
└──────────────┴──────────────────┘
```

**Components**:
- **Sidebar**:
  - Mission info (state, launch date)
  - Flight list (select active flight)
  - Team members
  - Skills list

- **Message List**:
  - User messages (right-aligned, blue)
  - Copilot responses (left-aligned, gray)
  - Tool call summaries (italics, "Checked weather forecast...")
  - Trajectory artifacts (map preview)

- **Input Box**:
  - Text input
  - Send button
  - Tool group toggles (weather, trajectory, airspace)

**State Management**:
- `useChat()` hook for message history
- `useMission()` hook for mission context
- `useAuth()` hook for user auth

---

### Dashboard (`/dashboard`)

**Purpose**: Real-time telemetry monitoring during "In Flight" phase

**Required Params**:
- `flight_id`: UUID (query param, required)

**Layout**:
```
┌────────────────────────────────────┐
│ Flight ASCENT • In Flight          │
├────────────┬──────────────────────┤
│ Status Box │ Telemetry Charts     │
│ • Altitude │ ┌──────────────────┐ │
│ • Temp     │ │ Altitude (m)     │ │
│ • Signal   │ │ 95K ╱╲╱╲╱╲╱╲    │ │
│ • Battery  │ │     Time →        │ │
│            │ └──────────────────┘ │
│ Recovery   │ ┌──────────────────┐ │
│ • Location │ │ Temperature (°C) │ │
│ • Status   │ │ -50 ╱╲ ╱╲ ╱╲    │ │
│            │ │     Time →        │ │
│            │ └──────────────────┘ │
├────────────┴──────────────────────┤
│ Map View (GPS tracking)            │
│ Current: 18.210°N, 67.094°W        │
│ Predicted: 18.205°N, 67.100°W      │
└────────────────────────────────────┘
```

**Components**:
- **Status Box**:
  - Current altitude
  - Temperature
  - Battery voltage
  - Signal strength
  - Color-coded warnings (red if signal lost >10s)

- **Telemetry Charts**:
  - Altitude vs. time (line chart)
  - Temperature vs. time
  - Battery voltage vs. time
  - Scrolling window (last 30 min)

- **Map View**:
  - Current GPS position (blue marker)
  - Predicted landing zone (red circle)
  - Flight path (line trail)
  - Uses Mapbox or OSM

**State Management**:
- `useTelemetry()` hook for WebSocket stream
- Real-time chart updates (recharts or Chart.js)
- Auto-reconnect WebSocket if disconnected

---

## Shared Hooks

### `useAuth()`

```typescript
const { user, isLoading, logout } = useAuth();
```

**Returns**:
- `user`: { id, email, roles }
- `isLoading`: boolean
- `logout()`: function

### `useMission(missionId)`

```typescript
const { mission, flights, team, isLoading, refetch } = useMission(missionId);
```

**Returns**:
- `mission`: Mission entity
- `flights`: Flight[]
- `team`: TeamMember[]
- `isLoading`: boolean
- `refetch()`: refresh from API

### `useChat(missionId, flightId?)`

```typescript
const { messages, sendMessage, isLoading } = useChat(missionId, flightId);
```

**Returns**:
- `messages`: { role, content, toolCalls, timestamp }[]
- `sendMessage(text, toolGroups)`: send user message
- `isLoading`: boolean

### `useTelemetry(flightId)`

```typescript
const { telemetry, isConnected, error } = useTelemetry(flightId);
```

**Returns**:
- `telemetry`: latest telemetry record
- `isConnected`: WebSocket connected
- `error`: connection error message

---

## API Layer

### `lib/api/client.ts`

Axios/fetch wrapper with automatic JWT injection:

```typescript
const apiClient = createClient({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL,
  getToken: () => localStorage.getItem('auth_token')
});

export const fetchMission = (id: string) => apiClient.get(`/missions/${id}`);
export const sendChatMessage = (missionId: string, message: string) =>
  apiClient.post(`/missions/${missionId}/chat`, { message });
```

### `lib/api/telemetry.ts`

WebSocket wrapper:

```typescript
export const connectTelemetry = (flightId: string, onMessage: (data) => void) => {
  const ws = new WebSocket(`${BACKEND_WS_URL}/flights/${flightId}/telemetry`);
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  return ws; // caller responsible for ws.close()
};
```

---

## State Management

**Simple approach**: React Context + hooks + localStorage for auth token.

**If complexity grows**:
- Upgrade to Redux or Zustand for global state
- Persist mission context to localStorage

**Current approach** (preferred):
```typescript
// context/AuthContext.tsx
export const AuthProvider: React.FC<{ children }> = ({ children }) => {
  const [user, setUser] = useState(null);
  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// hooks/useAuth.ts
export const useAuth = () => {
  const { user } = useContext(AuthContext);
  return user;
};
```

---

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://xyzabc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
MAPBOX_ACCESS_TOKEN=...  # For map view
```

---

## Build & Deploy

### Development

```bash
npm install
npm run dev  # http://localhost:3000
```

### Production

```bash
npm run build  # TypeScript check + optimize
npm run start  # Production server
```

### CI/CD

```bash
npm ci
npm run lint  # ESLint
npm run build # TypeScript check
npm audit --audit-level=high
```

---

## Accessibility & UX

- All interactive elements keyboard-navigable
- ARIA labels on buttons/forms
- Dark mode support (prefers-color-scheme)
- Responsive layout (mobile-first)
- Error messages clear and actionable

---

## Next: Implement React components

- Chat UI components (MessageList, InputBox)
- Dashboard charts (recharts integration)
- WebSocket reconnection logic
