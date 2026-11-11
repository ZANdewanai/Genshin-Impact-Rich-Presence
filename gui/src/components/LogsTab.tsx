import { useEffect, useRef, useState } from "react";
import type { DebugConfig } from "../types";
import { Card, Toggle } from "./ui";
import { CopyIcon } from "./Icons";

function DebugRow({ title, desc, checked, onChange, children }: {
  title: string;
  desc: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  children?: React.ReactNode;
}) {
  return (
    <div className="px-4 py-3 border-b border-[var(--color-line)] last:border-b-0">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="text-[13.5px] text-[var(--color-text)]">{title}</div>
          <p className="mt-0.5 text-[12px] leading-snug text-[var(--color-faint)]">{desc}</p>
        </div>
        <Toggle label={title} checked={checked} onChange={onChange} />
      </div>
      {children && <div className="mt-2.5">{children}</div>}
    </div>
  );
}

export function LogsTab({ logs, debug, onDebugChange }: {
  logs: string[];
  debug: DebugConfig;
  onDebugChange: (patch: Partial<DebugConfig>) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <Card title="Debug">
        <DebugRow
          title="Engine debug logs"
          desc="Verbose engine output. Required for the console below."
          checked={debug.debugMode}
          onChange={v => onDebugChange({ debugMode: v })}
        />
        <DebugRow
          title="Character detection debug"
          desc="Extra OCR detail when reading names from the party screen."
          checked={debug.debugCharacterMode}
          onChange={v => onDebugChange({ debugCharacterMode: v })}
        />
        <DebugRow
          title="Static image debug"
          desc="Read name regions from a screenshot file instead of the live screen."
          checked={debug.debugStaticImage}
          onChange={v => onDebugChange({ debugStaticImage: v })}
        >
          <input
            className="input font-mono !text-[12px]"
            value={debug.debugStaticImagePath}
            placeholder="debug_images\\debug_image.jpg"
            onChange={e => onDebugChange({ debugStaticImagePath: e.target.value })}
          />
        </DebugRow>
      </Card>

      <LogConsole logs={logs} enabled={debug.debugMode} />
    </div>
  );
}

function LogConsole({ logs, enabled }: { logs: string[]; enabled: boolean }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [pinned, setPinned] = useState(true);

  useEffect(() => {
    if (pinned) bottomRef.current?.scrollIntoView({ block: "end" });
  }, [logs.length, pinned]);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    setPinned(el.scrollHeight - el.scrollTop - el.clientHeight < 48);
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(logs.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard unavailable */ }
  };

  return (
    <Card
      title="Engine output"
      actions={
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[var(--color-faint)]">
            {logs.length} {logs.length === 1 ? "line" : "lines"}
          </span>
          <button
            onClick={copy}
            disabled={logs.length === 0}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-[var(--color-line)] text-[11px] font-heading tracking-wider text-[var(--color-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-gold)]/40 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            <CopyIcon size={11} />
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      }
    >
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-[420px] overflow-y-auto px-4 py-3 select-text"
      >
        {!enabled ? (
          <p className="text-[13px] text-[var(--color-faint)] italic">
            Enable “Engine debug logs” above to stream engine output here.
          </p>
        ) : logs.length === 0 ? (
          <p className="text-[13px] text-[var(--color-faint)] italic">
            No output yet — start the engine from the Live tab.
          </p>
        ) : (
          logs.map((line, i) => (
            <div key={i} className={`log-line ${/error|exception|traceback/i.test(line) ? "error" : /warn/i.test(line) ? "warn" : ""}`}>
              {line}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </Card>
  );
}
