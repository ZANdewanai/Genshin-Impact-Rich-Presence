import { useState } from "react";
import { OrnamentDivider } from "./SmallComponents";
import { GenshinLogo, ExternalLinkIcon, CopyIcon } from "./Icons";

export function AboutPanel() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="about-header">
        <span className="corner tl" /><span className="corner tr" />
        <span className="corner bl" /><span className="corner br" />

        <div className="about-logo">
          <GenshinLogo size={28} />
        </div>

        <div className="about-title">
          Genshin Presence
        </div>

        <div className="about-version">
          VERSION 3.0
        </div>
      </div>

      <div>
        <OrnamentDivider label="DETAILS" />
        <div className="mt-3 rounded overflow-hidden grid grid-cols-2 gap-px" style={{ background: "rgba(200,168,75,0.1)", border: "1px solid rgba(200,168,75,0.14)" }}>
          {[
            { label: "VERSION", value: "3.0" },
            { label: "BUILT WITH", value: "Python · React · pywebview · RapidOCR" },
            { label: "GAME SUPPORT", value: "Genshin Impact (EN text)" },
            { label: "PLATFORM", value: "Windows only" },
            { label: "LICENSE", value: "MIT License" },
          ].map(({ label, value }) => (
            <div key={label} className="flex flex-col gap-1 px-4 py-2.5" style={{ background: "rgba(8,9,26,0.65)" }}>
              <span style={{ fontFamily: "var(--font-heading)", fontSize: "10px", color: "#6a5820", letterSpacing: "0.14em" }}>
                {label}
              </span>
              <span style={{ fontFamily: "var(--font-body)", fontSize: "13px", color: "#ede3c4", lineHeight: 1.3 }}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <OrnamentDivider label="LINKS" />
        <div className="mt-3 grid grid-cols-2 gap-2">
          {[
            { label: "GitHub Repo", sub: "github.com/ZANdewanai/…", href: "https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence" },
            { label: "Report Issue", sub: "Bugs & feedback", href: "https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence/issues" },
            { label: "Releases", sub: "Changelog & downloads", href: "https://github.com/ZANdewanai/Genshin-Impact-Rich-Presence/releases" },
          ].map(({ label, sub, href }) => (
            <a key={label} href={href} target="_blank" rel="noopener noreferrer" className="link-card">
              <div className="link-icon">
                <ExternalLinkIcon className="link-icon-symbol" />
                <span className="link-title">{label}</span>
              </div>
              <span className="link-sub">{sub}</span>
            </a>
          ))}
        </div>
      </div>

      <div>
        <OrnamentDivider label="ACKNOWLEDGEMENTS" />
        <div className="disclaimer-box">
          <p className="disclaimer-text">
            Genshin Impact and all related assets are property of{" "}
            <span style={{ color: "#ede3c4" }}>HoYoverse</span>. This tool is a{" "}
            <span style={{ color: "#ede3c4" }}>fan-made, unofficial</span> project and is not affiliated with or endorsed by HoYoverse in any way.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <div className="divider-gold" />
            <button onClick={handleCopy} className={`copy-btn ${copied ? "copied" : "default"}`}>
              {copied ? "COPIED ✓" : "COPY DISCLAIMER"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}