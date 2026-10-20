# DrishtiGuard Guardian — Mobile App

The Guardian mobile app for the Smart Blind Stick backend. React Native +
Expo + TypeScript, communicating with the real FastAPI backend in this
repository over REST and WebSocket. There is no mock/demo mode: every
screen renders data that came from the backend, and shows "No data
available" / "Device offline" / "No events recorded" when the backend
has nothing to show.

## Prerequisites

- Node.js 18+ and npm
- The backend running (see the repository root `README.md`) — this app
  is useless without it, by design
- Expo Go app on a physical Android/iOS device, **or** an emulator/simulator

## 1. Configure the backend URL

Copy `.env.example` to `.env` and set `EXPO_PUBLIC_API_URL`:

```bash
cp .env.example .env
```

**Same machine as the backend (simulator only):**
```
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000
```

**Physical device on the same Wi-Fi/LAN (the normal case):**
`localhost` on a phone means the phone itself, not your computer.
You must use your computer's LAN IP:

```
EXPO_PUBLIC_API_URL=http://192.168.1.100:8000
```

Find your LAN IP:
- macOS/Linux: `ifconfig | grep "inet "`
- Windows: `ipconfig`

Make sure your phone and dev machine are on the **same Wi-Fi network**,
and that your OS firewall allows inbound connections to port 8000
(the FastAPI backend must be started with `--host 0.0.0.0`, not
`127.0.0.1`, for the phone to reach it — see the backend
`app/main.py` / `uvicorn` invocation in the root README).

**Production:** point this at your deployed backend's HTTPS URL.

## 2. Install and run

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with Expo Go (Android) or the Camera app (iOS), or
press `a`/`i` for an emulator/simulator.

## 3. Sign in

1. Register a Guardian account (real backend record, bcrypt-hashed
   password, JWT issued on success).
2. Power on the Smart Blind Stick so it sends at least one
   `POST /api/device/data` check-in — pairing rejects device IDs that
   have never contacted the backend.
3. Pair the device by its `device_id`.
4. The dashboard, location, safety, and events screens now show real
   data, and the WebSocket connects for live updates.

## Architecture

```
services/api.ts            axios instance, JWT attach + refresh-on-401
services/authService.ts    register / login / logout / me
services/deviceService.ts  pairing, status
services/locationService.ts   latest + history
services/eventService.ts   event history with filters
services/sosService.ts     real SOS trigger (POST /api/sos)
services/contactService.ts emergency contacts CRUD
services/notificationService.ts  Expo push token + local critical alerts
services/websocketService.ts     /ws/device/{id} client, reconnect, heartbeat
context/AuthContext.tsx    session state
context/DeviceContext.tsx  paired devices + live-merged status
hooks/useDeviceSocket.ts   React hook wrapping the WebSocket client
```

Routes use Expo Router with two groups: `(auth)` (login/register) and
`(app)` (dashboard/location/safety/events/sos/contacts/settings/pairing),
gated by `app/_layout.tsx` based on whether a valid session exists.

## Testing performed in this environment

- `npx tsc --noEmit` — clean, 0 errors
- `npx expo export --platform android` — bundled successfully, 1376
  modules resolved, produced a real Hermes bytecode bundle
- `npx expo export --platform ios` — bundled successfully, 1247 modules
- `npx expo config --type public` — app.json resolves without error

## Known limitations (honest, not glossed over)

- **Not tested on a physical Android/iOS device** — this was built and
  bundle-verified in a sandboxed environment with no phone attached.
  Before calling this "production ready," run it against a real device
  on your LAN per the steps above.
- **Server -> device push delivery is unverified.** The app registers a
  real Expo push token with the backend (`POST /api/push/register`,
  persisted in the `push_tokens` table), and locally fires a
  notification immediately for any critical WebSocket event while the
  app is foregrounded/backgrounded-with-socket-alive. But nothing in
  this build calls Expo's push-send API from the backend yet — the
  backend's `notification_service` is still the pre-existing Mock
  implementation for SOS. Wiring a real Expo push send call is a small,
  well-scoped follow-up (see backend `app/services/notification_service.py`).
- **No token blacklist on logout.** Logout is stateless JWT — the
  client discards its tokens, but a still-valid access token isn't
  server-side revoked (only expires naturally, default 30 minutes).
  Acceptable for a first release; add a blacklist/short-lived-token
  strategy if this needs stronger guarantees.
- **`sensor_fusion` and `safety_engine` backend modules don't exist
  yet** in this repository (their feature branches contain no unique
  code beyond `main`). The mobile app is wired to display events from
  those sources whenever the backend starts emitting them (same
  generic `Event` schema as `ai_vision`), but there's nothing to show
  until those modules are built.
