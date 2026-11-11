import type { BackendState, DebugConfig, Settings } from "./types";

/* Bridge to the pywebview JS-API exposed by gui/api.py. Everything is
 * optional: in a plain browser (vite dev) none of it exists and the UI
 * falls back to demo data. */
interface PywebviewApi {
  get_state(): Promise<BackendState>;
  toggle_connection(): Promise<{ running: boolean }>;
  get_settings?(): Promise<Partial<Settings>>;
  save_settings?(patch: Partial<Settings>): Promise<{ ok: boolean }>;
  get_logs?(): Promise<string[]>;
  get_debug?(): Promise<DebugConfig>;
  set_debug?(debugMode: boolean, debugCharacterMode: boolean, debugStaticImage: boolean, debugStaticImagePath: string): Promise<{ ok: boolean }>;
}

declare global {
  interface Window {
    pywebview?: { api: PywebviewApi };
  }
}

export const hasBackend = (): boolean =>
  typeof window !== "undefined" && !!window.pywebview?.api;

export const api = (): PywebviewApi | null => window.pywebview?.api ?? null;

export const fmtElapsed = (ts: number | null | undefined): string => {
  if (!ts) return "—";
  const secs = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
};

/* Demo state used only when the UI runs outside pywebview (vite dev). */
const DEMO_STATE: BackendState = {
  running: true,
  location: "Liyue Harbor",
  activity: "Exploring the open world",
  timestamp: Date.now() / 1000 - 754,
  party: [
    { name: "Kamisato Ayaka", element: "cryo", rarity: 5, imageUrl: "" },
    { name: "Xingqiu", element: "hydro", rarity: 4, imageUrl: "" },
    { name: "Zhongli", element: "geo", rarity: 5, imageUrl: "" },
    { name: "Kuki Shinobu", element: "electro", rarity: 4, imageUrl: "" },
    null,
  ],
  active_character_index: 0,
  discord_details: "Exploring Teyvat",
  discord_state: "In Liyue Harbor",
  discord_large_image: "char_kamisato_ayaka",
  discord_large_text: "Kamisato Ayaka",
  discord_small_image: "",
  discord_small_text: "",
};

export const fetchState = async (demoRunning = true): Promise<BackendState> => {
  const backend = api();
  if (backend) return backend.get_state();
  // Simulate the ~1s engine write cadence so timers tick realistically.
  await new Promise(r => setTimeout(r, 50));
  return { ...DEMO_STATE, running: demoRunning, party: [...DEMO_STATE.party] };
};
