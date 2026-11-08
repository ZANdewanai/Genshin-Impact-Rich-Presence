import type { Element } from "./types";

export const EL_COLOR: Record<Element, string> = {
  pyro: "#ff6432", hydro: "#3298ff", anemo: "#5adcb4",
  electro: "#b464ff", cryo: "#8cc8ff", geo: "#c8a032",
  dendro: "#64d250", empty: "#4a4a5a",
};

export const EL_LABEL: Record<Element, string> = {
  pyro: "Pyro", hydro: "Hydro", anemo: "Anemo", electro: "Electro",
  cryo: "Cryo", geo: "Geo", dendro: "Dendro", empty: "—",
};

export const RARITY_5 = "#FFD780";
export const RARITY_4 = "#B48AE6";

export const rarityColor = (rarity?: number): string =>
  rarity === 5 ? RARITY_5 : rarity === 4 ? RARITY_4 : RARITY_5;

export const LOCATIONS = [
  "Mondstadt — City of Freedom", "Liyue Harbor — Port of Commerce",
  "Inazuma — Electro Archon's Domain", "Sumeru — City of Wisdom",
  "Fontaine — Nation of Justice", "Natlan — Nation of War",
  "Domain of Forsaken Ruins", "Golden Apple Archipelago",
];

export const ACTIVITIES = [
  "Exploring the open world", "Clearing Spiral Abyss",
  "Completing a Story Quest", "Grinding Resin in Domain",
  "Fighting World Boss", "In Co-Op Session",
  "Forging and Crafting", "Idle in Serenitea Pot",
];

export const STATIC_PARTICLES = Array.from({ length: 18 }, (_, i) => ({
  id: i, left: `${8 + (i * 5.1) % 84}%`, top: `${10 + (i * 4.7) % 80}%`,
  size: 1.5 + (i % 3) * 0.7,
  dur: `${5 + (i % 7)}s`, delay: `${-(i * 0.9)}s`,
  gold: i % 2 === 0,
}));

export const DEMO_STARTED_AT = Date.now() / 1000 - 83 * 60;