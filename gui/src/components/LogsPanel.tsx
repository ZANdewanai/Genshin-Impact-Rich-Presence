import { useState, useEffect, useRef } from "react";
import { OrnamentDivider } from "./SmallComponents";

export function LogsPanel({ logs }: { logs: string[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (!autoScroll) return;
    bottomRef.current?.scrollIntoView({ behavior: "auto" });
  }, [logs.length, autoScroll]);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    setAutoScroll(atBottom);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(logs.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const selection = window.getSelection();
      if (containerRef.current && selection) {
        const range = document.createRange();
        range.selectNodeContents(containerRef.current);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    }
  };

  return (
    <div>
      <OrnamentDivider label="ENGINE LOG" />
      <div className="mt-3 rounded overflow-hidden"
        style={{ background: "rgba(8,9,26,0.65)", border: "1px solid rgba(200,168,75,0.14)" }}>
        <div className="flex items-center justify-between px-3 py-1.5"
          style={{ borderBottom: "1px solid rgba(200,168,75,0.14)" }}>
          <span style={{ fontSize: "12px", color: "#6a7089" }}>
            {logs.length} {logs.length === 1 ? "line" : "lines"}
            {!autoScroll && logs.length > 0 && (
              <span style={{ color: "#6a5820", fontStyle: "italic" }}> · scrolled up</span>
            )}
          </span>
          <button
            onClick={handleCopy}
            disabled={logs.length === 0}
            className="rounded px-2.5 py-0.5 transition-colors"
            style={{
              fontSize: "12px",
              fontFamily: "var(--font-body)",
              color: copied ? "#ede3c4" : "#c8a84b",
              border: "1px solid rgba(200,168,75,0.35)",
              background: copied ? "rgba(200,168,75,0.15)" : "transparent",
              cursor: logs.length === 0 ? "not-allowed" : "pointer",
              opacity: logs.length === 0 ? 0.4 : 1,
            }}
          >
            {copied ? "✓ Copied" : "Copy"}
          </button>
        </div>
        <div
          ref={containerRef}
          onScroll={handleScroll}
          style={{
            maxHeight: 480, overflowY: "auto", padding: "12px 14px",
            fontFamily: "var(--font-body)", fontSize: "12px", lineHeight: 1.6,
            color: "#9aa0b8", userSelect: "text", cursor: "text",
          }}>
          {logs.length === 0 ? (
            <span style={{ color: "#6a5820", fontStyle: "italic" }}>
              No engine output yet. Press CONNECT to start the detection + RPC engine.
            </span>
          ) : (
            logs.map((line, i) => (
              <div key={i} style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                {line}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}