"use client";

import { useEffect, useRef, useState } from "react";

// A per-section "pin on the map": the same reticle-lock visual the old
// fixed quest marker used (chevron, label chip, corner brackets, no
// status dot), but placed with position:absolute inside its own section
// instead of position:fixed on the viewport. It locks in (corner-draw +
// ping) once when scrolled into view, then scrolls away with the section
// like any other in-page element — no global position tracking needed.
export default function QuestPin({
  label,
  progress,
  total = 6,
  side,
  className,
}: {
  label: string;
  progress: number;
  total?: number;
  side: "left" | "right";
  className?: string;
}) {
  const [locked, setLocked] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setLocked(true);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`quest-pin side-${side}${locked ? " is-locked" : ""}${className ? ` ${className}` : ""}`}
      aria-hidden="true"
    >
      <div className={`ql-marker ql-${side}`}>
        <div className={`ql-reticle${locked ? " lock" : ""}`}>
          <span className="ql-corner tl" />
          <span className="ql-corner tr" />
          <span className="ql-corner bl" />
          <span className="ql-corner br" />
          <svg className="ql-chevron" viewBox="0 0 12 12" aria-hidden="true">
            <path
              d="M3 2 L9 6 L3 10"
              fill="none"
              stroke="#7B6CF0"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {locked && <span className="ql-ping go" />}
        </div>
        <div className="ql-tag">
          <span className="ql-name">{label}</span>
          <span className="ql-prog">
            {String(progress).padStart(2, "0")} / {String(total).padStart(2, "0")}
          </span>
        </div>
      </div>
    </div>
  );
}
