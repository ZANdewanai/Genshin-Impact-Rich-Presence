# genshin-presence-gui

React + Vite + Tailwind CSS frontend for the Genshin Impact Rich Presence engine. It runs inside a pywebview window (see `../webview_launcher.py`) and talks to the Python backend through `window.pywebview.api` (`../gui/api.py`).

## Development

- `pnpm dev` - Vite dev server on port 8443. Without pywebview the UI runs in demo mode (`src/api.ts` fabricates state).
- `pnpm build` - typecheck (`tsc --noEmit`) + production build into `dist/`, which `webview_launcher.py` serves.

## Project Structure

- `src/main.tsx` - entrypoint; imports `src/index.css`, mounts `src/App.tsx`
- `src/App.tsx` - app shell: header, tab nav, routed tab content
- `src/api.ts` - pywebview bridge types/helpers, `fetchState`, `fmtElapsed`, demo fallback
- `src/hooks.ts` - `useSettings`, `useDebug`, `useBackendState` (1s poll), `useLogs`
- `src/types.ts`, `src/constants.ts` - shared types and element/rarity colors
- `src/components/` - `TabBar`, `PresenceTab` (Live), `SettingsTab`, `LogsTab`, `AboutTab`, `CharacterCard`, `ui.tsx` primitives, `Icons.tsx`
- `src/index.css` - Tailwind v4 import, theme tokens, shared component classes
- `../api.py` - Python side of the bridge: `get_state`, `toggle_connection`, settings/debug/log endpoints

## Backend contract

- Engine state comes from `get_state()` (poll ~1s). `running=false` means the engine subprocess is stopped.
- Settings persist to `shared_config.json` via `get_settings`/`save_settings`; identity keys hot-reload, `useGpu` applies on next engine start.
- Debug flags and the log ring buffer are exposed via `get_debug`/`set_debug`/`get_logs`.
