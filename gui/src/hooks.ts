import { useState, useEffect, useRef, useCallback } from "react";
import type { Settings, DebugConfig, BackendState } from "./types";
import { hasBackend, fetchState, fmtElapsed } from "./utils";

export const useSettings = (initial: Settings) => {
  const [settings, setSettings] = useState<Settings>(initial);

  const loadSettings = useCallback(async () => {
    if (!hasBackend()) return;
    let attempts = 0;
    const load = async () => {
      if (!window.pywebview?.api?.get_settings) {
        attempts++;
        if (attempts < 100) setTimeout(load, 200);
        return;
      }
      try {
        const s = await window.pywebview!.api.get_settings!();
        if (s && Object.keys(s).length) {
          setSettings(prev => ({ ...prev, ...s }));
        }
      } catch {}
    };
    load();
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const updateSettings = useCallback((patch: Partial<Settings>) => {
    setSettings(prev => ({ ...prev, ...patch }));
    if (hasBackend()) {
      window.pywebview!.api.save_settings?.(patch)?.catch(() => {});
    }
  }, []);

  return { settings, setSettings: updateSettings, reload: loadSettings };
};

export const useDebug = () => {
  const [debug, setDebug] = useState<DebugConfig>({
    debugMode: false,
    debugCharacterMode: false,
    debugStaticImage: false,
    debugStaticImagePath: "",
  });

  const loadDebug = useCallback(async () => {
    if (!hasBackend()) return;
    let attempts = 0;
    const load = async () => {
      if (!window.pywebview?.api?.get_debug) {
        attempts++;
        if (attempts < 100) setTimeout(load, 200);
        return;
      }
      try {
        const d = await window.pywebview!.api.get_debug!();
        if (d && typeof d.debugMode === "boolean") {
          setDebug({
            debugMode: d.debugMode,
            debugCharacterMode: d.debugCharacterMode,
            debugStaticImage: d.debugStaticImage,
            debugStaticImagePath: d.debugStaticImagePath || "",
          });
        }
      } catch {}
    };
    load();
  }, []);

  useEffect(() => {
    loadDebug();
  }, [loadDebug]);

  const updateDebug = useCallback((
    debugMode: boolean,
    debugCharacterMode: boolean,
    debugStaticImage: boolean,
    debugStaticImagePath?: string
  ) => {
    setDebug(prev => {
      const next = { ...prev, debugMode, debugCharacterMode, debugStaticImage };
      if (typeof debugStaticImagePath === "string") next.debugStaticImagePath = debugStaticImagePath;
      return next;
    });
    if (hasBackend()) {
      window.pywebview!.api.set_debug?.(debugMode, debugCharacterMode, debugStaticImage, typeof debugStaticImagePath === "string" ? debugStaticImagePath : debug.debugStaticImagePath)?.catch(() => {});
    }
  }, []);

  return { debug, setDebug: updateDebug };
};

export const useBackendState = (demoConnected: boolean, onConnectedChange?: (running: boolean) => void) => {
  const [state, setState] = useState<BackendState | null>(null);
  const connectedRef = useRef(false);
  // Keep the latest callback in a ref so an inline lambda from the parent
  // doesn't recreate the polling effect every render.
  const onConnectedChangeRef = useRef(onConnectedChange);
  onConnectedChangeRef.current = onConnectedChange;
  const lastJsonRef = useRef("");

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      const s = await fetchState(demoConnected);
      if (!alive) return;
      connectedRef.current = s.running;
      onConnectedChangeRef.current?.(s.running);
      // Skip re-render when nothing actually changed (fetchState builds a
      // fresh object every poll).
      const json = JSON.stringify(s);
      if (json !== lastJsonRef.current) {
        lastJsonRef.current = json;
        setState(s);
      }
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => { alive = false; clearInterval(t); };
  }, [demoConnected]);

  return { state, connected: connectedRef.current };
};

export const useLogs = (debugEnabled: boolean) => {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    if (!debugEnabled || !hasBackend()) {
      setLogs([]);
      return;
    }
    let alive = true;
    const tick = async () => {
      if (!window.pywebview?.api?.get_logs) return;
      try {
        const lines = await window.pywebview!.api.get_logs!();
        if (alive && Array.isArray(lines)) setLogs(lines);
      } catch {}
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => { alive = false; clearInterval(t); };
  }, [debugEnabled]);

  return logs;
};