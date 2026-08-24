"use client";

import { useEffect, useRef } from "react";
import { generatePrism, generatePrismHalo } from "@/lib/prism";

export default function Prism({ className }: { className?: string }) {
  const { facets, radialLines, crossLines, rings, outline } = generatePrism();
  const halo = generatePrismHalo();
  const stageRef = useRef<HTMLDivElement>(null);

  // Subtle cursor parallax on the whole stage — lifted as-is from the
  // provided prism component.
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const onMove = (e: MouseEvent) => {
      const dx = e.clientX / window.innerWidth - 0.5;
      const dy = e.clientY / window.innerHeight - 0.5;
      stage.style.transform = `translate(${dx * 14}px, ${dy * 14}px)`;
    };
    document.addEventListener("mousemove", onMove);
    return () => document.removeEventListener("mousemove", onMove);
  }, []);

  return (
    <div ref={stageRef} data-shard-anchor="prism" className={["prism-stage", className].filter(Boolean).join(" ")}>
      <div className="prism-glow" />
      <svg viewBox="0 0 400 400" role="img" aria-label="Luminous subdivided triangular prism, lit from within">
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
          {halo.map((s, i) => (
            <polygon key={i} points={s.points} fill="none" stroke="#7B6CF0" strokeWidth={0.6} strokeOpacity={0.4} />
          ))}
        </g>
      </svg>
    </div>
  );
}
