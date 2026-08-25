"use client";

import { useEffect, useRef, useState } from "react";

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

// A quiet, always-visible odometer — deliberately NOT another reticle: no
// chevron, no corner brackets, no big label, so it reads as a distinct
// "how far through the page" readout rather than competing with the
// per-section QuestPin markers for attention.
export default function QuestProgress() {
  const [index, setIndex] = useState(1);
  const ratios = useRef<Map<Element, number>>(new Map());

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
          setIndex(PROGRESS[label] ?? 1);
        }
      },
      { threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <div className="quest-progress" aria-hidden="true">
      <div className="quest-progress-segs">
        {Array.from({ length: PROGRESS_TOTAL }, (_, i) => (
          <span key={i} className={`quest-progress-seg${i < index ? " is-filled" : ""}`} />
        ))}
      </div>
      <span className="quest-progress-count">
        {String(index).padStart(2, "0")} / {String(PROGRESS_TOTAL).padStart(2, "0")}
      </span>
    </div>
  );
}
