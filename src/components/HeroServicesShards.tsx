"use client";

import { useEffect, useRef } from "react";
import Shard from "@/components/brand/Shard";

// shard 1 -> Strategy/apex, shard 2 -> Social, shard 3 -> Software
const TARGETS = ["apex", "social", "software"] as const;

export default function HeroServicesShards() {
  const shardRefs = useRef<(HTMLDivElement | null)[]>([]);
  const rafRef = useRef<number | null>(null);
  const reduceMotionRef = useRef(false);

  useEffect(() => {
    reduceMotionRef.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function update() {
      rafRef.current = null;
      const prismEl = document.querySelector<HTMLElement>('[data-shard-anchor="prism"]');
      const homeEl = document.getElementById("home");
      const servicesEl = document.getElementById("services");
      if (!prismEl || !homeEl || !servicesEl) return;

      const prismRect = prismEl.getBoundingClientRect();
      const start = { x: prismRect.left + prismRect.width / 2, y: prismRect.top + prismRect.height / 2 };

      // Bound to scroll progress between the hero and services sections:
      // 0 at hero-in-view (top of page), 1 once services has reached the
      // top of the viewport. Reduced motion skips straight to 1 (pinned at
      // the boxes, no travel) but still recomputes live target positions
      // on resize so it stays correct across breakpoints.
      let progress = 1;
      if (!reduceMotionRef.current) {
        const heroTop = homeEl.offsetTop;
        const servicesTop = servicesEl.offsetTop;
        const span = Math.max(1, servicesTop - heroTop);
        progress = Math.min(1, Math.max(0, (window.scrollY - heroTop) / span));
      }

      TARGETS.forEach((target, i) => {
        const node = shardRefs.current[i];
        const targetEl = document.querySelector<HTMLElement>(`[data-shard-anchor="${target}"]`);
        if (!node || !targetEl) return;
        const r = targetEl.getBoundingClientRect();
        const end = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
        const x = start.x + (end.x - start.x) * progress;
        const y = start.y + (end.y - start.y) * progress;
        // Direct 1:1 binding to scroll position, no transition — the scroll
        // itself is the animation, not an eased follow.
        node.style.transform = `translate(${x}px, ${y}px)`;
        node.style.opacity = reduceMotionRef.current ? "0.35" : String(0.25 + progress * 0.3);
      });
    }

    function schedule() {
      if (rafRef.current !== null) return;
      rafRef.current = requestAnimationFrame(update);
    }

    update();
    if (!reduceMotionRef.current) {
      window.addEventListener("scroll", schedule, { passive: true });
    }
    window.addEventListener("resize", schedule);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <div className="scroll-shards" aria-hidden="true">
      {TARGETS.map((target, i) => (
        <div
          key={target}
          ref={(node) => {
            shardRefs.current[i] = node;
          }}
          className="scroll-shard"
        >
          <Shard className="h-full w-full" />
        </div>
      ))}
    </div>
  );
}
