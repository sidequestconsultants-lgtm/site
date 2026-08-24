"use client";

import { useEffect, useRef, useState } from "react";

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

const LABEL_SWAP_MS = 220;

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
        <div className={`ql-marker ql-${side}`}>
          {/* Re-keyed on every relock to replay the corner-draw + ping,
              same trick as the outer marker avoids: this is an inner node,
              so remounting it doesn't touch the position tween above. */}
          <div key={lockKey} className="ql-reticle lock">
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
            <span className="ql-ping go" />
          </div>
          <div className="ql-tag">
            <span className={`ql-name${swapping ? " swap" : ""}`}>{displayLabel}</span>
            <span className="ql-prog">
              {String(progress).padStart(2, "0")} / {String(PROGRESS_TOTAL).padStart(2, "0")}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
