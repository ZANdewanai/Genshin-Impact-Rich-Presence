import type { Character } from "../types";
import { EL_COLOR, EL_LABEL, rarityColor } from "../constants";

function Stars({ n, color }: { n: number; color: string }) {
  return (
    <span className="flex gap-0.5">
      {Array.from({ length: n }).map((_, i) => (
        <svg key={i} width="8" height="8" viewBox="0 0 10 10" fill={color}>
          <polygon points="5,0.5 6.6,3.4 9.5,5 6.6,6.6 5,9.5 3.4,6.6 0.5,5 3.4,3.4" />
        </svg>
      ))}
    </span>
  );
}

export function CharacterCard({ character, active }: {
  character: Character | null;
  active: boolean;
}) {
  const el = character?.element ?? "empty";
  const elColor = EL_COLOR[el];

  return (
    <div
      className={`party-card el-${el} ${active ? "active" : ""}`}
      title={character ? `${character.name} · ${EL_LABEL[el]}` : "Empty slot"}
    >
      <div className="el-bar" />
      <div className="relative flex-1 min-h-0" style={{ aspectRatio: "3 / 4" }}>
        {character?.imageUrl ? (
          <img
            src={character.imageUrl}
            alt={character.name}
            className="absolute inset-0 w-full h-full object-cover object-top"
            style={{ filter: "saturate(0.85) contrast(1.05) brightness(0.95)" }}
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center"
            style={{ background: "linear-gradient(160deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01))" }}>
            <span className="font-heading text-[10px] font-semibold tracking-[0.18em] text-[var(--color-faint)]">
              {character ? EL_LABEL[el].toUpperCase() : "EMPTY"}
            </span>
          </div>
        )}
        <div className="absolute inset-0"
          style={{ background: "linear-gradient(180deg, transparent 55%, rgba(8,9,15,0.92) 100%)" }} />
        {character && (
          <div className="absolute top-1.5 left-1.5">
            <Stars n={character.rarity ?? 5} color={rarityColor(character.rarity)} />
          </div>
        )}
        {active && character && (
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
            style={{ background: elColor, boxShadow: `0 0 6px ${elColor}` }} />
        )}
        <div className="absolute bottom-0 left-0 right-0 px-2 pb-1.5">
          <div className="font-heading text-[11px] font-semibold tracking-wide truncate"
            style={{ color: active ? "var(--color-gold-bright)" : "var(--color-text)" }}>
            {character?.name ?? "—"}
          </div>
          <div className="flex items-center justify-between mt-0.5">
            <span className="text-[10px] text-[var(--color-faint)] font-heading tracking-wider">
              {character?.level != null ? `Lv.${character.level}` : ""}
            </span>
            <span className="text-[9px] font-heading tracking-[0.14em] uppercase"
              style={{ color: elColor }}>
              {EL_LABEL[el]}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
