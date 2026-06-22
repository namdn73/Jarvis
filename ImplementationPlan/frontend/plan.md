# Frontend Implementation Plan

## Confirmed Design Decisions

| Concern | Decision |
|---|---|
| Styling | Tailwind CSS v4 — utility classes, dark JARVIS palette |
| State | `useReducer` + `useContext` — one reducer switching on 5 WS message types |
| WebSocket | Native browser `WebSocket` in custom `useWebSocket` hook |
| Waveform | HTML `<canvas>` + `requestAnimationFrame` — outside React render cycle |
| Font | `Orbitron` (headings/labels) + `Inter` (body) — Google Fonts |
| Animations | Tailwind CSS only — `animate-pulse`, custom keyframes, `transition-all` |
| Sphere | Canvas 2D — 150 nodes, Fibonacci distribution, cyan glow, no Three.js |
| Layout | `IDLE`: fullscreen sphere. `ACTIVE`: sphere shrinks top-left, split view slides in |
| HTTP client | Native `fetch` — 3 endpoints, no library |
| Follow-up UI | No countdown indicator — backend sends STANDBY → UI fades back to sphere |
| Mouse wake | Mouse movement while in sphere → return to split view |
| Testing | `vitest` + React Testing Library — reducer transitions + WS hook |

---

## Folder Structure

```
frontend/
├── index.html              # Orbitron + Inter Google Fonts import
├── package.json
├── vite.config.ts
├── tailwind.config.ts      # custom colors, Orbitron font, keyframes
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx              # IDLE vs ACTIVE layout + mouse activity listener
    ├── types.ts             # JarvisStatus, ResultItem, WsMessage, JarvisState types
    ├── context/
    │   └── JarvisContext.tsx  # useReducer + Context + dispatch export
    ├── hooks/
    │   ├── useWebSocket.ts    # native WS connect/reconnect, dispatches to reducer
    │   └── useMouseActivity.ts # mousemove → wake from IDLE to ACTIVE
    ├── components/
    │   ├── SphereCanvas.tsx   # fullscreen Canvas 2D JARVIS sphere
    │   ├── LeftPanel.tsx      # status badge + waveform + conversation log
    │   ├── RightPanel.tsx     # result cards list
    │   ├── WaveformCanvas.tsx # Canvas waveform driven by amplitude values
    │   ├── ResultCard.tsx     # individual card: title, source, snippet, link
    │   ├── StatusBadge.tsx    # LISTENING / PROCESSING / RESPONDING indicator
    │   └── ConversationLog.tsx # scrollable transcript + Jarvis tts_text entries
    └── tests/
        ├── reducer.test.ts    # state transition tests
        └── useWebSocket.test.ts # reconnect logic tests
```

---

## package.json

```json
{
  "dependencies": {
    "react": "^18",
    "react-dom": "^18"
  },
  "devDependencies": {
    "typescript": "^5",
    "vite": "^5",
    "@vitejs/plugin-react": "^4",
    "tailwindcss": "^4",
    "@tailwindcss/vite": "^4",
    "vitest": "^1",
    "@testing-library/react": "^14",
    "@testing-library/user-event": "^14",
    "jsdom": "^24"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "test": "vitest"
  }
}
```

---

## Tailwind Config (`tailwind.config.ts`)

```ts
colors: {
  jarvis: {
    bg:     '#000000',
    panel:  '#080d14',
    cyan:   '#00c9ff',
    blue:   '#1ac6ff',
    border: 'rgba(0,201,255,0.25)',
    glow:   'rgba(0,201,255,0.12)',
  }
}
fontFamily: {
  orbitron: ['Orbitron', 'sans-serif'],
  inter:    ['Inter', 'sans-serif'],
}
// custom keyframes: fadeIn, glowPulse, slideInRight
```

---

## Module-by-Module Plan

### `types.ts`
```ts
type JarvisStatus = 'STANDBY' | 'GREETING' | 'LISTENING' | 'PROCESSING' | 'RESPONDING' | 'ACTIVE_WINDOW'
type ResultItem   = { title: string; url: string; snippet: string; source: string }
type WsMessage    = { type: 'state_change'|'transcript'|'results'|'amplitude'|'tts_text'; payload: any }
type JarvisState  = { status: JarvisStatus; transcript: string; results: ResultItem[]; amplitude: number; log: string[] }
```

### `context/JarvisContext.tsx`
- `useReducer(jarvisReducer, initialState)` — reducer switches on `WsMessage.type`:
  - `state_change` → update `status`
  - `transcript` → set `transcript`, append to `log`
  - `results` → replace `results` array entirely
  - `amplitude` → update `amplitude` float
  - `tts_text` → append Jarvis line to `log`
- Export `JarvisContext` and `useJarvis()` convenience hook

