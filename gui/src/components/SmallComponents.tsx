import type { Element } from "../types";
import { EL_COLOR, EL_LABEL } from "../constants";

export function ElBadge({ el }: { el: Element }) {
  if (el === "empty") return null;
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-px rounded-sm" style={{
      background: `${EL_COLOR[el]}18`, border: `1px solid ${EL_COLOR[el]}50`,
      color: EL_COLOR[el], fontFamily: "var(--font-heading)", fontSize: "10px", letterSpacing: "0.09em",
    }}>
      {EL_LABEL[el]}
    </span>
  );
}

export function Stars({ n, color }: { n: number; color: string }) {
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

export function OrnamentDivider({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <div className="flex-1 h-px gold-line" />
      <svg width="10" height="10" viewBox="0 0 12 12" fill="#c8a84b" opacity={0.7}>
        <path d="M6 0l1.5 4.5L12 6l-4.5 1.5L6 12 4.5 7.5 0 6l4.5-1.5z"/>
      </svg>
      {label && (
        <span style={{ fontFamily: "var(--font-heading)", fontSize: "10.5px", color: "#c8a84b", letterSpacing: "0.18em", opacity: 0.85 }}>
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