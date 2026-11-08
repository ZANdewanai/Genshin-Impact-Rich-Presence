import type { BackendState, Character, Settings } from "./types";

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_state(): Promise<BackendState>;
        toggle_connection(): Promise<{ running: boolean }>;
        get_settings?(): Promise<Partial<Settings>>;
        save_settings?(patch: Partial<Settings>): Promise<{ ok: boolean }>;
        get_logs?(): Promise<string[]>;
        get_debug?(): Promise<{ debugMode: boolean; debugCharacterMode: boolean; debugStaticImage: boolean; debugStaticImagePath: string }>;
        set_debug?(debugMode: boolean, debugCharacterMode: boolean, debugStaticImage: boolean, debugStaticImagePath: string): Promise<{ ok: boolean }>;
      };
    };
  }
}

export const hasBackend = (): boolean =>
  typeof window !== "undefined" && !!window.pywebview;

export const fmtElapsed = (ts: number | null): string => {
  if (!ts) return "-";
  const secs = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return h > 0 ? `${h} hour ${m} min` : `${m} min`;
};

export const fetchState = async (demoConnected: boolean): Promise<BackendState> => {
  if (hasBackend()) return window.pywebview!.api.get_state();
  return Promise.resolve({
    running: demoConnected,
    location: LOCATIONS[0],
    activity: ACTIVITIES[0],
    timestamp: DEMO_STARTED_AT,
    party: [
      { name: "ZANdewanai", element: "pyro", level: 90, rarity: 5, imageUrl: "https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/refs/heads/main/resources/assets/images/characters/char_kibble.png" },
      { name: "Qiqi", element: "cryo", level: 80, rarity: 5, imageUrl: "https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/refs/heads/main/resources/assets/images/characters/char_qiqi.png" },
      { name: "Keqing", element: "electro", level: 75, rarity: 5, imageUrl: "https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/refs/heads/main/resources/assets/images/characters/char_keqing.png" },
    ],
    active_character_index: 0,
  });
};

// Re-export constants used by fetchState
import { LOCATIONS, ACTIVITIES, DEMO_STARTED_AT } from "./constants";
export { LOCATIONS, ACTIVITIES, DEMO_STARTED_AT };