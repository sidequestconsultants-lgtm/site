"use client";

import { useEffect, useRef } from "react";

type Anchor = { name: string; side: "left" | "right" };

// Order must match the real DOM order of the [data-quest] sections below —
// only name + side are needed here now; each waypoint's actual position
// lives on the page (via <QuestWaypoint> inside its section) and is read
// live every frame, never cached.
const WAYPOINTS: Anchor[] = [
  { name: "Home", side: "left" },
  { name: "Services", side: "left" },
  { name: "POV", side: "left" },
  { name: "Method", side: "left" },
  { name: "Work", side: "left" },
  { name: "Studio", side: "left" },
  { name: "Start", side: "left" },
];
const TOTAL = WAYPOINTS.length;
const TRAIL_COUNT = 3;

function progressText(i: number) {
  return `${String(i + 1).padStart(2, "0")} / ${String(TOTAL).padStart(2, "0")}`;
}

function centerOf(el: HTMLElement): [number, number] {
  const r = el.getBoundingClientRect();
  return [r.left + r.width / 2, r.top + r.height / 2];
}

// ═══ quest dot ═══ waypoint reticles now live on the page (absolute,
// inside their own section) instead of floating at fixed viewport-%
// spots. This component just threads a single glowing dot + fading trail
// between them: every animation frame it re-reads each waypoint's live
// getBoundingClientRect() (never cached, since the page scrolls under
// them) and interpolates the dot — itself position:fixed, so its
// viewport-coordinate math lines up directly with the rects it reads —
// between the current pair by scroll progress.
export default function QuestDot() {
  const dotRef = useRef<HTMLDivElement>(null);
  const labelRef = useRef<HTMLDivElement>(null);
  const labelNameRef = useRef<HTMLDivElement>(null);
  const labelProgRef = useRef<HTMLDivElement>(null);
  const trailRefs = useRef<(HTMLDivElement | null)[]>([]);
  const mobileNameRef = useRef<HTMLSpanElement>(null);
  const mobileProgRef = useRef<HTMLSpanElement>(null);
  // Waypoints are page-anchored (they scroll with the page), so the dot's
  // on-screen motion doesn't reliably track scroll direction — a segment
  // transition, a resize, or just where a waypoint happens to sit can move
  // the dot opposite to how the page is actually scrolling. A trail built
  // from the dot's own position history inherits that same unreliability.
  // Base the trail on scroll direction itself instead, which is always
  // unambiguous.
  const lastYRef = useRef(0);
  const scrollDirRef = useRef(1);

  useEffect(() => {
    const sections = Array.from(document.querySelectorAll<HTMLElement>("[data-quest]"));
    if (sections.length !== TOTAL) return;
    const wps = sections.map((s) => s.querySelector<HTMLElement>(".wp"));
    if (wps.some((w) => !w)) return;

    lastYRef.current = window.scrollY;

    function update() {
      const probe = window.scrollY + 40;
      let i = 0;
      for (let k = 0; k < TOTAL; k++) {
        if (sections[k].offsetTop <= probe) i = k;
      }
      const j = Math.min(i + 1, TOTAL - 1);
      const span = sections[j].offsetTop - sections[i].offsetTop || 1;
      const p = i === j ? 0 : Math.min(1, Math.max(0, (probe - sections[i].offsetTop) / span));

      const [ax, ay] = centerOf(wps[i]!);
      const [bx, by] = centerOf(wps[j]!);
      const x = ax + (bx - ax) * p;
      const y = ay + (by - ay) * p;

      if (dotRef.current) {
        dotRef.current.style.left = `${x}px`;
        dotRef.current.style.top = `${y}px`;
      }

      wps.forEach((w, k) => {
        w?.classList.toggle("lit", k <= i);
      });

      const cur = WAYPOINTS[i];
      const [cx, cy] = centerOf(wps[i]!);
      if (labelRef.current) {
        labelRef.current.style.left = cur.side === "right" ? `${cx - 16}px` : `${cx + 22}px`;
        labelRef.current.style.top = `${cy}px`;
        labelRef.current.style.transform = `translateY(-50%)${cur.side === "right" ? " translateX(-100%)" : ""}`;
      }
      if (labelNameRef.current) labelNameRef.current.textContent = cur.name;
      if (labelProgRef.current) labelProgRef.current.textContent = progressText(i);
      if (mobileNameRef.current) mobileNameRef.current.textContent = cur.name;
      if (mobileProgRef.current) mobileProgRef.current.textContent = progressText(i);

      // Trail offset follows scroll direction, not the dot's own (possibly
      // opposite) on-screen drift: scrolling down puts the trail above the
      // dot, scrolling up puts it below, every frame, unambiguously.
      const sy = window.scrollY;
      scrollDirRef.current = sy > lastYRef.current ? 1 : sy < lastYRef.current ? -1 : scrollDirRef.current;
      lastYRef.current = sy;
      trailRefs.current.forEach((t, ti) => {
        const off = (ti + 1) * 12;
        if (t) {
          t.style.left = `${x}px`;
          t.style.top = `${y - scrollDirRef.current * off}px`;
          t.style.opacity = String(0.5 - ti * 0.14);
        }
      });
    }

    let raf = 0;
    const loop = () => {
      update();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("resize", update);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <>
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
          style={{ width: `${9 - i * 2}px`, height: `${9 - i * 2}px` }}
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
