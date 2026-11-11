import { useEffect, useState } from "react";
import type { DebugConfig, Settings } from "../types";
import { Card, TextField, Toggle } from "./ui";

interface SettingsTabProps {
  settings: Settings;
  onSave: (patch: Partial<Settings>) => void;
  debug: DebugConfig;
  onDebugChange: (patch: Partial<DebugConfig>) => void;
}

export function SettingsTab({ settings, onSave, debug, onDebugChange }: SettingsTabProps) {
  const [form, setForm] = useState<Settings>(settings);
  const [savedKey, setSavedKey] = useState<string | null>(null);

  useEffect(() => { setForm(settings); }, [settings]);

  const set = (patch: Partial<Settings>) => setForm(prev => ({ ...prev, ...patch }));

  const apply = (key: keyof Settings) => {
    onSave({ [key]: form[key] } as Partial<Settings>);
    setSavedKey(key);
    setTimeout(() => setSavedKey(prev => (prev === key ? null : prev)), 2000);
  };

  const field = (key: keyof Settings) => ({
    value: String(form[key]),
    savedValue: String(settings[key]),
    saved: savedKey === key,
    onChange: (v: string) => set({ [key]: v } as Partial<Settings>),
    onApply: () => apply(key),
  });

  const mcDirty = form.mcAether !== settings.mcAether;
  const mcSaved = savedKey === "mcAether";

  return (
    <div className="flex flex-col gap-4">
      <Card title="Identity">
        <TextField
          label="Traveler name"
          hint="Your in-game username. Used to spot your character in the party and in presence text."
          placeholder="PlayerName"
          {...field("username")}
        />

        <div className="px-4 py-3 border-b border-[var(--color-line)]">
          <div className="field-label mb-1.5">Main character</div>
          <div className="flex items-center gap-2">
            <select
              className="input flex-1"
              value={form.mcAether ? "aether" : "lumine"}
              onChange={e => set({ mcAether: e.target.value === "aether" })}
            >
              <option value="aether">Aether</option>
              <option value="lumine">Lumine</option>
            </select>
            <button
              type="button"
              onClick={() => apply("mcAether")}
              disabled={!mcDirty}
              className={`apply-btn ${mcSaved ? "saved" : ""}`}
            >
              {mcSaved ? "Saved" : "Apply"}
            </button>
          </div>
          <p className="mt-1.5 text-[12px] leading-snug text-[var(--color-faint)]">
            Which twin you play as — needed to tell your character apart in co-op parties.
          </p>
        </div>

        <TextField
          label="Wanderer name"
          hint="Custom name shown when Wanderer is detected. Only change it if you renamed him in-game."
          {...field("wandererName")}
        />
        <TextField
          label="Manekin name"
          hint="Custom name shown when Wonderland Manekin is detected."
          {...field("manekinName")}
        />
        <TextField
          label="Manekina name"
          hint="Custom name shown when Wonderland Manekina is detected."
          {...field("manekinaName")}
        />
      </Card>

      <Card title="Engine">
        <div className="flex items-center justify-between gap-4 px-4 py-3">
          <div className="min-w-0">
            <div className="text-[13.5px] text-[var(--color-text)]">GPU acceleration</div>
            <p className="mt-0.5 text-[12px] leading-snug text-[var(--color-faint)]">
              Uses the GPU for OCR detection. Applies the next time the engine starts.
            </p>
          </div>
          <Toggle
            label="GPU acceleration"
            checked={form.useGpu}
            onChange={v => {
              set({ useGpu: v });
              onSave({ useGpu: v });
            }}
          />
        </div>
      </Card>
    </div>
  );
}
