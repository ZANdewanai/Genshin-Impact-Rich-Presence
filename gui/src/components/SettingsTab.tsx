import { SettingsPanel } from "./SettingsPanel";
import { OrnamentDivider } from "./SmallComponents";
import { ToggleSwitch } from "./FormComponents";
import type { Settings, DebugConfig } from "../types";

interface SettingsTabProps {
  settings: Settings;
  onSave: (s: Partial<Settings>) => void;
  debug: DebugConfig;
  onDebugChange: (d: Partial<DebugConfig>) => void;
}

export function SettingsTab({ settings, onSave, debug, onDebugChange }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel settings={settings} onSave={onSave} />

      <div className="panel-card mb-4">
        <div className="px-4 py-3">
          <span style={{
            fontFamily: "var(--font-heading)",
            fontSize: "12px",
            color: "#ede3c4",
            letterSpacing: "0.05em",
          }}>
            ENGINE DEBUG SETTINGS
          </span>
          <span style={{
            fontFamily: "var(--font-body)",
            fontSize: "12.5px",
            color: "#6a5820",
            lineHeight: 1.4,
            display: "block",
            marginTop: 4,
          }}>
            Toggle verbose engine output and character-detection logging. Maps to CONFIG DEBUG_MODE, DEBUG_CHARACTER_MODE, and DEBUG_STATIC_IMAGE.
          </span>
        </div>

        <div className="status-row">
          <div className="status-label">
            <span className="status-title">Engine Debug Logs</span>
            <span className="status-desc">General verbose engine output (DEBUG_MODE)</span>
          </div>
          <button
            type="button"
            onClick={() => onDebugChange({ debugMode: !debug.debugMode })}
            className={`toggle-switch ${debug.debugMode ? "on" : "off"}`}
            aria-pressed={debug.debugMode}
          >
            <span className={`toggle-thumb ${debug.debugMode ? "on" : "off"}`} />
          </button>
        </div>

        <div className="status-row">
          <div className="status-label">
            <span className="status-title">Character Detection Debug</span>
            <span className="status-desc">Extra OCR debug output for character name detection (DEBUG_CHARACTER_MODE)</span>
          </div>
          <button
            type="button"
            onClick={() => onDebugChange({ debugCharacterMode: !debug.debugCharacterMode })}
            className={`toggle-switch ${debug.debugCharacterMode ? "on" : "off"}`}
            aria-pressed={debug.debugCharacterMode}
          >
            <span className={`toggle-thumb ${debug.debugCharacterMode ? "on" : "off"}`} />
          </button>
        </div>

        <div className="status-row">
          <div className="status-label flex-1">
            <span className="status-title">Static Image Debug</span>
            <span className="status-desc">Read character name regions from a static screenshot instead of the live screen (DEBUG_STATIC_IMAGE)</span>
            <input
              type="text"
              value={debug.debugStaticImagePath}
              onChange={e => onDebugChange({ debugStaticImagePath: e.target.value })}
              placeholder="debug_images\debug_image.jpg"
              className="mt-1 px-2 py-1 rounded text-xs"
              style={{
                background: "rgba(8,9,26,0.5)",
                border: "1px solid rgba(200,168,75,0.2)",
                color: "#ede3c4",
                fontFamily: "var(--font-body)",
                outline: "none",
                width: "100%",
                maxWidth: 320,
              }}
            />
          </div>
          <button
            type="button"
            onClick={() => onDebugChange({ debugStaticImage: !debug.debugStaticImage })}
            className={`toggle-switch ${debug.debugStaticImage ? "on" : "off"}`}
            aria-pressed={debug.debugStaticImage}
          >
            <span className={`toggle-thumb ${debug.debugStaticImage ? "on" : "off"}`} />
          </button>
        </div>
      </div>
    </>
  );
}