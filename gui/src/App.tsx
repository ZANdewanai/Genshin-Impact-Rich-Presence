import { useState, useEffect, useRef } from "react";
import type { Character, Element, Settings, DebugConfig, BackendState, Tab } from "./types";
import { EL_COLOR, rarityColor, LOCATIONS, ACTIVITIES, STATIC_PARTICLES, DEMO_STARTED_AT } from "./constants";
import { hasBackend, fmtElapsed, fetchState } from "./utils";
import { useSettings, useDebug, useBackendState, useLogs } from "./hooks";
import {
  ParticleField,
  TabBar,
  CharacterSlot,
  PresenceTab,
  SettingsTab,
  LogsTab,
  AboutTab,
} from "./components";

/* == Backend bridge (pywebview) ================================== */

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

const hasBackendGlobal = () => typeof window !== "undefined" && !!window.pywebview;

/* ── Main ──────────────────────────────────────── */
export default function App() {
  const [tab, setTab] = useState<Tab>("presence");
  const [connected, setConnected] = useState(false);

  const { settings, setSettings: updateSettings } = useSettings({
    username: "",
    mcAether: true,
    wandererName: "Wanderer",
    manekinName: "Manekin",
    manekinaName: "Manekina",
  });

  const { debug, setDebug: updateDebug } = useDebug();

  const onDebugChange = (patch: Partial<DebugConfig>) => {
    const next = { ...debug, ...patch };
    updateDebug(next.debugMode, next.debugCharacterMode, next.debugStaticImage, next.debugStaticImagePath);
  };

  const { state, connected: backendConnected } = useBackendState(connected, (running) => {
    setConnected(running);
  });

  const logs = useLogs(debug.debugMode);

  const location = state?.location ?? "Waiting for game data...";
  const activity = state?.activity ?? "-";
  const elapsed = state?.timestamp ? fmtElapsed(state.timestamp) : "-";
  const party = state?.party ?? [];
  const activeCharacterIndex = (state?.active_character_index ?? -1) >= 0 ? state?.active_character_index ?? null : null;
  // Discord RPC exact params
  const discordDetails = state?.discord_details ?? "";
  const discordState = state?.discord_state ?? "";
  const discordLargeImage = state?.discord_large_image ?? "";
  const discordLargeText = state?.discord_large_text ?? "";
  const discordSmallImage = state?.discord_small_image ?? "";
  const discordSmallText = state?.discord_small_text ?? "";

  const activeChar = party[activeCharacterIndex ?? 0] ?? null;
  const activeEl: Element = activeChar?.element ?? "empty";

  const un = settings.username.trim().toLowerCase();
  const needsSetup = un === "" || un === "playername" || un === "player";

  const toggleConnection = () => {
    if (hasBackendGlobal()) {
      window.pywebview!.api.toggle_connection()
        .then(r => { setConnected(r.running); })
        .catch(() => {});
    } else {
      setConnected(c => !c);
    }
  };

  return (
    <div className="size-full flex items-center justify-center p-3"
      style={{ background: "radial-gradient(ellipse 80% 60% at 40% 30%,#0c1030 0%,#08091a 65%,#060810 100%)" }}
    >
      <div className="w-full relative panel-halo flex flex-col"
        style={{
          aspectRatio: "16 / 9",
          maxWidth: "calc(100vh * 16 / 9)",
          maxHeight: "100%",
          background: "linear-gradient(145deg,#0c1028 0%,#090d1e 50%,#080a18 100%)",
          border: "1px solid rgba(200,168,75,0.22)",
          borderRadius: 8,
          overflow: "hidden",
          transition: "box-shadow 0.6s ease",
        }}
      >
        <div className="absolute inset-0 pointer-events-none animate-breathe"
          style={{
            background: `radial-gradient(ellipse 70% 50% at 50% 50%,${EL_COLOR[activeEl]}16,transparent 70%)`,
            borderRadius: 6, transition: "background 1s ease",
          }}
        />

        <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ borderRadius: 6 }}>
          {STATIC_PARTICLES.map(p => (
            <div key={p.id} className="particle" style={{
              left: p.left, top: p.top, width: p.size, height: p.size, borderRadius: "50%", position: "absolute",
              backgroundColor: p.gold ? `rgba(200,168,75,0.4)` : `rgba(140,160,220,0.25)`,
              ["--dur" as string]: p.dur, ["--delay" as string]: p.delay,
              boxShadow: p.gold ? `0 0 ${p.size * 3}px rgba(200,168,75,0.6)` : `0 0 ${p.size * 2}px rgba(140,160,220,0.4)`,
            }} />
          ))}
        </div>

        <span className="corner tl corner-lg" style={{ opacity: 0.7 }} />
        <span className="corner tr corner-lg" style={{ opacity: 0.7 }} />
        <span className="corner bl corner-lg" style={{ opacity: 0.7 }} />
        <span className="corner br corner-lg" style={{ opacity: 0.7 }} />

        <div className="relative px-5 pt-4 pb-3.5 flex items-center justify-between"
          style={{ borderBottom: "1px solid rgba(200,168,75,0.14)" }}
        >
          <div className="absolute bottom-0 left-0 right-0 h-px animate-shimmer" style={{ opacity: 0.4 }} />

          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center logo-glow"
              style={{
                width: 40, height: 40, borderRadius: "50%",
                background: "radial-gradient(circle,rgba(200,168,75,0.14) 0%,transparent 70%)",
                border: "1px solid rgba(200,168,75,0.38)",
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24">
                <polygon points="12,1 16,8 23,12 16,16 12,23 8,16 1,12 8,8" fill="#c8a84b" opacity="0.95"/>
              </svg>
              <div className="absolute inset-0 rounded-full" style={{ border: "1px solid rgba(200,168,75,0.18)", transform: "scale(1.28)" }} />
            </div>
            <div>
              <div style={{
                fontFamily: "var(--font-display)", fontSize: "13.5px", letterSpacing: "0.07em",
                background: "linear-gradient(90deg,#c8a84b,#f0d47a 50%,#c8a84b)",
                backgroundSize: "200%", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                animation: "shimmer 4s linear infinite",
              }}>
                Genshin Impact
              </div>
              <div style={{ fontFamily: "var(--font-heading)", fontSize: "9.5px", color: "#6a5820", letterSpacing: "0.22em", marginTop: 2 }}>
                RICH PRESENCE
              </div>
            </div>
          </div>

          <button onClick={toggleConnection}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full cursor-pointer transition-all duration-300"
            style={{
              border: connected ? "1px solid rgba(200,168,75,0.35)" : "1px solid rgba(80,80,100,0.35)",
              background: connected ? "rgba(200,168,75,0.07)" : "rgba(60,60,80,0.15)",
              outline: "none",
            }}
          >
            <span className="status-dot inline-block rounded-full" style={{
              width: 6, height: 6,
              backgroundColor: connected ? "#64d250" : "#555568",
              boxShadow: connected ? "0 0 6px #64d250" : "none",
            }} />
            <span style={{
              fontFamily: "var(--font-heading)", fontSize: "10px",
              color: connected ? "#c8a84b" : "#555568", letterSpacing: "0.14em",
            }}>
              {connected ? "CONNECTED" : "OFFLINE"}
            </span>
          </button>
        </div>

        <div className="relative">
          <TabBar active={tab} onChange={setTab} needsSetup={needsSetup} />
        </div>

        <div className="relative px-4 pb-4 pt-3 flex flex-1 min-h-0 flex-col gap-4 overflow-y-auto">
          {tab === "presence" && (
            <PresenceTab
              party={party}
              activeCharacterIndex={activeCharacterIndex}
              location={location}
              activity={activity}
              elapsed={elapsed}
              connected={connected}
              onToggle={toggleConnection}
              discordDetails={discordDetails}
              discordState={discordState}
              discordLargeImage={discordLargeImage}
              discordLargeText={discordLargeText}
              discordSmallImage={discordSmallImage}
              discordSmallText={discordSmallText}
            />
          )}

          {tab === "settings" && (
            <SettingsTab
              settings={settings}
              onSave={updateSettings}
              debug={debug}
              onDebugChange={onDebugChange}
            />
          )}

          {tab === "logs" && (
            <LogsTab
              logs={logs}
              debug={debug}
            />
          )}

          {tab === "about" && <AboutTab />}
        </div>
      </div>
    </div>
  );
}