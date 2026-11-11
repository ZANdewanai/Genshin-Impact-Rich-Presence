import type { BackendState } from "../types";
import { fmtElapsed } from "../api";
import { EL_COLOR, EL_LABEL } from "../constants";
import { CharacterCard } from "./CharacterCard";
import { Card } from "./ui";
import { BoltIcon, ClockIcon, DiscordIcon, ImageIcon, PinIcon, UserIcon } from "./Icons";

function Stat({ icon, label, value }: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <span className="mt-0.5 text-[var(--color-gold)] opacity-80">{icon}</span>
      <div className="min-w-0">
        <div className="field-label">{label}</div>
        <div className="mt-0.5 text-[15px] leading-snug text-[var(--color-text)] truncate">
          {value}
        </div>
      </div>
    </div>
  );
}

export function PresenceTab({ state, running, onToggle }: {
  state: BackendState | null;
  running: boolean;
  onToggle: () => void;
}) {
  if (!running) {
    return (
      <div className="card card-pad flex flex-col items-center gap-3 py-14 text-center">
        <span className="status-dot" />
        <p className="text-[15px] text-[var(--color-muted)] max-w-sm">
          The detection engine is stopped. Start it to read your party, location
          and activity from the game and publish them to Discord.
        </p>
        <button onClick={onToggle} className="apply-btn mt-1">Start engine</button>
      </div>
    );
  }

  const party = state?.party ?? [];
  const slots = Array.from({ length: 5 }, (_, i) => party[i] ?? null);
  const activeIndex = state?.active_character_index ?? -1;
  const activeChar = activeIndex >= 0 ? slots[activeIndex] : null;
  const activeEl = activeChar?.element ?? "empty";

  const location = state?.location && state.location !== "Unknown" ? state.location : "—";
  const activity = state?.activity && state.activity !== "None" ? state.activity : "—";
  const elapsed = fmtElapsed(state?.timestamp);

  const hasAssets = !!(
    state?.discord_large_image || state?.discord_small_image ||
    state?.discord_large_text || state?.discord_small_text
  );

  return (
    <div className="flex flex-col gap-4">
      {/* What the engine currently sees */}
      <Card title="Detection">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 lg:divide-x divide-[var(--color-line)]">
          <Stat icon={<PinIcon size={15} />} label="Location" value={location} />
          <Stat icon={<BoltIcon size={15} />} label="Activity" value={activity} />
          <Stat icon={<ClockIcon size={15} />} label="Session" value={elapsed} />
          <Stat
            icon={<UserIcon size={15} />}
            label="Active character"
            value={activeChar ? `${activeChar.name} · ${EL_LABEL[activeEl]}` : "—"}
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 items-start">
        {/* Party as read from the party screen */}
        <Card
          title="Party"
          className="lg:col-span-3"
          actions={
            activeChar ? (
              <span className="text-[11px] font-heading tracking-wider uppercase"
                style={{ color: EL_COLOR[activeEl] }}>
                {EL_LABEL[activeEl]}
              </span>
            ) : undefined
          }
        >
          <div className="card-pad grid grid-cols-3 sm:grid-cols-5 gap-3">
            {slots.map((char, i) => (
              <CharacterCard key={i} character={char} active={activeIndex === i} />
            ))}
          </div>
        </Card>

        {/* Exactly what gets sent to Discord RPC */}
        <Card title="Discord presence" className="lg:col-span-2">
          <div className="card-pad flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <DiscordIcon size={22} />
              <div className="min-w-0">
                <div className="text-[13px] font-medium text-[#c9cdf0]">Genshin Impact</div>
                <div className="text-[12px] text-[var(--color-faint)]">Rich Presence</div>
              </div>
            </div>

            <div className="rounded-lg border border-[var(--color-line)] bg-black/30 px-3 py-2.5 flex flex-col gap-1">
              <div className="text-[13px] text-[#e6e6f0]">
                {state?.discord_details || "Waiting for game data..."}
              </div>
              <div className="text-[12px] text-[#9aa0b8]">
                {state?.discord_state || activity}
              </div>
            </div>

            {hasAssets && (
              <div className="flex flex-col gap-1.5 text-[11px] font-mono text-[var(--color-muted)]">
                {state?.discord_large_image && (
                  <AssetRow label="large" image={state.discord_large_image} text={state.discord_large_text} />
                )}
                {state?.discord_small_image && (
                  <AssetRow label="small" image={state.discord_small_image} text={state.discord_small_text} />
                )}
              </div>
            )}

            <p className="text-[11.5px] leading-snug text-[var(--color-faint)]">
              This is the payload the engine pushes to Discord every update.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}

function AssetRow({ label, image, text }: {
  label: string;
  image: string;
  text?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <ImageIcon size={12} className="shrink-0 opacity-60" />
      <span className="text-[var(--color-faint)] w-10 shrink-0">{label}</span>
      <span className="truncate">{image}</span>
      {text && <span className="truncate text-[var(--color-faint)]">“{text}”</span>}
    </div>
  );
}
