import { LogsPanel } from "./LogsPanel";
import { OrnamentDivider } from "./SmallComponents";
import type { DebugConfig } from "../types";

interface LogsTabProps {
  logs: string[];
  debug: DebugConfig;
}

export function LogsTab({ logs, debug }: LogsTabProps) {
  return (
    <div>
      <div className="rounded overflow-hidden mb-4"
        style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}
      >
        <div className="px-4 py-3">
          <span style={{ fontFamily: "var(--font-heading)", fontSize: "12px", color: "#ede3c4", letterSpacing: "0.05em" }}>
            ENGINE DEBUG SETTINGS
          </span>
          <span style={{ fontFamily: "var(--font-body)", fontSize: "12.5px", color: "#6a5820", lineHeight: 1.4, display: "block", marginTop: 4 }}>
            Toggle verbose engine output and character-detection logging. Maps to CONFIG DEBUG_MODE, DEBUG_CHARACTER_MODE, and DEBUG_STATIC_IMAGE.
          </span>
        </div>

        <div className="flex items-center justify-between gap-4 py-3 px-4"
          style={{ borderTop: "1px solid rgba(200,168,75,0.08)" }}
        >
          <div className="flex flex-col gap-0.5 min-w-0">
            <span style={{ fontFamily: "var(--font-body)", fontSize: "12.5px", color: "#c8a84b" }}>
              Engine Debug Logs
            </span>
            <span style={{ fontFamily: "var(--font-body)", fontSize: "11px", color: "#6a5820", lineHeight: 1.3 }}>
              General verbose engine output (DEBUG_MODE)
            </span>
          </div>
          <button
            type="button"
            onClick={() => window.pywebview?.api?.set_debug?.(!debug.debugMode, debug.debugCharacterMode, debug.debugStaticImage, debug.debugStaticImagePath)}
            className="relative inline-flex items-center rounded-full cursor-pointer transition-colors duration-200 flex-shrink-0"
            style={{
              width: 34, height: 18, outline: "none",
              background: debug.debugMode ? "rgba(200,168,75,0.85)" : "rgba(200,168,75,0.12)",
              border: `1px solid ${debug.debugMode ? "rgba(200,168,75,0.6)" : "rgba(200,168,75,0.25)"}`,
            }}
            aria-pressed={debug.debugMode}
          >
            <span
              className="absolute rounded-full transition-transform duration-200"
              style={{
                width: 12, height: 12, top: 2, left: 2,
                background: debug.debugMode ? "#08091a" : "#c8a84b",
                transform: debug.debugMode ? "translateX(16px)" : "translateX(0)",
              }}
            />
          </button>
        </div>
      </div>

      {debug.debugMode ? (
        <LogsPanel logs={logs} />
      ) : (
        <div className="rounded overflow-hidden"
          style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}
        >
          <div className="px-4 py-6 text-center">
            <span style={{ fontFamily: "var(--font-body)", fontSize: "13px", color: "#6a5820", lineHeight: 1.5 }}>
              Debug logging is disabled. Enable Engine Debug Logs above to view live engine output.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}