import type { Tab } from "../types";

export function TabBar({ active, onChange, needsSetup }: { active: Tab; onChange: (t: Tab) => void; needsSetup?: boolean }) {
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
        const showDot = tab.id === "settings" && !!needsSetup;
        const label = showDot ? "Setup" : tab.label;
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
                <div className="absolute inset-0" style={{ background: "rgba(200,168,75,0.04)" }} />
                <div className="absolute bottom-0 left-0 right-0 h-0.5 animate-shimmer"
                  style={{ background: "linear-gradient(90deg,transparent,#c8a84b,transparent)" }}
                />
              </>
            )}
            <span style={{ position: "relative" }}>{tab.icon}</span>
            <span style={{
              fontFamily: "var(--font-heading)", fontSize: "11px",
              letterSpacing: "0.14em", position: "relative",
            }}>
              {label.toUpperCase()}
            </span>
            {showDot && (
              <span title="Configure your username so your character can be detected"
                className="absolute top-2 right-[calc(50%-34px)] w-2 h-2 rounded-full animate-pulse"
                style={{
                  background: "#e8564b",
                  boxShadow: "0 0 6px 1px rgba(232,86,75,0.7)",
                }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
}