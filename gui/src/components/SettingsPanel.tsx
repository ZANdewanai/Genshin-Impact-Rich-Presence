import { useState, useEffect } from "react";
import type { Settings } from "../types";
import { OrnamentDivider } from "./SmallComponents";
import { TextField, ApplyButton, ToggleSwitch } from "./FormComponents";

export function SettingsPanel({ settings, onSave }: {
  settings: Settings; onSave: (s: Partial<Settings>) => void;
}) {
  const [form, setForm] = useState<Settings>(settings);
  const [savedKey, setSavedKey] = useState<string | null>(null);

  useEffect(() => { setForm(settings); }, [settings]);

  const set = (patch: Partial<Settings>) => setForm(prev => ({ ...prev, ...patch }));

  const apply = (key: keyof Settings) => {
    onSave({ [key]: form[key] } as Partial<Settings>);
    setSavedKey(key);
    setTimeout(() => setSavedKey(prev => (prev === key ? null : prev)), 2000);
  };

  const isDirty = (key: keyof Settings) => form[key] !== settings[key];
  const isSaved = (key: keyof Settings) => savedKey === key && !isDirty(key);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <OrnamentDivider label="IDENTITY" />
        <div className="mt-3 rounded overflow-hidden" style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}>
          <TextField label="TRAVELER NAME" value={form.username}
            dirty={isDirty("username")} saved={isSaved("username")}
            onChange={v => set({ username: v })} onApply={() => apply("username")}
            hint="✓ Applied live. Your player name, shown in party-related presence text." />

          <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
            <div style={{ fontFamily: "var(--font-heading)", fontSize: "10px", color: "#6a5820", letterSpacing: "0.16em", marginBottom: 6 }}>
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