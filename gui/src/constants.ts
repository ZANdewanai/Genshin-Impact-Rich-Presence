import type { Element } from "./types";

export const EL_COLOR: Record<Element, string> = {
  pyro: "#ff7a59",
  hydro: "#5aa9ff",
  anemo: "#6fe3c1",
  electro: "#b97bff",
  cryo: "#9fd4ff",
  geo: "#e0b95c",
  dendro: "#7ed957",
  empty: "#565b70",
};

export const EL_LABEL: Record<Element, string> = {
  pyro: "Pyro",
  hydro: "Hydro",
  anemo: "Anemo",
  electro: "Electro",
  cryo: "Cryo",
  geo: "Geo",
  dendro: "Dendro",
  empty: "—",
};

export const rarityColor = (rarity?: number): string =>
  rarity === 4 ? "#b48ae6" : "#ffd780";
