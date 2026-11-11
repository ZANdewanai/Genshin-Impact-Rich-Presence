import { useEffect, useState } from "react";
import type { Tab } from "./types";
import { api, hasBackend } from "./api";
import { useBackendState, useDebug, useLogs, useSettings } from "./hooks";
import { TabBar, PresenceTab, SettingsTab, LogsTab, AboutTab } from "./components";

export default function App() {
  const [tab, setTab] = useState<Tab>("presence");
  // Demo mode (plain browser, no pywebview): pretend the engine is running
  // so the UI is explorable. The real state always comes from the backend.
  const [demoRunning, setDemoRunning] = useState(true);

  const { settings, updateSettings } = useSettings();
  const { debug, setDebugFlags } = useDebug();
  const state = useBackendState(demoRunning);
  const logs = useLogs(debug.debugMode);

  // Re-render every second so the session timer stays fresh even when the
  // backend payload itself hasn't changed.
  const [, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 1000);
    return () => clearInterval(t);
  }, []);

  // Until the first poll resolves, assume the last known intent (demoRunning)
  // so the UI doesn't flash "stopped" on launch.
  const running = state?.running ?? demoRunning;

  const toggleEngine = () => {
    if (hasBackend()) {
      // State refreshes on the next 1s poll.
      api()?.toggle_connection()?.catch(() => {});
    } else {
      setDemoRunning(r => !r);
    }
  };

  const un = settings.username.trim().toLowerCase();
  const needsSetup = un === "" || un === "playername" || un === "player";

  return (
    <div className="h-full flex flex-col bg-[var(--color-ink)]">
      {/* Header */}
      <header className="flex items-center justify-between gap-3 px-4 sm:px-6 h-14 shrink-0 border-b border-[var(--color-line)] bg-[var(--color-panel)]/60">
        <div className="flex items-center gap-2.5 min-w-0">
          <svg width="18" height="18" viewBox="0 0 24 24" className="shrink-0">
            <polygon points="12,1 16,8 23,12 16,16 12,23 8,16 1,12 8,8" fill="#d4af6a" />
          </svg>
          <span className="font-display text-[15px] tracking-wide text-[var(--color-gold-bright)] truncate">
            Genshin Presence
          </span>
        </div>

        <button
          onClick={toggleEngine}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg border cursor-pointer transition-colors"
          style={{
            borderColor: running ? "rgba(95,214,104,0.35)" : "var(--color-line)",
            background: running ? "rgba(95,214,104,0.08)" : "rgba(255,255,255,0.04)",
          }}
        >
          <span className={`status-dot ${running ? "on" : ""}`} />
          <span className="font-heading text-[10.5px] font-semibold tracking-[0.12em] text-[var(--color-muted)]">
            {running ? "ENGINE RUNNING" : "ENGINE STOPPED"}
          </span>
        </button>
      </header>

      {/* Nav */}
      <nav className="flex items-center gap-1 px-4 sm:px-6 pt-3 shrink-0 overflow-x-auto">
        <TabBar active={tab} onChange={setTab} needsSetup={needsSetup} />
      </nav>

      {/* Content */}
      <main className="flex-1 min-h-0 overflow-y-auto">
        <div key={tab} className="max-w-5xl mx-auto px-4 sm:px-6 py-5 fade-up">
          {tab === "presence" && (
            <PresenceTab
              state={state}
              running={running}
              onToggle={toggleEngine}
            />
          )}
          {tab === "settings" && (
            <SettingsTab
              settings={settings}
              onSave={updateSettings}
              debug={debug}
              onDebugChange={setDebugFlags}
            />
          )}
          {tab === "logs" && <LogsTab logs={logs} debug={debug} onDebugChange={setDebugFlags} />}
          {tab === "about" && <AboutTab />}
        </div>
      </main>
    </div>
  );
}
