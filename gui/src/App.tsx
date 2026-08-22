import { useState, useEffect, useRef } from "react";

type Element = "pyro" | "hydro" | "anemo" | "electro" | "cryo" | "geo" | "dendro" | "empty";
type Tab = "presence" | "settings" | "logs" | "about";

interface Character {
  id?: number; name: string; element: Element;
  level?: number; imageUrl: string; rarity?: number;
}

interface Settings {
  username: string;
  mcAether: boolean;
  wandererName: string;
  manekinName: string;
  manekinaName: string;
}

const EL_COLOR: Record<Element, string> = {
  pyro: "#ff6432", hydro: "#3298ff", anemo: "#5adcb4",
  electro: "#b464ff", cryo: "#8cc8ff", geo: "#c8a032",
  dendro: "#64d250", empty: "#4a4a5a",
};
const EL_LABEL: Record<Element, string> = {
  pyro: "Pyro", hydro: "Hydro", anemo: "Anemo", electro: "Electro",
  cryo: "Cryo", geo: "Geo", dendro: "Dendro", empty: "—",
};

const LOCATIONS = [
  "Mondstadt — City of Freedom", "Liyue Harbor — Port of Commerce",
  "Inazuma — Electro Archon's Domain", "Sumeru — City of Wisdom",
  "Fontaine — Nation of Justice", "Natlan — Nation of War",
  "Domain of Forsaken Ruins", "Golden Apple Archipelago",
];
const ACTIVITIES = [
  "Exploring the open world", "Clearing Spiral Abyss",
  "Completing a Story Quest", "Grinding Resin in Domain",
  "Fighting World Boss", "In Co-Op Session",
  "Forging and Crafting", "Idle in Serenitea Pot",
];

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
      };
    };
  }
}

interface BackendState {
  running: boolean;
  location: string;
  activity: string;
  timestamp: number | null;
  party: (Character | null)[];
  active_character_index: number;
}

const hasBackend = () => typeof window !== "undefined" && !!window.pywebview;

function fmtElapsed(ts: number | null): string {
  if (!ts) return "-";
  const secs = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

/* Demo simulator so pnpm dev in a plain browser still renders. */
const DEMO_STARTED_AT = Date.now() / 1000 - 83 * 60;

function fetchState(demoConnected: boolean): Promise<BackendState> {
  if (hasBackend()) return window.pywebview!.api.get_state();
  return Promise.resolve({
    running: demoConnected,
    location: LOCATIONS[0],
    activity: ACTIVITIES[0],
    timestamp: DEMO_STARTED_AT,
    party: [null, null, null, null],
    active_character_index: 0,
  });
}

/* ── Particles ─────────────────────────────────── */
const STATIC_PARTICLES = Array.from({ length: 18 }, (_, i) => ({
  id: i, left: `${8 + (i * 5.1) % 84}%`, top: `${10 + (i * 4.7) % 80}%`,
  size: 1.5 + (i % 3) * 0.7,
  dur: `${5 + (i % 7)}s`, delay: `${-(i * 0.9)}s`,
  gold: i % 2 === 0,
}));

function ParticleField() {
  return (
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
  );
}

/* ── Ornament divider ──────────────────────────── */
function OrnamentDivider({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <div className="flex-1 h-px gold-line" />
      <svg width="10" height="10" viewBox="0 0 12 12" fill="#c8a84b" opacity={0.7}>
        <path d="M6 0l1.5 4.5L12 6l-4.5 1.5L6 12 4.5 7.5 0 6l4.5-1.5z"/>
      </svg>
      {label && (
        <span style={{ fontFamily: "var(--font-heading)", fontSize: "9px", color: "#c8a84b", letterSpacing: "0.18em", opacity: 0.85 }}>
          {label}
        </span>
      )}
      <svg width="10" height="10" viewBox="0 0 12 12" fill="#c8a84b" opacity={0.7}>
        <path d="M6 0l1.5 4.5L12 6l-4.5 1.5L6 12 4.5 7.5 0 6l4.5-1.5z"/>
      </svg>
      <div className="flex-1 h-px gold-line" />
    </div>
  );
}

function Stars({ n, color }: { n: number; color: string }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: n }).map((_, i) => (
        <svg key={i} width="9" height="9" viewBox="0 0 10 10" fill={color}>
          <polygon points="5,0.5 6.6,3.4 9.5,5 6.6,6.6 5,9.5 3.4,6.6 0.5,5 3.4,3.4"/>
        </svg>
      ))}
    </div>
  );
}

