"use client";

import { useEffect, useRef } from "react";

type Anchor = { name: string; x: number; y: number; side: "left" | "right" };

// Hand-placed viewport-% anchor spots, strictly alternating sides in
// section order with descending heights — this array's order must match
// the real DOM order of the [data-quest] sections below.
const WAYPOINTS: Anchor[] = [
  { name: "Home", x: 12, y: 16, side: "left" },
  { name: "Services", x: 88, y: 27, side: "right" },
  { name: "POV", x: 13, y: 38, side: "left" },
  { name: "Method", x: 87, y: 49, side: "right" },
  { name: "Work", x: 15, y: 60, side: "left" },
  { name: "Studio", x: 86, y: 71, side: "right" },
  { name: "Start", x: 12, y: 84, side: "left" },
];
const TOTAL = WAYPOINTS.length;
const TRAIL_COUNT = 3;

function progressText(i: number) {
  return `${String(i + 1).padStart(2, "0")} / ${String(TOTAL).padStart(2, "0")}`;
}

// ═══ quest dot + waypoints (lifted as-is from the provided reference
// component) ═══ 7 fixed reticle waypoints that never reposition; one
// glowing dot with a short fading trail threads them in DOM order as the
// page scrolls, interpolating between the two anchors the current scroll
// position sits between. Direct style mutation via refs (not React state)
// on every scroll frame, matching the reference's approach — this needs
// to update at native scroll speed, not through a render cycle.
export default function QuestDot() {
  const dotRef = useRef<HTMLDivElement>(null);
  const labelRef = useRef<HTMLDivElement>(null);
  const labelNameRef = useRef<HTMLDivElement>(null);
  const labelProgRef = useRef<HTMLDivElement>(null);
  const wpRefs = useRef<(HTMLDivElement | null)[]>([]);
  const trailRefs = useRef<(HTMLDivElement | null)[]>([]);
  const mobileNameRef = useRef<HTMLSpanElement>(null);
  const mobileProgRef = useRef<HTMLSpanElement>(null);
  const histRef = useRef<Array<[number, number]>>([]);

  useEffect(() => {
    const sections = Array.from(document.querySelectorAll<HTMLElement>("[data-quest]"));
    // The waypoint chain assumes exactly one section per waypoint, in the
    // same order — if that ever drifts out of sync, sit this out rather
    // than threading the dot through the wrong anchors.
    if (sections.length !== TOTAL) return;

    // The trail reads history entries several steps back (index 3, 6, 9),
    // so on the very first frame — before scrolling has appended enough
    // history — those reads are undefined and the trail dots are left
    // with no left/top ever applied, showing at their default (0,0)
    // static-flow position instead of near the dot. Pre-seed history with
    // the starting position so the trail sits on the dot from first paint.
    histRef.current = Array.from({ length: 12 }, () => [
      WAYPOINTS[0].x * (window.innerWidth / 100),
      WAYPOINTS[0].y * (window.innerHeight / 100),
    ]);

    function update() {
      const probe = window.scrollY + 40;
      let i = 0;
      for (let k = 0; k < TOTAL; k++) {
        if (sections[k].offsetTop <= probe) i = k;
      }
      const j = Math.min(i + 1, TOTAL - 1);
      const span = sections[j].offsetTop - sections[i].offsetTop || 1;
      const p = i === j ? 0 : Math.min(1, Math.max(0, (probe - sections[i].offsetTop) / span));

      const vw = window.innerWidth / 100;
      const vh = window.innerHeight / 100;
      const a = WAYPOINTS[i];
      const b = WAYPOINTS[j];
      const x = (a.x + (b.x - a.x) * p) * vw;
      const y = (a.y + (b.y - a.y) * p) * vh;

      if (dotRef.current) {
        dotRef.current.style.left = `${x}px`;
        dotRef.current.style.top = `${y}px`;
      }

      wpRefs.current.forEach((w, k) => w?.classList.toggle("lit", k <= i));

      const cur = WAYPOINTS[i];
      if (labelRef.current) {
        labelRef.current.style.left = cur.side === "right" ? `${cur.x * vw - 16}px` : `${cur.x * vw + 22}px`;
        labelRef.current.style.top = `${cur.y * vh}px`;
        labelRef.current.style.transform = `translateY(-50%)${cur.side === "right" ? " translateX(-100%)" : ""}`;
      }
      if (labelNameRef.current) labelNameRef.current.textContent = cur.name;
      if (labelProgRef.current) labelProgRef.current.textContent = progressText(i);
      if (mobileNameRef.current) mobileNameRef.current.textContent = cur.name;
      if (mobileProgRef.current) mobileProgRef.current.textContent = progressText(i);

      histRef.current.unshift([x, y]);
      histRef.current = histRef.current.slice(0, 12);
      trailRefs.current.forEach((t, ti) => {
        const h = histRef.current[(ti + 1) * 3];
        if (t && h) {
          t.style.left = `${h[0]}px`;
          t.style.top = `${h[1]}px`;
          t.style.opacity = String(0.42 - ti * 0.12);
        }
      });
    }

    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(update);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", update);
    update();
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", update);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <>
      {WAYPOINTS.map((w, i) => (
        <div
          key={w.name}
          ref={(el) => {
            wpRefs.current[i] = el;
          }}
          className="wp"
          style={{ left: `${w.x}vw`, top: `${w.y}vh` }}
          aria-hidden="true"
        >
          <span className="corner tl" />
          <span className="corner tr" />
          <span className="corner bl" />
          <span className="corner br" />
          <svg className="chev" viewBox="0 0 12 12" aria-hidden="true">
            <path
              d="M3 2 L9 6 L3 10"
              fill="none"
              stroke="#7B6CF0"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              transform={w.side === "right" ? "translate(12,0) scale(-1,1)" : undefined}
            />
          </svg>
        </div>
      ))}
      <div id="quest-label" ref={labelRef} aria-hidden="true">
        <div className="nm" ref={labelNameRef}>
          Home
        </div>
        <div className="pr" ref={labelProgRef}>
          {progressText(0)}
        </div>
      </div>
      <div id="quest-dot" ref={dotRef} aria-hidden="true" />
      {Array.from({ length: TRAIL_COUNT }, (_, i) => (
        <div
          key={i}
          className="quest-trail"
          ref={(el) => {
            trailRefs.current[i] = el;
          }}
          aria-hidden="true"
        />
      ))}
      <div className="quest-mobile" aria-hidden="true">
        <span className="nm" ref={mobileNameRef}>
          Home
        </span>
        <span className="pr" ref={mobileProgRef}>
          {progressText(0)}
        </span>
      </div>
    </>
  );
}
