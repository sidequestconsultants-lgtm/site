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

export default function QuestMarker() {
  const [active, setActive] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [lockKey, setLockKey] = useState(0);
  const ratios = useRef<Map<Element, number>>(new Map());
  const lastLabel = useRef<string | null>(null);

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

  if (!active) return null;
  const side = SIDE[active] ?? "left";

  return (
    <div className="quest-marker-track" aria-hidden="true">
      <div key={lockKey} className={`quest-marker quest-lock side-${side}${ready ? " is-ready" : ""}`}>
        <div className="quest-marker-frame">
          <CornerBracket className="corner tl" />
          <CornerBracket className="corner tr" />
          <CornerBracket className="corner br" />
          <CornerBracket className="corner bl" />
          <span className="quest-marker-dot" />
        </div>
        <span key={active} className="quest-marker-label">
          {active}
        </span>
      </div>
    </div>
  );
}
