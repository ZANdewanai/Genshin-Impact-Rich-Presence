export type Element = "pyro" | "hydro" | "anemo" | "electro" | "cryo" | "geo" | "dendro" | "empty";
export type Tab = "presence" | "settings" | "logs" | "about";

export interface Character {
  id?: number;
  name: string;
  element: Element;
  level?: number;
  imageUrl: string;
  rarity?: number;
}

export interface Settings {
  username: string;
  mcAether: boolean;
  wandererName: string;
  manekinName: string;
  manekinaName: string;
}

export interface BackendState {
  running: boolean;
  location: string;
  activity: string;
  timestamp: number | null;
  party: (Character | null)[];
  active_character_index: number;
}

export interface DebugConfig {
  debugMode: boolean;
  debugCharacterMode: boolean;
  debugStaticImage: boolean;
  debugStaticImagePath: string;
}