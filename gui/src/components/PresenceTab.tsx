import type { Character, Element } from "../types";
import { EL_COLOR, rarityColor } from "../constants";
import {
  CharacterSlot,
  OrnamentDivider,
  LocationIcon,
  StateIcon,
  TimeIcon,
  AssetIcon,
  DiscordIcon,
  TriangleIcon,
} from ".";

interface PresenceTabProps {
  party: (Character | null)[];
  activeCharacterIndex: number | null;
  location: string;
  activity: string;
  elapsed: string;
  connected: boolean;
  onToggle: () => void;
  discordDetails?: string;
  discordState?: string;
  discordLargeImage?: string;
  discordLargeText?: string;
  discordSmallImage?: string;
  discordSmallText?: string;
}

export function PresenceTab({
  party,
  activeCharacterIndex,
  location,
  activity,
  elapsed,
  connected,
  onToggle,
  discordDetails,
  discordState,
  discordLargeImage,
  discordLargeText,
  discordSmallImage,
  discordSmallText,
}: PresenceTabProps) {
  const activeChar = party[activeCharacterIndex ?? 0] ?? null;
  const activeEl: Element = activeChar?.element ?? "geo";
  const elColor = EL_COLOR[activeEl];

  return (
    <>
      <div className="flex flex-col gap-4">
        <div>
          <OrnamentDivider label="ACTIVE PARTY" />
          <div className="flex flex-wrap justify-center gap-3 mt-3">
            {party.map((char, i) => char ? (
              <CharacterSlot key={i} character={char} index={i}
                isActive={activeCharacterIndex === i}
              />
            ) : null)}
          </div>

          {activeChar && (
            <div className="active-char-card"
              style={{
                background: `linear-gradient(90deg,${elColor}10,transparent 80%)`,
                borderColor: `${elColor}28`,
              }}
            >
              <div className="active-char-bar" style={{ background: elColor }} />
              <div className="flex flex-col gap-0.5">
                <span className="active-char-name" style={{ color: elColor }}>
                  {activeChar.name}
                </span>
                <div className="active-char-meta">
                  <span className="active-char-level">
                    {activeChar.level != null ? `Lv.${activeChar.level}` : ""}
                  </span>
                  <span className="active-char-element"
                    style={{
                      background: `${elColor}18`,
                      borderColor: `${elColor}50`,
                      color: elColor,
                    }}
                  >
                    {activeEl === "empty" ? "—" : activeEl.charAt(0).toUpperCase() + activeEl.slice(1)}
                  </span>
                  <span className="active-char-rarity">
                    {Array.from({ length: activeChar.rarity ?? 5 }).map((_, i) => (
                      <svg key={i} width="9" height="9" viewBox="0 0 10 10" fill={activeChar.rarity === 5 ? "#FFD780" : "#B48AE6"}>
                        <polygon points="5,0.5 6.6,3.4 9.5,5 6.6,6.6 5,9.5 3.4,6.6 0.5,5 3.4,3.4"/>
                      </svg>
                    ))}
                  </span>
                  <span className="active-char-level" style={{ fontWeight: 500 }}>
                    {activeChar.level != null ? `Lv.${activeChar.level}` : ""}
                  </span>
                </div>
              </div>
              <span className="active-char-selected">Selected</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 items-start">
          <div>
            <OrnamentDivider label="STATUS" />
            <div className="panel-card mt-3">
              <div className="info-row">
                <LocationIcon className="info-icon" />
                <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                  <span className="info-label">DETAILS</span>
                  <span className="info-value">{discordDetails || location || "—"}</span>
                </div>
              </div>

              <div className="info-row">
                <StateIcon className="info-icon" />
                <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                  <span className="info-label">STATE</span>
                  <span className="info-value">{discordState || activity || "—"}</span>
                </div>
              </div>

              <div className="info-row">
                <TimeIcon className="info-icon" />
                <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                  <span className="info-label">SESSION TIME</span>
                  <span className="info-value">{elapsed}</span>
                </div>
              </div>

              {(discordLargeImage || discordLargeText || discordSmallImage || discordSmallText) && (
                <div className="info-row">
                  <AssetIcon className="info-icon" />
                  <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                    <span className="info-label">ASSETS</span>
                    <span className="info-value" style={{ fontSize: "12px" }}>
                      L: {discordLargeImage || "—"} {discordLargeText ? `("${discordLargeText}")` : ""}
                      {discordSmallImage ? ` · S: ${discordSmallImage}` : ""} {discordSmallText ? `("${discordSmallText}")` : ""}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="panel-card-blue">
            <div className="px-4 py-3 flex items-center gap-3">
              <DiscordIcon className="discord-preview-icon" />
              <div className="flex flex-col min-w-0 flex-1">
                <span style={{
                  fontFamily: "var(--font-heading)",
                  fontSize: "10px",
                  color: "#7289da",
                  letterSpacing: "0.14em",
                  marginBottom: 2,
                }}>
                  DISCORD PREVIEW
                </span>
                <span style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "13.5px",
                  color: "#b0b8d8",
                  lineHeight: 1.4,
                }}>
                  Playing <span style={{ color: "#ede3c4", fontStyle: "italic" }}>Genshin Impact</span>
                  {discordDetails ? ` · ${discordDetails}` : ` · {location.split("—")[0].trim()}`}
                  {discordState ? ` · ${discordState}` : ` · {elapsed}`}
                </span>
              </div>
              <div style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                flexShrink: 0,
                backgroundColor: connected ? "#64d250" : "#555568",
                boxShadow: connected ? "0 0 6px #64d250" : "none",
              }} />
            </div>
          </div>

          <div className="flex items-center justify-between pt-0.5 md:col-span-2">
            <span style={{
              fontFamily: "var(--font-heading)",
              fontSize: "9px",
              color: "#3a3020",
              letterSpacing: "0.14em",
            }}>
              v3.0 · GENSHIN PRESENCE
            </span>
            <button onClick={onToggle}
              className="px-4 py-1.5 rounded cursor-pointer transition-all duration-300"
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "10.5px",
                letterSpacing: "0.12em",
                color: connected ? "#08091a" : "#c8a84b",
                background: connected ? "linear-gradient(135deg,#d4b055 0%,#a88c3c 100%)" : "rgba(200,168,75,0.08)",
                border: connected ? "1px solid #c8a84b" : "1px solid rgba(200,168,75,0.28)",
                outline: "none",
                boxShadow: connected ? "0 0 14px rgba(200,168,75,0.3)" : "none",
              }}
            >
              {connected ? "DISCONNECT" : "CONNECT"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}