import { generatePrism } from "@/lib/prism";

export default function Prism({ className }: { className?: string }) {
  const { facets, radialLines, crossLines, rings, outline, halo } = generatePrism();

  return (
    <div className={["relative", className].filter(Boolean).join(" ")}>
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
        <g className="prism-halo">
          {halo.map((points, i) => (
            <polygon
              key={`halo-${i}`}
              points={points}
              fill="none"
              stroke="#7B6CF0"
              strokeWidth={0.6}
              strokeOpacity={0.4}
            />
          ))}
        </g>
      </svg>
    </div>
  );
}