function ElBadge({ el }: { el: Element }) {
  if (el === "empty") return null;
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-px rounded-sm" style={{
      background: `${EL_COLOR[el]}18`, border: `1px solid ${EL_COLOR[el]}50`,
      color: EL_COLOR[el], fontFamily: "var(--font-heading)", fontSize: "8.5px", letterSpacing: "0.09em",
    }}>
      {EL_LABEL[el]}
    </span>
  );
}

/* ── Character slot ────────────────────────────── */
function CharacterSlot({ character, index, isActive, onClick }: {
  character: Character | null; index: number; isActive: boolean; onClick: () => void;
}) {
  const el = character?.element ?? "empty";
  const clr = EL_COLOR[el];
  const animClass = ["slide-up-1","slide-up-2","slide-up-3","slide-up-4"][index];
  return (
    <button onClick={onClick}
      className={`relative flex flex-col overflow-hidden cursor-pointer group ${animClass} slot-glow glow-${el} ${isActive ? "active" : ""}`}
      style={{
        background: character ? "linear-gradient(170deg,#0d1122 0%,#0a0d1a 100%)" : "rgba(10,13,26,0.5)",
        border: `1px solid ${isActive ? clr + "70" : "rgba(200,168,75,0.18)"}`,
        borderRadius: 4, aspectRatio: "3/4", outline: "none",
        transition: "border-color 0.35s ease",
      }}
    >
      <span className="corner tl" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      <span className="corner tr" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      <span className="corner bl" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      <span className="corner br" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      {character ? (
        <>
          <div className="relative flex-1 overflow-hidden">
            <img src={character.imageUrl} alt={character.name}
              className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform"
              style={{ filter: "saturate(0.8) contrast(1.08) brightness(0.95)", transitionDuration: "600ms" }}
            />
            <div className="absolute inset-0" style={{ background: "linear-gradient(180deg,transparent 38%,rgba(8,9,26,0.96) 100%)" }} />
            <div className="absolute top-0 left-0 right-0 h-0.5" style={{ backgroundColor: clr, boxShadow: `0 0 6px ${clr}` }} />
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
              style={{ background: `linear-gradient(120deg,transparent 30%,${clr}10 50%,transparent 70%)` }} />
            <div className="absolute top-2 left-2">
              <Stars n={character.rarity ?? 5} color={character.rarity === 5 ? "#e8c96a" : "#b090e0"} />
            </div>
          </div>
          <div className="px-2.5 pt-1.5 pb-2.5 flex flex-col gap-1.5">
            <span style={{ fontFamily: "var(--font-heading)", fontSize: "12.5px",
              color: isActive ? "#f0d47a" : "#ede3c4", fontWeight: 500, letterSpacing: "0.04em",
              whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", transition: "color 0.3s" }}>
              {character.name}
            </span>
            <div className="flex items-center justify-between">
              <ElBadge el={character.element} />
              <span style={{ fontFamily: "var(--font-heading)", fontSize: "9px", color: "#6a5820", letterSpacing: "0.06em" }}>
                {character.level != null ? `Lv.${character.level}` : ""}
              </span>
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-2">
          <div style={{ width: 32, height: 32, borderRadius: "50%", border: "1px solid rgba(200,168,75,0.2)",
            display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(200,168,75,0.35)" strokeWidth="1.2">
              <circle cx="12" cy="8" r="4"/><path d="M4 22c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
            </svg>
          </div>
          <span style={{ fontFamily: "var(--font-heading)", fontSize: "8px", color: "rgba(200,168,75,0.3)", letterSpacing: "0.14em" }}>
            EMPTY
          </span>
        </div>
      )}
    </button>
  );
}

function InfoRow({ icon, label, value, onClick }: {
  icon: React.ReactNode; label: string; value: string; onClick?: () => void;
}) {
  return (
    <div onClick={onClick}
      className={`flex items-start gap-3 px-4 py-3 group ${onClick ? "cursor-pointer hover:bg-white/[0.02]" : ""} transition-colors`}
      style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
      <div className="mt-0.5 flex-shrink-0" style={{ color: "#c8a84b", opacity: 0.65 }}>{icon}</div>
      <div className="flex flex-col gap-0.5 min-w-0 flex-1">
        <span style={{ fontFamily: "var(--font-heading)", fontSize: "8.5px", color: "#6a5820", letterSpacing: "0.16em" }}>
          {label}
        </span>
        <span style={{ fontFamily: "var(--font-body)", fontSize: "15px", color: "#ede3c4", lineHeight: 1.3 }}>
          {value}
        </span>
      </div>
      {onClick && (
        <svg className="mt-1 flex-shrink-0 opacity-0 group-hover:opacity-40 transition-opacity"
          width="10" height="10" viewBox="0 0 14 14" fill="none" stroke="#c8a84b" strokeWidth="1.5">
          <path d="M9 1l4 6-4 6M1 7h12"/>
        </svg>
      )}
    </div>
  );
}

function SelectField({ value, options, onChange, onBlur, label }: {
  value: string; options: string[]; onChange: (v: string) => void; onBlur: () => void; label: string;
}) {
  return (
    <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
      <div style={{ fontFamily: "var(--font-heading)", fontSize: "8.5px", color: "#6a5820", letterSpacing: "0.16em", marginBottom: 4 }}>
        {label}
      </div>
      <select autoFocus value={value}
        onChange={e => { onChange(e.target.value); onBlur(); }} onBlur={onBlur}
        className="w-full bg-transparent outline-none cursor-pointer"
        style={{ fontFamily: "var(--font-body)", fontSize: "15px", color: "#ede3c4", border: "none" }}
      >
        {options.map(o => (
          <option key={o} value={o} style={{ background: "#0e1228", color: "#ede3c4" }}>{o}</option>
        ))}
      </select>
    </div>
  );
}

/* ── Settings row ──────────────────────────────── */
function SettingRow({ label, description, children }: {
  label: string; description?: string; children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 px-4"
      style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span style={{ fontFamily: "var(--font-heading)", fontSize: "11px", color: "#ede3c4", letterSpacing: "0.05em" }}>
          {label}
        </span>
        {description && (
          <span style={{ fontFamily: "var(--font-body)", fontSize: "12.5px", color: "#6a5820", lineHeight: 1.3 }}>
            {description}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

/* ── Settings panel ────────────────────────────── */
function ApplyButton({ dirty, saved, onApply }: {
  dirty: boolean; saved: boolean; onApply: () => void;
}) {
  if (!dirty) return null;
  return (
    <button onClick={onApply} className="px-2.5 py-1 rounded cursor-pointer transition-all duration-200 flex-shrink-0"
      style={{
        fontFamily: "var(--font-heading)", fontSize: "8px", letterSpacing: "0.1em",
        background: saved ? "rgba(100,210,80,0.15)" : "rgba(200,168,75,0.1)",
        border: saved ? "1px solid rgba(100,210,80,0.4)" : "1px solid rgba(200,168,75,0.35)",
        color: saved ? "#64d250" : "#c8a84b", outline: "none",
      }}>
      {saved ? "SAVED" : "APPLY"}
    </button>
  );
}

function TextField({ label, hint, value, dirty, saved, onChange, onApply }: {
  label: string; hint?: string; value: string;
  dirty: boolean; saved: boolean;
  onChange: (v: string) => void; onApply: () => void;
}) {
  return (
    <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
      <div style={{ fontFamily: "var(--font-heading)", fontSize: "8.5px", color: "#6a5820", letterSpacing: "0.16em", marginBottom: 6 }}>
        {label}
      </div>
      <div className="flex items-center gap-2">
        <input
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && dirty) onApply(); }}
          className="flex-1 bg-transparent outline-none min-w-0"
          style={{
            fontFamily: "var(--font-heading)", fontSize: "12px", color: "#ede3c4",
            border: `1px solid ${dirty ? "rgba(200,168,75,0.5)" : "rgba(200,168,75,0.2)"}`,
            borderRadius: 3,
            padding: "6px 10px", letterSpacing: "0.06em",
            background: "rgba(200,168,75,0.04)",
          }}
        />
        <ApplyButton dirty={dirty} saved={saved} onApply={onApply} />
      </div>
      {hint && (
        <p style={{ fontFamily: "var(--font-body)", fontSize: "12px", color: "#6a5820", marginTop: 6, lineHeight: 1.4 }}>
          {hint}
        </p>
      )}
    </div>
  );
}

function SettingsPanel({ settings, onSave }: {
  settings: Settings; onSave: (s: Partial<Settings>) => void;
}) {
  const [form, setForm] = useState<Settings>(settings);
  const [savedKey, setSavedKey] = useState<string | null>(null);

  /* Re-sync the form when the backend loads persisted values */
  useEffect(() => { setForm(settings); }, [settings]);

  const set = (patch: Partial<Settings>) => setForm(prev => ({ ...prev, ...patch }));

  const apply = (key: keyof Settings) => {
    onSave({ [key]: form[key] } as Partial<Settings>);
    setSavedKey(key);
    setTimeout(() => setSavedKey(prev => (prev === key ? null : prev)), 2000);
  };

  const isDirty = (key: keyof Settings) => form[key] !== settings[key];
  const isSaved = (key: keyof Settings) => savedKey === key && !isDirty(key);

  const inputStyle = {
    flex: 1,
    background: "transparent", outline: "none", minWidth: 0,
    fontFamily: "var(--font-heading)", fontSize: "12px", color: "#ede3c4",
    border: "1px solid rgba(200,168,75,0.2)", borderRadius: 3,
    padding: "6px 10px", letterSpacing: "0.06em",
  } as React.CSSProperties;

  return (
    <div className="flex flex-col gap-5">
      {/* Identity */}
      <div>
        <OrnamentDivider label="IDENTITY" />
        <div className="mt-3 rounded overflow-hidden" style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}>
          <TextField label="TRAVELER NAME" value={form.username}
            dirty={isDirty("username")} saved={isSaved("username")}
            onChange={v => set({ username: v })} onApply={() => apply("username")}
            hint="✓ Applied live. Your player name, shown in party-related presence text." />

          <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
            <div style={{ fontFamily: "var(--font-heading)", fontSize: "8.5px", color: "#6a5820", letterSpacing: "0.16em", marginBottom: 6 }}>
              MAIN CHARACTER
            </div>
            <div className="flex items-center gap-2">
              <select
                value={form.mcAether ? "aether" : "lumine"}
                onChange={e => set({ mcAether: e.target.value === "aether" })}
                className="cursor-pointer bg-transparent outline-none flex-1 min-w-0"
                style={{
                  fontFamily: "var(--font-heading)", fontSize: "12px", color: "#ede3c4",
                  border: `1px solid ${form.mcAether !== settings.mcAether ? "rgba(200,168,75,0.5)" : "rgba(200,168,75,0.2)"}`,
                  borderRadius: 3,
                  padding: "6px 10px", letterSpacing: "0.06em",
                  background: "rgba(200,168,75,0.04)",
                }}
              >
                <option value="aether" style={{ background: "#0b0f22" }}>Aether</option>
                <option value="lumine" style={{ background: "#0b0f22" }}>Lumine</option>
              </select>
              <ApplyButton
                dirty={form.mcAether !== settings.mcAether}
                saved={isSaved("mcAether")}
                onApply={() => apply("mcAether")}
              />
            </div>
            <p style={{ fontFamily: "var(--font-body)", fontSize: "12px", color: "#6a5820", marginTop: 6, lineHeight: 1.4 }}>
              ✓ Applied live. Which twin you play as — used to detect your character in the party screen.
            </p>
          </div>

          <TextField label="WANDERER NAME" value={form.wandererName}
            dirty={isDirty("wandererName")} saved={isSaved("wandererName")}
            onChange={v => set({ wandererName: v })} onApply={() => apply("wandererName")}
            hint="✓ Applied live. Custom name shown when Wanderer is detected — only needed if you changed it in-game." />
          <TextField label="MANEKIN NAME" value={form.manekinName}
            dirty={isDirty("manekinName")} saved={isSaved("manekinName")}
            onChange={v => set({ manekinName: v })} onApply={() => apply("manekinName")}
            hint="✓ Applied live. Custom name shown when Wonderland Manekin (male) is detected." />
          <TextField label="MANEKINA NAME" value={form.manekinaName}
            dirty={isDirty("manekinaName")} saved={isSaved("manekinaName")}
            onChange={v => set({ manekinaName: v })} onApply={() => apply("manekinaName")}
            hint="✓ Applied live. Custom name shown when Wonderland Manekina (female) is detected." />

          
        </div>
      </div>

    </div>
  );
}

/* ── Logs panel ───────────────────────────────── */
function LogsPanel({ logs }: { logs: string[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "auto" });
  }, [logs.length]);

  return (
    <div>
      <OrnamentDivider label="ENGINE LOG" />
      <div className="mt-3 rounded overflow-hidden"
        style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}>
        <div style={{
          maxHeight: 480, overflowY: "auto", padding: "12px 14px",
          fontFamily: "var(--font-body)", fontSize: "12px", lineHeight: 1.6,
          color: "#9aa0b8",
        }}>
          {logs.length === 0 ? (
            <span style={{ color: "#6a5820", fontStyle: "italic" }}>
              No engine output yet. Press CONNECT to start the detection + RPC engine.
            </span>
          ) : (
            logs.map((line, i) => (
              <div key={i} style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                {line}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}

/* ── About panel ───────────────────────────────── */
function AboutPanel() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-5">
      {/* Hero */}
      <div className="relative flex flex-col items-center py-6 rounded overflow-hidden"
        style={{
          background: "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(200,168,75,0.08) 0%, rgba(8,9,26,0.8) 100%)",
          border: "1px solid rgba(200,168,75,0.18)",
        }}
      >
        <span className="corner tl" /><span className="corner tr" />
        <span className="corner bl" /><span className="corner br" />

        <div className="logo-glow flex items-center justify-center mb-4"
          style={{
            width: 56, height: 56, borderRadius: "50%",
            background: "radial-gradient(circle,rgba(200,168,75,0.18) 0%,transparent 70%)",
            border: "1px solid rgba(200,168,75,0.4)",
          }}
        >
          <svg width="28" height="28" viewBox="0 0 24 24">
            <polygon points="12,2 15,9 22,9 16.5,14 18.5,21 12,17 5.5,21 7.5,14 2,9 9,9" fill="#c8a84b"/>
          </svg>
        </div>

        <div style={{
          fontFamily: "var(--font-display)", fontSize: "15px", letterSpacing: "0.08em",
          background: "linear-gradient(90deg,#c8a84b,#f0d47a 50%,#c8a84b)",
          backgroundSize: "200%", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          animation: "shimmer 4s linear infinite",
        }}>
          Genshin Presence
        </div>

        <div style={{ fontFamily: "var(--font-heading)", fontSize: "9px", color: "#6a5820", letterSpacing: "0.2em", marginTop: 4 }}>
          VERSION 1.0.0
        </div>

        <div style={{ fontFamily: "var(--font-body)", fontStyle: "italic", fontSize: "13px", color: "#8a7a5a", marginTop: 8, textAlign: "center", maxWidth: 260, lineHeight: 1.5 }}>
          Show Teyvat to the world — your party, your world, your adventure.
        </div>
      </div>

      {/* Info cards */}
      <div>
        <OrnamentDivider label="DETAILS" />
        <div className="mt-3 rounded overflow-hidden" style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}>
          {[
            { label: "VERSION", value: "1.0.0 (stable)" },
            { label: "BUILT WITH", value: "Electron · React · Discord RPC" },
            { label: "GAME SUPPORT", value: "Genshin Impact 5.x" },
            { label: "PLATFORM", value: "Windows · macOS · Linux" },
            { label: "LICENSE", value: "MIT — open source" },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between px-4 py-2.5"
              style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
              <span style={{ fontFamily: "var(--font-heading)", fontSize: "8.5px", color: "#6a5820", letterSpacing: "0.14em" }}>
                {label}
              </span>
              <span style={{ fontFamily: "var(--font-body)", fontSize: "13.5px", color: "#ede3c4" }}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Links */}
      <div>
        <OrnamentDivider label="LINKS" />
        <div className="mt-3 grid grid-cols-2 gap-2">
          {[
            { label: "GitHub Repo", icon: "⧉", sub: "Source code & releases" },
            { label: "Discord Server", icon: "◈", sub: "Community & support" },
            { label: "Report Issue", icon: "⚑", sub: "Bugs & feedback" },
            { label: "Changelog", icon: "≡", sub: "What's new" },
          ].map(({ label, icon, sub }) => (
            <button key={label} className="flex flex-col gap-1 px-3 py-3 rounded text-left cursor-pointer group transition-all duration-200"
              style={{
                background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)",
                outline: "none",
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = "rgba(200,168,75,0.38)")}
              onMouseLeave={e => (e.currentTarget.style.borderColor = "rgba(200,168,75,0.14)")}
            >
              <div className="flex items-center gap-2">
                <span style={{ color: "#c8a84b", fontSize: "13px", opacity: 0.8 }}>{icon}</span>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: "10px", color: "#ede3c4", letterSpacing: "0.05em" }}>
                  {label}
                </span>
              </div>
              <span style={{ fontFamily: "var(--font-body)", fontSize: "12px", color: "#6a5820", paddingLeft: 20 }}>
                {sub}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Credits */}
      <div>
        <OrnamentDivider label="ACKNOWLEDGEMENTS" />
        <div className="mt-3 px-4 py-3 rounded" style={{
          background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)",
        }}>
          <p style={{ fontFamily: "var(--font-body)", fontSize: "13.5px", color: "#8a7a5a", lineHeight: 1.7 }}>
            Genshin Impact and all related assets are property of{" "}
            <span style={{ color: "#ede3c4" }}>HoYoverse</span>. This tool is a{" "}
            <span style={{ color: "#ede3c4" }}>fan-made, unofficial</span> project and is not affiliated with or endorsed by HoYoverse in any way.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <div className="h-px flex-1" style={{ background: "rgba(200,168,75,0.1)" }} />
            <button onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1 rounded cursor-pointer transition-all duration-200"
              style={{
                fontFamily: "var(--font-heading)", fontSize: "8px", letterSpacing: "0.12em",
                color: copied ? "#64d250" : "#6a5820",
                border: copied ? "1px solid rgba(100,210,80,0.3)" : "1px solid rgba(200,168,75,0.15)",
                background: "transparent", outline: "none",
              }}>
              {copied ? "COPIED ✓" : "COPY DISCLAIMER"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Tab bar ───────────────────────────────────── */
function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    {
      id: "presence", label: "Presence",
      icon: (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
      ),
    },
    {
      id: "settings", label: "Settings",
      icon: (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
      ),
    },
    {
      id: "logs", label: "Logs",
      icon: (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M4 6h16M4 12h16M4 18h10"/>
        </svg>
      ),
    },
    {
      id: "about", label: "About",
      icon: (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="8" strokeWidth="2" strokeLinecap="round"/>
          <line x1="12" y1="12" x2="12" y2="16"/>
        </svg>
      ),
    },
  ];

  return (
    <div className="flex" style={{ borderBottom: "1px solid rgba(200,168,75,0.14)" }}>
      {tabs.map(tab => {
        const isActive = active === tab.id;
        return (
          <button key={tab.id} onClick={() => onChange(tab.id)}
            className="relative flex items-center gap-1.5 px-4 py-3 cursor-pointer transition-all duration-200 flex-1 justify-center"
            style={{
              outline: "none", background: "transparent", border: "none",
              color: isActive ? "#c8a84b" : "#6a5820",
            }}
            onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = "#a08840"; }}
            onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = "#6a5820"; }}
          >
            {isActive && (
              <>
                {/* Active tab background */}
                <div className="absolute inset-0" style={{ background: "rgba(200,168,75,0.04)" }} />
                {/* Active indicator line */}
                <div className="absolute bottom-0 left-0 right-0 h-0.5 animate-shimmer"
                  style={{ background: "linear-gradient(90deg,transparent,#c8a84b,transparent)" }}
                />
              </>
            )}
            <span style={{ position: "relative" }}>{tab.icon}</span>
            <span style={{
              fontFamily: "var(--font-heading)", fontSize: "9.5px",
              letterSpacing: "0.14em", position: "relative",
            }}>
              {tab.label.toUpperCase()}
            </span>
          </button>
        );
      })}
    </div>
  );
}

