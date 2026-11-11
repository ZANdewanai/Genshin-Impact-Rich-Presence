export type Element =
  | "pyro" | "hydro" | "anemo" | "electro"
  | "cryo" | "geo" | "dendro" | "empty";

export type Tab = "presence" | "settings" | "logs" | "about";

export interface Character {
  name: string;
  element: Element;
  rarity?: number;
  level?: number;
  imageUrl: string;
}

export interface Settings {
  username: string;
  mcAether: boolean;
  wandererName: string;
  manekinName: string;
  manekinaName: string;
  useGpu: boolean;
}

export interface BackendState {
  running: boolean;
  location: string;
  activity: string;
  timestamp: number | null;
  party: (Character | null)[];
  active_character_index: number;
  discord_details?: string;
  discord_state?: string;
  discord_large_image?: string;
  discord_large_text?: string;
  discord_small_image?: string;
  discord_small_text?: string;
}

export interface DebugConfig {
  debugMode: boolean;
  debugCharacterMode: boolean;
  debugStaticImage: boolean;
  debugStaticImagePath: string;
}