### `hooks/useWebSocket.ts`
- Connect to `ws://localhost:8000/ws` on mount
- `onmessage`: parse JSON → `dispatch(message)`
- `onclose`: reconnect after 2s delay via `useEffect` cleanup + `setTimeout`
- Expose `{ connected: boolean }` — used by `StatusBadge` to show disconnected state

### `hooks/useMouseActivity.ts`
- `window.addEventListener('mousemove', handler)`
- If `layout === 'IDLE'` → call `setLayout('ACTIVE')`
- Debounce at 500ms to avoid thrashing

### `App.tsx`
- `layout: 'IDLE' | 'ACTIVE'` local state
- `IDLE`: render `<SphereCanvas fullscreen />` only
- `ACTIVE`: render `<SphereCanvas orb />` + `<LeftPanel />` + `<RightPanel />`
  - `slideInRight` CSS animation on `<RightPanel>` first render
- Transition to `IDLE` when `status === 'STANDBY'` (via `useEffect` watching context)
- `useMouseActivity` triggers `setLayout('ACTIVE')` while in `IDLE`

### `SphereCanvas.tsx`
- Canvas fills container (fullscreen in IDLE, fixed 120×120px orb in ACTIVE)
- Sphere generation: Fibonacci lattice → 150 points on unit sphere surface
- Per-frame loop (`requestAnimationFrame`):
  1. Rotate all points by `(angleX += 0.003, angleY += 0.005)`
  2. Project 3D → 2D with focal length
  3. Draw lines between points within distance threshold (cyan, low opacity)
  4. Draw dots at each point (cyan, radius scaled by depth/z)
- Pulse mode when `status` is `GREETING`, `LISTENING`, or `RESPONDING`:
  - Node radius and line opacity scale with `amplitude` value from context
- Glow: `ctx.shadowColor = '#00c9ff'`, `ctx.shadowBlur = 8`

### `WaveformCanvas.tsx`
- Reads `amplitude` from `useJarvis()`
- Maintains rolling buffer of last 60 values
- Draws vertical bars (bar chart, centre-aligned, mirrored top/bottom)
- Only animates when `status === 'LISTENING' || 'RESPONDING'`
- Bars: cyan fill with glow shadow

### `LeftPanel.tsx`
- Top: `<SphereCanvas orb />` (120px) + `<StatusBadge />`
- Middle: `<WaveformCanvas />` (shown during LISTENING/RESPONDING)
- Bottom: `<ConversationLog />` — scrollable, `overflow-y-auto`

### `RightPanel.tsx`
- Map `results` → `<ResultCard />` (max 5)
- If `results` is empty and `status !== 'STANDBY'`: show loading skeleton
- Cards fade in with `animate-fadeIn` stagger via `animation-delay` inline style

### `ResultCard.tsx`
- Dark panel: `bg-jarvis-panel border border-jarvis-border`
- Hover: `hover:border-jarvis-cyan hover:shadow-jarvis-glow transition-all duration-300`
- Shows: source badge (cyan), title, snippet, "Open →" link
- If `url` is empty (knowledge answer): hide link

### `StatusBadge.tsx`
Colour map:
- `STANDBY` / disconnected → dim gray
- `GREETING` / `LISTENING` → cyan + `animate-pulse`
- `PROCESSING` → amber + `animate-pulse`
- `RESPONDING` → green
- `ACTIVE_WINDOW` → cyan (steady, no pulse)

### `ConversationLog.tsx`
- Two entry types: user transcript (right-aligned, white) and Jarvis tts_text (left-aligned, cyan)
- Auto-scrolls to bottom on new entry (`useEffect` + `ref.scrollIntoView()`)

---

## Key Patterns

### Layout Transition (IDLE → ACTIVE)
```tsx
// App.tsx
useEffect(() => {
  if (status !== 'STANDBY') setLayout('ACTIVE')
  else setLayout('IDLE')
}, [status])
```

### Sphere Pulse from Amplitude
```ts
// SphereCanvas — inside draw loop
const pulse = status === 'LISTENING' ? 1 + amplitude * 2 : 1
ctx.arc(x, y, baseRadius * pulse * depthScale, 0, Math.PI * 2)
```

### WS Reconnect
```ts
// useWebSocket.ts
ws.onclose = () => setTimeout(() => connect(), 2000)
```

---

## Verification

1. `npm install` — no errors
2. `npm run dev` — Vite starts, opens at `localhost:5173`
3. App loads with fullscreen rotating cyan sphere on black background
4. Move mouse → nothing (backend not running, layout stays IDLE until WS connects)
5. Start backend → WS connects → `StatusBadge` shows STANDBY
6. Say "Jarvis" → sphere pulses → split view slides in from right
7. Results appear as glowing cards on the right panel
8. Backend sends STANDBY → UI fades back to fullscreen sphere
9. `npm run test` — reducer and WS hook tests pass
