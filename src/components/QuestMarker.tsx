"use client";

import { useEffect, useRef, useState } from "react";
import CornerBracket from "@/components/brand/CornerBracket";

const SIDE: Record<string, "left" | "right"> = {
  Home: "left",
  Services: "right",
  Method: "left",
  Work: "right",
  Studio: "left",
  Start: "right",
};

// Manifesto shares data-quest="Services" with the triad section, so this
// stays a fixed lookup keyed by label rather than counting DOM sections —
// the total is 6 regardless of how many elements share a label.
const PROGRESS: Record<string, number> = {
  Home: 1,
  Services: 2,
  Method: 3,
  Work: 4,
  Studio: 5,
  Start: 6,
};
const PROGRESS_TOTAL = 6;

const LABEL_SWAP_MS = 260;

export default function QuestMarker() {
  const [active, setActive] = useState<string | null>(null);
  const [displayLabel, setDisplayLabel] = useState<string | null>(null);
  const [swapping, setSwapping] = useState(false);
  const [ready, setReady] = useState(false);
  const [lockKey, setLockKey] = useState(0);
  const ratios = useRef<Map<Element, number>>(new Map());
  const lastLabel = useRef<string | null>(null);
  const swapTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>("[data-quest]"));
    if (!els.length) return;

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          ratios.current.set(entry.target, entry.intersectionRatio);
        });
        let best: Element | null = null;
        let bestRatio = 0;
        ratios.current.forEach((ratio, el) => {
          if (ratio > bestRatio) {
            bestRatio = ratio;
            best = el;
          }
        });
        if (best && bestRatio > 0) {
          const label = (best as HTMLElement).dataset.quest as string;
          if (label !== lastLabel.current) {
            lastLabel.current = label;
            setActive(label);
            setLockKey((k) => k + 1);
          }
          setReady(true);
        }
      },
      { threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  // Crossfade the label text mid-move instead of snapping it, while the
  // outer marker (below) tweens position via its own CSS transition.
  useEffect(() => {
    if (active === null) return;
    if (displayLabel === null) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- first-ever lock-on has nothing to crossfade from; syncs the initial label into state
      setDisplayLabel(active);
      return;
    }
    if (active === displayLabel) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setDisplayLabel(active);
      return;
    }
    setSwapping(true);
    swapTimeout.current = setTimeout(() => {
      setDisplayLabel(active);
      setSwapping(false);
    }, LABEL_SWAP_MS);
    return () => {
      if (swapTimeout.current) clearTimeout(swapTimeout.current);
    };
  }, [active, displayLabel]);

  if (!active || !displayLabel) return null;
  const side = SIDE[active] ?? "left";
  const progress = PROGRESS[displayLabel] ?? 1;

  return (
    <div className="quest-marker-track" aria-hidden="true">
      {/* This node is never re-keyed across section changes: only its
          side-left/side-right class swaps, so the transform transition
          on .quest-marker actually animates the move instead of the whole
          element remounting at the new position. */}
      <div className={`quest-marker side-${side}${ready ? " is-ready" : ""}`}>
        <div key={lockKey} className="quest-marker-frame quest-lock">
          <CornerBracket className="corner tl" />
          <CornerBracket className="corner tr" />
          <CornerBracket className="corner br" />
          <CornerBracket className="corner bl" />
          <svg viewBox="0 0 100 100" className="quest-marker-chevron" aria-hidden="true">
            <path
              d="M42 36 L62 50 L42 64"
              fill="none"
              stroke="var(--color-violet)"
              strokeWidth={10}
              strokeLinecap="square"
              strokeLinejoin="miter"
            />
          </svg>
          <span className="quest-marker-dot" />
          <span className="quest-marker-ring" />
        </div>
        <span className={`quest-marker-label${swapping ? " is-swapping" : ""}`}>
          <span className="quest-marker-label-text">{displayLabel}</span>
          <span className="quest-marker-progress">
            {String(progress).padStart(2, "0")} / {String(PROGRESS_TOTAL).padStart(2, "0")}
          </span>
        </span>
      </div>
    </div>
  );
}
