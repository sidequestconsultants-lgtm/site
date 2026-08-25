"use client";

import { useEffect, useRef, useState } from "react";

type Anchor = { side: "left" | "right"; xPct: number; yPct: number };

// Hand-placed per-section fixed spots (viewport %), each in that section's
// open gutter space, off the centered 1200px content column. The marker
// glides between these only at active-section transitions — never bound
// to scroll position.
const ANCHORS: Record<string, Anchor> = {
  Home: { side: "left", xPct: 15, yPct: 42 },
  Services: { side: "right", xPct: 15, yPct: 30 },
  Method: { side: "left", xPct: 13, yPct: 60 },
  Work: { side: "right", xPct: 14, yPct: 38 },
  Studio: { side: "left", xPct: 16, yPct: 55 },
  Start: { side: "right", xPct: 15, yPct: 45 },
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
  const markerRef = useRef<HTMLDivElement>(null);

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

  // Binds the marker's fixed-position anchor to the active section rather
  // than scroll position: recomputed only when the active section changes
  // (plus on resize, so a stale px reading doesn't survive a viewport
  // resize) and applied as CSS custom properties that .quest-marker's
  // transform composes — the transform transition then does the gliding.
  useEffect(() => {
    if (!active) return;
    const anchor = ANCHORS[active];
    const el = markerRef.current;
    // On the render where `active` first flips from null, the marker
    // hasn't mounted yet (displayLabel still lags a render behind, so the
    // component still returns null that pass) — markerRef.current is null
    // and this effect would otherwise never get another chance to run
    // once it does mount, since `active` alone doesn't change again.
    // Depending on displayLabel too guarantees a rerun right after mount.
    if (!anchor || !el) return;
    const CONTENT_GAP = 12;
    const apply = () => {
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      let xPx = anchor.side === "left" ? vw * (anchor.xPct / 100) : vw * (1 - anchor.xPct / 100);
      const yPx = vh * (anchor.yPct / 100);
      // The 1200px content column's side margins shrink much faster than
      // a fixed viewport percentage as the viewport narrows (they vanish
      // entirely below 1200px), so a hand-placed percentage that clears
      // the column at a wide viewport can land ON it at a laptop width.
      // Clamp against the column's real edge (measured live, rather than
      // duplicating its width/padding math here) so the marker — which
      // hangs away from center from this anchor point — never drifts
      // onto content, at the cost of sitting closer to the column on
      // narrower screens than the hand-placed percentage intended.
      const container = document.querySelector<HTMLElement>(".max-w-\\[1200px\\]");
      if (container) {
        const rect = container.getBoundingClientRect();
        xPx =
          anchor.side === "left"
            ? Math.min(xPx, rect.left - CONTENT_GAP)
            : Math.max(xPx, rect.right + CONTENT_GAP);
      }
      el.style.setProperty("--qm-edge", "0px");
      el.style.setProperty("--qm-x", `${xPx}px`);
      el.style.setProperty("--qm-y", `${yPx}px`);
      // Below roughly 1400px the margin the content clamp above just
      // pinned the marker against can be narrower than the marker itself
      // (the column's margin shrinks to nothing as the viewport
      // approaches 1200px, while the marker's own width doesn't), which
      // pushes it half off the edge of the screen. Re-measure and nudge
      // it back on-screen — same "measure the real box, correct with a
      // composed transform" approach as the triad pop panels' --clamp-x —
      // but computed from xPx + the marker's width rather than read off
      // getBoundingClientRect().left/right directly: those are mid-flight
      // through the position transform's own transition at this exact
      // instant (freshly changed this tick) and would report yesterday's
      // position, not the target. Width isn't animated by a translate-only
      // transform, so it's safe to read directly and derive the rest.
      const edgeGap = 12;
      const width = el.getBoundingClientRect().width;
      const left = anchor.side === "left" ? xPx - width : xPx;
      const right = anchor.side === "left" ? xPx : xPx + width;
      let edge = 0;
      if (left < edgeGap) edge = edgeGap - left;
      else if (right > vw - edgeGap) edge = vw - edgeGap - right;
      if (edge !== 0) el.style.setProperty("--qm-edge", `${edge}px`);
    };
    apply();
    window.addEventListener("resize", apply);
    return () => window.removeEventListener("resize", apply);
  }, [active, displayLabel]);

  if (!active || !displayLabel) return null;
  const side = ANCHORS[active]?.side ?? "left";
  const progress = PROGRESS[displayLabel] ?? 1;

  return (
    // Never re-keyed across section changes: only its side-left/side-right
    // class and --qm-x/--qm-y custom properties change, so the transform
    // transition actually animates the move instead of the whole element
    // remounting at the new position.
    <div
      ref={markerRef}
      className={`quest-marker side-${side}${ready ? " is-ready" : ""}`}
      aria-hidden="true"
    >
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
  );
}
