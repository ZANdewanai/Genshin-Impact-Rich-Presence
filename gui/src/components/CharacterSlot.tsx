import type { Character, Element } from "../types";
import { EL_COLOR, rarityColor } from "../constants";
import { ElBadge, Stars, OrnamentDivider } from "./SmallComponents";

export function CharacterSlot({ character, index, isActive }: {
  character: Character | null; index: number; isActive: boolean;
}) {
  const el = character?.element ?? "empty";
  const clr = EL_COLOR[el];
  const rclr = rarityColor(character?.rarity);
  const animClass = ["slide-up-1","slide-up-2","slide-up-3","slide-up-4"][index];
  return (
    <button
      className={`relative flex flex-col overflow-hidden group flex-1 ${animClass} slot-glow glow-${el} ${isActive ? "active" : ""}`}
      style={{
        background: character ? "linear-gradient(170deg,#0d1122 0%,#0a0d1a 100%)" : "rgba(10,13,26,0.5)",
        border: character ? `1px solid ${rclr}55` : "1px solid rgba(200,168,75,0.18)",
        boxShadow: isActive 
          ? `0 8px 18px rgba(0,0,0,0.45), 0 0 12px ${rclr}50, inset 0 0 16px rgba(var(--el-clr), 0.06)`
          : character ? `0 0 10px rgba(var(--el-clr), 0.0)` : undefined,
        borderRadius: 4, aspectRatio: "3 / 4", maxWidth: "150px", outline: "none",
        transform: isActive ? "translateY(-3px)" : "translateY(0)",
        transition: "transform 0.25s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s ease, border-color 0.3s ease",
      }}
    >
      <span className="corner tl" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      <span className="corner tr" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      <span className="corner bl" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      <span className="corner br" style={{ opacity: isActive ? 0.9 : 0.5 }} />
      
      {isActive && character && (
        <div className="absolute top-1 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
          <svg
            width="20"
            height="12"
            viewBox="0 0 20 12"
            fill="none"
            className="animate-triangle-appear"
          >
            <polygon points="10,12 20,0 0,0" fill="#FFD780" />
          </svg>
        </div>
      )}
        
      {character ? (
        <>
          <div className="relative flex-1 overflow-hidden">
            <img src={character.imageUrl} alt={character.name}
              className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform"
              style={{ filter: "saturate(0.8) contrast(1.08) brightness(0.95)", transitionDuration: "500ms" }}
            />
            <div className="absolute inset-0" style={{ background: "linear-gradient(180deg,transparent 36%,rgba(8,9,26,0.96) 100%)" }} />
            <div className="absolute top-0 left-0 right-0 h-0.5" style={{ backgroundColor: clr, boxShadow: `0 0 5px ${clr}` }} />
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-400"
              style={{ background: `linear-gradient(120deg,transparent 30%,${clr}10 50%,transparent 70%)` }} />
            <div className="absolute top-2 left-2">
              <Stars n={character.rarity ?? 5} color={rarityColor(character.rarity)} />
            </div>
          </div>
          <div className="px-2 pt-1 pb-2 flex flex-col gap-1">
            <span style={{ fontFamily: "var(--font-heading)", fontSize: "12px",
              color: isActive ? "#f0d47a" : "#ede3c4", fontWeight: 600, letterSpacing: "0.04em",
              whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", transition: "color 0.3s" }}>
              {character.name}
            </span>
            <div className="flex items-center justify-between">
              <span style={{ fontFamily: "var(--font-heading)", fontSize: "9.5px", color: isActive ? "#f0d47a" : "#6a5820", letterSpacing: "0.06em", fontWeight: 500 }}>
                {character.level != null ? `Lv.${character.level}` : ""}
              </span>
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-2">
          <div className="absolute top-1.5 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
            <Stars n={5} color="#FFD780" />
          </div>
          <div style={{ width: 28, height: 28, borderRadius: "50%", border: "1px solid rgba(200,168,75,0.2)",
            display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(200,168,75,0.35)" strokeWidth="1.2">
              <circle cx="12" cy="8" r="4"/><path d="M4 22c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
            </svg>
          </div>
          <span style={{ fontFamily: "var(--font-heading)", fontSize: "9px", color: "rgba(200,168,75,0.3)", letterSpacing: "0.14em" }}>
            EMPTY
          </span>
        </div>
      )}
    </button>
  );
}