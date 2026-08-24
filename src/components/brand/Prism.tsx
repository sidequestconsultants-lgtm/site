import type { CSSProperties } from "react";
import { generatePrism } from "@/lib/prism";
import Shard from "@/components/brand/Shard";

// Ambient shard fragments drifting around the prism. Positions are
// percentages of the prism box; --rot/--dx/--dy feed the shared
// shard-drift keyframe so each shard gets its own base rotation and
// drift amplitude without fighting the animation's transform.
const FLOATIES: { top: string; left: string; size: number; rot: number; dx: number; dy: number; opacity: number; dur: number; delay: number }[] = [
  { top: "-6%", left: "66%", size: 22, rot: 12, dx: 7, dy: -9, opacity: 0.4, dur: 16, delay: 0 },
  { top: "10%", left: "-9%", size: 15, rot: -20, dx: -6, dy: 8, opacity: 0.3, dur: 20, delay: 2 },
  { top: "80%", left: "84%", size: 18, rot: 28, dx: 8, dy: 6, opacity: 0.34, dur: 18, delay: 1 },
  { top: "90%", left: "8%", size: 13, rot: -10, dx: -5, dy: -6, opacity: 0.26, dur: 22, delay: 3 },
  { top: "42%", left: "98%", size: 19, rot: 46, dx: 6, dy: 7, opacity: 0.3, dur: 17, delay: 1.5 },
  { top: "-3%", left: "18%", size: 14, rot: -32, dx: -7, dy: 5, opacity: 0.24, dur: 19, delay: 2.5 },
];

export default function Prism({ className }: { className?: string }) {
  const { facets, radialLines, crossLines, rings, outline } = generatePrism();

  return (
    <div className={["relative", className].filter(Boolean).join(" ")}>
      <div className="prism-shards pointer-events-none absolute inset-0" aria-hidden="true">
        {FLOATIES.map((s, i) => (
          <Shard
            key={i}
            className="prism-shard"
            style={
              {
                top: s.top,
                left: s.left,
                width: s.size,
                height: s.size,
                opacity: s.opacity,
                "--rot": `${s.rot}deg`,
                "--dx": `${s.dx}px`,
                "--dy": `${s.dy}px`,
                animationDuration: `${s.dur}s`,
                animationDelay: `${s.delay}s`,
              } as CSSProperties
            }
          />
        ))}
      </div>
      <div className="prism-glow pointer-events-none absolute left-1/2 top-1/2 h-[58%] w-[58%] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[22px]"
        style={{
          background:
            "radial-gradient(circle, rgba(157,211,255,.5), rgba(123,108,240,.22) 40%, transparent 68%)",
        }}
      />
      <svg viewBox="0 0 400 400" className="relative z-10 h-auto w-full overflow-visible">
        {facets.map((f, i) => (
          <polygon
            key={i}
            points={f.points}
            fill={f.fill}
            fillOpacity={f.opacity}
            className={f.shimmer ? "prism-shimmer" : undefined}
            style={f.shimmer ? { animationDelay: `${f.delay}s` } : undefined}
          />
        ))}
        {radialLines.map((l, i) => (
          <line
            key={`rl-${i}`}
            x1={l.x1}
            y1={l.y1}
            x2={l.x2}
            y2={l.y2}
            stroke="#8794F0"
            strokeWidth={0.5}
            strokeOpacity={l.opacity}
          />
        ))}
        {crossLines.map((l, i) => (
          <line
            key={`cl-${i}`}
            x1={l.x1}
            y1={l.y1}
            x2={l.x2}
            y2={l.y2}
            stroke="#8794F0"
            strokeWidth={0.5}
            strokeOpacity={l.opacity}
          />
        ))}
        {rings.map((r, i) => (
          <polygon
            key={`ring-${i}`}
            points={r.points}
            fill="none"
            stroke="#CFE6FF"
            strokeWidth={0.7}
            strokeOpacity={r.opacity}
          />
        ))}
        <polygon
          points={outline}
          fill="none"
          stroke="#BFE0FF"
          strokeWidth={1.4}
          strokeOpacity={0.9}
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
