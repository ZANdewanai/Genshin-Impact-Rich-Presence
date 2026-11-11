import type { ReactNode } from "react";

export function Toggle({ checked, onChange, label }: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`toggle ${checked ? "on" : ""}`}
    >
      <span className="toggle-thumb" />
    </button>
  );
}

export function ApplyButton({ dirty, saved, onApply }: {
  dirty: boolean;
  saved: boolean;
  onApply: () => void;
}) {
  if (!dirty && !saved) return null;
  return (
    <button
      type="button"
      onClick={onApply}
      disabled={!dirty}
      className={`apply-btn ${saved ? "saved" : ""}`}
    >
      {dirty ? "Apply" : "Saved"}
    </button>
  );
}

/* Labelled text input with an apply-on-dirty button (Enter also applies). */
export function TextField({ label, hint, value, savedValue, saved, onChange, onApply, placeholder }: {
  label: string;
  hint?: string;
  value: string;
  savedValue: string;
  saved: boolean;
  onChange: (v: string) => void;
  onApply: () => void;
  placeholder?: string;
}) {
  const dirty = value !== savedValue;
  return (
    <div className="px-4 py-3 border-b border-[var(--color-line)] last:border-b-0">
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="field-label">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <input
          className={`input ${dirty ? "input-dirty" : ""}`}
          value={value}
          placeholder={placeholder}
          onChange={e => onChange(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && dirty) onApply(); }}
        />
        <ApplyButton dirty={dirty} saved={saved} onApply={onApply} />
      </div>
      {hint && <p className="mt-1.5 text-[12px] leading-snug text-[var(--color-faint)]">{hint}</p>}
    </div>
  );
}

export function Card({ title, children, actions, className }: {
  title?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card ${className ?? ""}`}>
      {title && (
        <header className="flex items-center justify-between gap-2 px-4 py-3 border-b border-[var(--color-line)]">
          <h2 className="section-title">{title}</h2>
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}
