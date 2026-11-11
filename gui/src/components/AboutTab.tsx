import { useState } from "react";
import { Card } from "./ui";
import { CopyIcon, ExternalLinkIcon, GenshinMark } from "./Icons";

const DISCLAIMER =
  "Genshin Impact and all related assets are property of HoYoverse. " +
  "This tool is a fan-made, unofficial project and is not affiliated with " +
  "or endorsed by HoYoverse in any way.";

const LINKS = [
  { label: "GitHub repository", href: "https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence" },
  { label: "Report an issue", href: "https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence/issues" },
  { label: "Releases", href: "https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence/releases" },
];

export function AboutTab() {
  const [copied, setCopied] = useState(false);

  const copyDisclaimer = async () => {
    try {
      await navigator.clipboard.writeText(DISCLAIMER);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = DISCLAIMER;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="card-pad flex items-center gap-4">
          <span className="flex items-center justify-center w-12 h-12 rounded-full border border-[rgba(212,175,106,0.35)] bg-[rgba(212,175,106,0.08)] text-[var(--color-gold)] shrink-0">
            <GenshinMark size={22} />
          </span>
          <div>
            <div className="font-display text-[16px] text-[var(--color-gold-bright)]">
              Genshin Impact Rich Presence
            </div>
            <div className="text-[12px] text-[var(--color-faint)] mt-0.5">
              v3.0 · Windows · Python + React
            </div>
          </div>
        </div>
      </Card>

      <Card title="Links">
        <div className="divide-y divide-[var(--color-line)]">
          {LINKS.map(l => (
            <a
              key={l.label}
              href={l.href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between gap-3 px-4 py-3 text-[14px] text-[var(--color-text)] hover:bg-white/[0.03] transition-colors"
            >
              {l.label}
              <ExternalLinkIcon size={13} className="text-[var(--color-faint)]" />
            </a>
          ))}
        </div>
      </Card>

      <Card title="Disclaimer">
        <div className="card-pad">
          <p className="text-[13px] leading-relaxed text-[var(--color-muted)]">{DISCLAIMER}</p>
          <button
            onClick={copyDisclaimer}
            className="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[var(--color-line)] text-[11px] font-heading tracking-wider text-[var(--color-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-gold)]/40 transition-colors cursor-pointer"
          >
            <CopyIcon size={11} />
            {copied ? "Copied" : "Copy disclaimer"}
          </button>
        </div>
      </Card>
    </div>
  );
}