/* ── Main ──────────────────────────────────────── */
export default function App() {
  const [tab, setTab] = useState<Tab>("presence");
  const [connected, setConnected] = useState(false);
  const [location, setLocation] = useState("Waiting for game data...");
  const [activity, setActivity] = useState("-");
  const [elapsed, setElapsed] = useState("-");
  const [party, setParty] = useState<(Character | null)[]>([]);
  const [activeSlot, setActiveSlot] = useState<number | null>(0);
  const [settings, setSettings] = useState<Settings>({
    username: "",
    mcAether: true,
    wandererName: "Wanderer",
    manekinName: "Manekin",
    manekinaName: "Manekina",
  });

  /* Load persisted settings once the backend bridge is available.
     pywebview injects window.pywebview asynchronously (in a thread after
     page load), so the bridge may not exist on the first mount — keep
     retrying until it's exposed. */
  useEffect(() => {
    let cancelled = false;
    let attempts = 0;
    const load = () => {
      if (cancelled) return;
      if (!window.pywebview?.api?.get_settings) {
        attempts++;
        if (attempts < 100) setTimeout(load, 200); // retry for up to ~20s
        return;
      }
      window.pywebview!.api.get_settings!()
        .then(s => {
          if (!cancelled && s && Object.keys(s).length) {
            setSettings(prev => ({ ...prev, ...s }));
          }
        })
        .catch(() => {});
    };
    load();
    return () => { cancelled = true; };
  }, []);

  /* Persist a settings patch; engine-facing keys reach shared_config.json */
  const updateSettings = (patch: Partial<Settings>) => {
    setSettings(prev => ({ ...prev, ...patch }));
    if (hasBackend()) {
      window.pywebview!.api.save_settings?.(patch)?.catch(() => {});
    }
  };

  /* Live engine log lines, shown in the Logs tab. */
  const [logs, setLogs] = useState<string[]>([]);
  useEffect(() => {
    let alive = true;
    const tick = () => {
      if (!window.pywebview?.api?.get_logs) return;
      window.pywebview!.api.get_logs!()
        .then(lines => {
          if (alive && Array.isArray(lines)) setLogs(lines);
        })
        .catch(() => {});
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  /* Poll backend engine state (or demo simulator when running in a browser) */
  const connectedRef = useRef(false);

  useEffect(() => {
    let alive = true;
    const tick = () => {
      fetchState(connectedRef.current)
        .then(s => {
          if (!alive) return;
          connectedRef.current = s.running;
          setConnected(s.running);
          setLocation(s.location || "Unknown");
          setActivity(s.activity || "None");
          setElapsed(fmtElapsed(s.timestamp));
          setParty(s.party.map(p => (p ? { ...p } : null)));
          setActiveSlot(prev =>
            prev !== null ? prev : (s.active_character_index >= 0 ? s.active_character_index : null));
        })
        .catch(() => {});
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  /* CONNECT / DISCONNECT starts or stops the detection + RPC engine */
  const toggleConnection = () => {
    if (hasBackend()) {
      window.pywebview!.api.toggle_connection()
        .then(r => { connectedRef.current = r.running; setConnected(r.running); })
        .catch(() => {});
    } else {
      connectedRef.current = !connectedRef.current;
      setConnected(connectedRef.current);
    }
  };

  const activeChar = party[activeSlot ?? 0] ?? null;
  const activeEl = activeChar?.element ?? "geo";

  return (
    <div className="size-full flex items-center justify-center p-5"
      style={{ background: "radial-gradient(ellipse 80% 60% at 40% 30%,#0c1030 0%,#08091a 65%,#060810 100%)" }}
    >
      <div className="w-full max-w-5xl relative panel-halo"
        style={{
          background: "linear-gradient(145deg,#0c1028 0%,#090d1e 50%,#080a18 100%)",
          border: "1px solid rgba(200,168,75,0.22)",
          borderRadius: 6,
          transition: "box-shadow 0.6s ease",
        }}
      >
        {/* Ambient glow */}
        <div className="absolute inset-0 pointer-events-none animate-breathe"
          style={{
            background: `radial-gradient(ellipse 70% 50% at 50% 50%,${EL_COLOR[activeEl]}16,transparent 70%)`,
            borderRadius: 6, transition: "background 1s ease",
          }}
        />

        <ParticleField />

        <span className="corner tl corner-lg" style={{ opacity: 0.7 }} />
        <span className="corner tr corner-lg" style={{ opacity: 0.7 }} />
        <span className="corner bl corner-lg" style={{ opacity: 0.7 }} />
        <span className="corner br corner-lg" style={{ opacity: 0.7 }} />

        {/* ── Header ── */}
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
                <polygon points="12,2 15,9 22,9 16.5,14 18.5,21 12,17 5.5,21 7.5,14 2,9 9,9" fill="#c8a84b" opacity="0.95"/>
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
              <div style={{ fontFamily: "var(--font-heading)", fontSize: "8px", color: "#6a5820", letterSpacing: "0.22em", marginTop: 2 }}>
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
              fontFamily: "var(--font-heading)", fontSize: "8.5px",
              color: connected ? "#c8a84b" : "#555568", letterSpacing: "0.14em",
            }}>
              {connected ? "CONNECTED" : "OFFLINE"}
            </span>
          </button>
        </div>

        {/* ── Tab bar ── */}
        <div className="relative">
          <TabBar active={tab} onChange={setTab} />
        </div>

        {/* ── Tab content ── */}
        <div className="relative px-5 pb-5 pt-4 flex flex-col gap-5"
          
        >
          {tab === "presence" && (
            <>
              <div className="grid grid-cols-1 xl:grid-cols-[1.15fr_1fr] gap-x-8 gap-y-5 items-start">
              <div className="flex flex-col gap-5 min-w-0">
              {/* Party */}
              <div>
                <OrnamentDivider label="ACTIVE PARTY" />
                <div className="grid grid-cols-2 gap-3 mt-3.5 sm:grid-cols-4">
                  {party.map((char, i) => (
                    <CharacterSlot key={i} character={char} index={i}
                      isActive={activeSlot === i}
                      onClick={() => setActiveSlot(activeSlot === i ? null : i)}
                    />
                  ))}
                </div>

                {activeChar && (
                  <div className="mt-3 flex items-center gap-3 px-3 py-2.5 rounded"
                    style={{
                      background: `linear-gradient(90deg,${EL_COLOR[activeEl]}10,transparent 80%)`,
                      border: `1px solid ${EL_COLOR[activeEl]}28`,
                    }}
                  >
                    <div style={{
                      width: 5, height: 32, borderRadius: 3, flexShrink: 0,
                      background: EL_COLOR[activeEl],
                      boxShadow: `0 0 8px ${EL_COLOR[activeEl]}`,
                    }} />
                    <div className="flex flex-col gap-0.5">
                      <span style={{ fontFamily: "var(--font-heading)", fontSize: "11px", color: EL_COLOR[activeEl], letterSpacing: "0.06em" }}>
                        {activeChar.name}
                      </span>
                      <div className="flex items-center gap-2">
                        <ElBadge el={activeEl} />
                        <Stars n={activeChar.rarity ?? 5} color={activeChar.rarity === 5 ? "#e8c96a" : "#b090e0"} />
                        <span style={{ fontFamily: "var(--font-heading)", fontSize: "8.5px", color: "#6a5820" }}>
                          {activeChar.level != null ? `Lv.${activeChar.level}` : ""}
                        </span>
                      </div>
                    </div>
                    <span style={{ fontFamily: "var(--font-body)", fontStyle: "italic", fontSize: "13px", color: "rgba(200,168,75,0.35)", marginLeft: "auto" }}>
                      Selected
                    </span>
                  </div>
                )}
              </div>

              </div>
              <div className="flex flex-col gap-5 min-w-0">
              {/* Status */}
              <div>
                <OrnamentDivider label="STATUS" />
                <div className="mt-3 rounded overflow-hidden"
                  style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}
                >
                  <InfoRow
                    icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>}
                    label="LOCATION" value={location}
                  />

                  <InfoRow
                    icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>}
                    label="ACTIVITY" value={activity}
                  />

                  <InfoRow
                    icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>}
                    label="SESSION TIME" value={elapsed}
                  />
                </div>
              </div>

              {/* Discord preview */}
              <div className="rounded overflow-hidden"
                style={{ background: "rgba(88,101,242,0.07)", border: "1px solid rgba(88,101,242,0.2)" }}
              >
                <div className="px-4 py-3 flex items-center gap-3">
                  <div className="flex-shrink-0 flex items-center justify-center rounded-full"
                    style={{ width: 34, height: 34, background: "rgba(88,101,242,0.18)", border: "1px solid rgba(88,101,242,0.32)" }}
                  >
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="#7289da">
                      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057.101 18.079.11 18.1.127 18.114a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
                    </svg>
                  </div>
                  <div className="flex flex-col min-w-0 flex-1">
                    <span style={{ fontFamily: "var(--font-heading)", fontSize: "8.5px", color: "#7289da", letterSpacing: "0.14em", marginBottom: 2 }}>
                      DISCORD PREVIEW
                    </span>
                    <span style={{ fontFamily: "var(--font-body)", fontSize: "13.5px", color: "#b0b8d8", lineHeight: 1.4 }}>
                      Playing <span style={{ color: "#ede3c4", fontStyle: "italic" }}>Genshin Impact</span>
                      {" "}· {location.split("—")[0].trim()} · {elapsed}
                    </span>
                  </div>
                  <div style={{
                    width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                    backgroundColor: connected ? "#64d250" : "#555568",
                    boxShadow: connected ? "0 0 6px #64d250" : "none",
                  }} />
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-0.5">
                <span style={{ fontFamily: "var(--font-heading)", fontSize: "7.5px", color: "#3a3020", letterSpacing: "0.14em" }}>
                  v1.0.0 · GENSHIN PRESENCE
                </span>
                <button onClick={toggleConnection}
                  className="px-4 py-1.5 rounded cursor-pointer transition-all duration-300"
                  style={{
                    fontFamily: "var(--font-heading)", fontSize: "9px", letterSpacing: "0.12em",
                    color: connected ? "#08091a" : "#c8a84b",
                    background: connected ? "linear-gradient(135deg,#d4b055 0%,#a88c3c 100%)" : "rgba(200,168,75,0.08)",
                    border: connected ? "1px solid #c8a84b" : "1px solid rgba(200,168,75,0.28)",
                    outline: "none",
                    boxShadow: connected ? "0 0 14px rgba(200,168,75,0.3)" : "none",
                  }}
                >
                  {connected ? "DISCONNECT" : "CONNECT"}
                </button>
              </div>
              </div>
              </div>
            </>
          )}

          {tab === "settings" && (
            <SettingsPanel settings={settings} onSave={updateSettings} />
          )}

          {tab === "logs" && <LogsPanel logs={logs} />}

          {tab === "about" && <AboutPanel />}
        </div>
      </div>
    </div>
  );
}
