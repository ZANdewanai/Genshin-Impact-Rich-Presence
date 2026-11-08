import { useState, useEffect, useRef } from "react";
import type { Element } from "../types";
import { EL_COLOR, EL_LABEL, rarityColor } from "../constants";

export function ParticleField() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ borderRadius: 6 }}>
      {STATIC_PARTICLES.map(p => (
        <div key={p.id} className="particle" style={{
          left: p.left, top: p.top, width: p.size, height: p.size, borderRadius: "50%", position: "absolute",
          backgroundColor: p.gold ? `rgba(200,168,75,0.4)` : `rgba(140,160,220,0.25)`,
          ["--dur" as string]: p.dur, ["--delay" as string]: p.delay,
          boxShadow: p.gold ? `0 0 ${p.size * 3}px rgba(200,168,75,0.6)` : `0 0 ${p.size * 2}px rgba(140,160,220,0.4)`,
        }} />
      ))}
    </div>
  );
}

const STATIC_PARTICLES = Array.from({ length: 18 }, (_, i) => ({
  id: i, left: `${8 + (i * 5.1) % 84}%`, top: `${10 + (i * 4.7) % 80}%`,
  size: 1.5 + (i % 3) * 0.7,
  dur: `${5 + (i % 7)}s`, delay: `${-(i * 0.9)}s`,
  gold: i % 2 === 0,
}));