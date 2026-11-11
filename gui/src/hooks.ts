import { useCallback, useEffect, useRef, useState } from "react";
import type { BackendState, DebugConfig, Settings } from "./types";
import { api, fetchState, hasBackend } from "./api";

const DEFAULT_SETTINGS: Settings = {
  username: "",
  mcAether: true,
  wandererName: "Wanderer",
  manekinName: "Manekin",
  manekinaName: "Manekina",
  useGpu: true,
};

const DEFAULT_DEBUG: DebugConfig = {
  debugMode: false,
  debugCharacterMode: false,
  debugStaticImage: false,
  debugStaticImagePath: "",
};

/* Wait for the pywebview bridge to finish injecting, then call `fn` once.
 * The API object can appear a few hundred ms after first paint. */
function whenApiReady(fn: () => void) {
  if (api()?.get_settings) return fn();
  let attempts = 0;
  const poll = () => {
    if (api() || ++attempts >= 100) return fn();
    setTimeout(poll, 200);
  };
  poll();
}

export function useSettings() {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  useEffect(() => {
    whenApiReady(async () => {
      try {
        const s = await api()?.get_settings?.();
        if (s && Object.keys(s).length) {
          setSettings(prev => ({ ...prev, ...s }));
        }
      } catch { /* bridge not ready or engine offline */ }
    });
  }, []);

  const updateSettings = useCallback((patch: Partial<Settings>) => {
    setSettings(prev => ({ ...prev, ...patch }));
    api()?.save_settings?.(patch)?.catch(() => {});
  }, []);

  return { settings, updateSettings };
}

export function useDebug() {
  const [debug, setDebug] = useState<DebugConfig>(DEFAULT_DEBUG);
  const debugRef = useRef(debug);
  debugRef.current = debug;

  useEffect(() => {
    whenApiReady(async () => {
      try {
        const d = await api()?.get_debug?.();
        if (d) setDebug({ ...DEFAULT_DEBUG, ...d });
      } catch { /* ignore */ }
    });
  }, []);

  const setDebugFlags = useCallback((patch: Partial<DebugConfig>) => {
    const next = { ...debugRef.current, ...patch };
    debugRef.current = next;
    setDebug(next);
    api()?.set_debug?.(
      next.debugMode,
      next.debugCharacterMode,
      next.debugStaticImage,
      next.debugStaticImagePath,
    )?.catch(() => {});
  }, []);

  return { debug, setDebugFlags };
}

/* Polls get_state() once per second. `demoRunning` only matters outside
 * pywebview, where fetchState fabricates a demo BackendState. */
export function useBackendState(demoRunning: boolean) {
  const [state, setState] = useState<BackendState | null>(null);
  const lastJson = useRef("");

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const s = await fetchState(demoRunning);
        if (!alive) return;
        // Skip the re-render when the payload is unchanged - the JSON
        // stringify is cheaper than diffing the tree every second.
        const json = JSON.stringify(s);
        if (json !== lastJson.current) {
          lastJson.current = json;
          setState(s);
        }
      } catch { /* keep last known state */ }
    };
    tick();
    const timer = setInterval(tick, 1000);
    return () => { alive = false; clearInterval(timer); };
  }, [demoRunning]);

  return state;
}

export function useLogs(enabled: boolean) {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    if (!enabled || !hasBackend()) {
      setLogs([]);
      return;
    }
    let alive = true;
    const tick = async () => {
      try {
        const lines = await api()?.get_logs?.();
        if (alive && Array.isArray(lines)) setLogs(lines);
      } catch { /* ignore */ }
    };
    tick();
    const timer = setInterval(tick, 1000);
    return () => { alive = false; clearInterval(timer); };
  }, [enabled]);

  return logs;
}
