import type { HTMLAttributes, SVGProps } from "react";

interface IconProps extends SVGProps<SVGSVGElement> {
  size?: number;
  color?: string;
}

export function LocationIcon({ size = 14, color = "currentColor", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" {...props}>
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
      <circle cx="12" cy="9" r="2.5"/>
    </svg>
  );
}

export function StateIcon({ size = 14, color = "currentColor", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" {...props}>
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  );
}

export function TimeIcon({ size = 14, color = "currentColor", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" {...props}>
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  );
}

export function AssetIcon({ size = 14, color = "currentColor", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" {...props}>
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
      <circle cx="8.5" cy="8.5" r="1.5"/>
      <polyline points="21 15 16 10 5 21"/>
    </svg>
  );
}

export function DiscordIcon({ size = 17, color = "#7289da", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={color} {...props}>
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057.101 18.079.11 18.1.127 18.114a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
    </svg>
  );
}

export function GenshinLogo({ size = 20, ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...props}>
      <polygon points="12,1 16,8 23,12 16,16 12,23 8,16 1,12 8,8" fill="#c8a84b" opacity="0.95"/>
    </svg>
  );
}

export function TriangleIcon({ size = 20, color = "#FFD780", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 12" fill="none" {...props}>
      <polygon points="10,12 20,0 0,0" fill={color} />
    </svg>
  );
}

export function StarIcon({ size = 9, color = "#FFD780", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 10 10" fill={color} {...props}>
      <polygon points="5,0.5 6.6,3.4 9.5,5 6.6,6.6 5,9.5 3.4,6.6 0.5,5 3.4,3.4"/>
    </svg>
  );
}

export function EmptySlotIcon({ size = 14, color = "rgba(200,168,75,0.35)", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.2" {...props}>
      <circle cx="12" cy="8" r="4"/>
      <path d="M4 22c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
    </svg>
  );
}

interface GoldStarsProps extends HTMLAttributes<HTMLSpanElement> {
  count?: number;
  color?: string;
  size?: number;
}

export function GoldStars({ count = 5, color = "#FFD780", size = 9, ...props }: GoldStarsProps) {
  return (
    <span className="flex gap-0.5" {...props}>
      {Array.from({ length: count }).map((_, i) => (
        <StarIcon key={i} size={size} color={color} />
      ))}
    </span>
  );
}

export function ChevronIcon({ size = 12, color = "currentColor", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" {...props}>
      <polyline points="9 18 15 12 9 6"/>
    </svg>
  );
}

export function CopyIcon({ size = 14, color = "currentColor", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" {...props}>
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  );
}

export function ExternalLinkIcon({ size = 13, color = "#c8a84b", ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" {...props}>
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
      <polyline points="15 3 21 3 21 9"/>
      <line x1="10" y1="14" x2="21" y2="3"/>
    </svg>
  );
}