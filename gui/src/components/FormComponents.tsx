export function InfoRow({ icon, label, value, onClick }: {
  icon: React.ReactNode; label: string; value: string; onClick?: () => void;
}) {
  return (
    <div onClick={onClick}
      className={`flex items-start gap-3 px-4 py-3 group ${onClick ? "cursor-pointer hover:bg-white/[0.02]" : ""} transition-colors`}
      style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
      <div className="mt-0.5 flex-shrink-0" style={{ color: "#c8a84b", opacity: 0.65 }}>{icon}</div>
      <div className="flex flex-col gap-0.5 min-w-0 flex-1">
        <span style={{ fontFamily: "var(--font-heading)", fontSize: "10px", color: "#6a5820", letterSpacing: "0.16em" }}>
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

export function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      type="button"
      onClick={onChange}
      className="relative inline-flex items-center rounded-full cursor-pointer transition-colors duration-200 flex-shrink-0"
      style={{
        width: 34, height: 18, outline: "none",
        background: checked ? "rgba(200,168,75,0.85)" : "rgba(200,168,75,0.12)",
        border: `1px solid ${checked ? "rgba(200,168,75,0.6)" : "rgba(200,168,75,0.25)"}`,
      }}
      aria-pressed={checked}
    >
      <span
        className="absolute rounded-full transition-transform duration-200"
        style={{
          width: 12, height: 12, top: 2, left: 2,
          background: checked ? "#08091a" : "#c8a84b",
          transform: checked ? "translateX(16px)" : "translateX(0)",
        }}
      />
    </button>
  );
}

export function ApplyButton({ dirty, saved, onApply }: {
  dirty: boolean; saved: boolean; onApply: () => void;
}) {
  if (!dirty) return null;
  return (
    <button onClick={onApply} className="px-2.5 py-1 rounded cursor-pointer transition-all duration-200 flex-shrink-0"
      style={{
        fontFamily: "var(--font-heading)", fontSize: "9.5px", letterSpacing: "0.1em",
        background: saved ? "rgba(100,210,80,0.15)" : "rgba(200,168,75,0.1)",
        border: saved ? "1px solid rgba(100,210,80,0.4)" : "1px solid rgba(200,168,75,0.35)",
        color: saved ? "#64d250" : "#c8a84b", outline: "none",
      }}>
      {saved ? "SAVED" : "APPLY"}
    </button>
  );
}

export function TextField({ label, hint, value, dirty, saved, onChange, onApply }: {
  label: string; hint?: string; value: string;
  dirty: boolean; saved: boolean;
  onChange: (v: string) => void; onApply: () => void;
}) {
  return (
    <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(200,168,75,0.07)" }}>
      <div style={{ fontFamily: "var(--font-heading)", fontSize: "10px", color: "#6a5820", letterSpacing: "0.16em", marginBottom: 6 }}>
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