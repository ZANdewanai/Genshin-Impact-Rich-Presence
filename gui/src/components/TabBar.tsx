import type { Tab } from "../types";
import { BoltIcon, GearIcon, ListIcon, InfoIcon } from "./Icons";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "presence", label: "Live", icon: <BoltIcon size={13} /> },
  { id: "settings", label: "Settings", icon: <GearIcon size={13} /> },
  { id: "logs", label: "Logs", icon: <ListIcon size={13} /> },
  { id: "about", label: "About", icon: <InfoIcon size={13} /> },
];

export function TabBar({ active, onChange, needsSetup }: {
  active: Tab;
  onChange: (t: Tab) => void;
  needsSetup?: boolean;
}) {
  return (
    <div className="flex items-center gap-1" role="tablist">
      {TABS.map(t => {
        const isActive = active === t.id;
        const showDot = t.id === "settings" && !!needsSetup;
        return (
          <button
            key={t.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(t.id)}
            className={`nav-tab relative ${isActive ? "active" : ""}`}
          >
            {t.icon}
            <span className="nav-label">{showDot ? "Setup" : t.label}</span>
            {showDot && (
              <span
                title="Set your traveler name so party detection works"
                className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#e8564b] animate-pulse"
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
