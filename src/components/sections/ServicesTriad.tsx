"use client";

import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";
import Link from "next/link";
import RevealOnScroll from "@/components/RevealOnScroll";
import TessellationField from "@/components/brand/TessellationField";
import Shard from "@/components/brand/Shard";
import Container from "@/components/Container";
import { services, type ServiceSlug } from "@/data/services";

const tagColorClass = { dim: "text-dim", cyan: "text-cyan", violet: "text-violet" } as const;

function ServiceCard({
  slug,
  cardRef,
  armed,
  delay,
}: {
  slug: ServiceSlug;
  cardRef: RefObject<HTMLDivElement | null>;
  armed: boolean;
  delay: number;
}) {
  const s = services[slug];
  return (
    <div ref={cardRef} className={`triad-card h-full${armed ? " is-in" : ""}`} style={{ transitionDelay: `${delay}s` }}>
      <Link
        href={`/${slug}`}
        className={`card-hover accent-${s.accent} group relative flex h-full flex-col gap-5 overflow-hidden rounded-md border border-hairline bg-gradient-to-b from-surface to-[#0C0C16] p-8`}
      >
        <TessellationField className="card-glow" masked size={50} />
        <div className="relative z-10 flex items-start justify-between gap-3">
          <div className="font-display text-lg font-bold uppercase leading-tight text-ink">
            {s.name}
          </div>
          <div className={`shrink-0 font-mono text-[11px] tracking-wide ${tagColorClass[s.tagColor]}`}>
            {s.tag}
          </div>
        </div>
        <p className="relative z-10 text-sm leading-relaxed text-muted">{s.tagline}</p>
        <span className="relative z-10 mt-auto font-mono text-xs text-ink opacity-80 transition-opacity group-hover:opacity-100">
          Explore <span className="text-violet">→</span>
        </span>
      </Link>
    </div>
  );
}

type Pt = { x: number; y: number };
type Geometry = { w: number; h: number; apex: Pt; baseLeft: Pt; baseRight: Pt };
type ShardTarget = "apex" | "left" | "right";
type ShardMode = "start" | "arm" | "arm-track" | "static";

// Fragments that arrive from above (as if shed from the hero prism) and
// resolve into the three card corners the triangle already connects.
// 2 per corner; one per lingering pair stays on as ambient texture instead
// of fading all the way out.
const TRIAD_SHARDS: { target: ShardTarget; ox: number; oy: number; rot: number; size: number; linger?: boolean }[] = [
  { target: "apex", ox: -26, oy: -8, rot: 14, size: 20 },
  { target: "apex", ox: 20, oy: 12, rot: -20, size: 16, linger: true },
  { target: "left", ox: -16, oy: -20, rot: 26, size: 18 },
  { target: "left", ox: 22, oy: 10, rot: -14, size: 15 },
  { target: "right", ox: -20, oy: 12, rot: 18, size: 17, linger: true },
  { target: "right", ox: 18, oy: -16, rot: -24, size: 14 },
];

const SHARD_SETTLE_MS = 1100;

function shardTargetPt(g: Geometry, target: ShardTarget): Pt {
  return target === "apex" ? g.apex : target === "left" ? g.baseLeft : g.baseRight;
}

export default function ServicesTriad() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const topRef = useRef<HTMLDivElement>(null);
  const leftRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);
  const shardRefs = useRef<(HTMLDivElement | null)[]>([]);
  const geoRef = useRef<Geometry | null>(null);
  const armedRef = useRef(false);
  const settleTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [geo, setGeo] = useState<Geometry | null>(null);
  const [drawn, setDrawn] = useState(false);
  const [armed, setArmed] = useState(false);

  function applyShardState(g: Geometry, mode: ShardMode) {
    TRIAD_SHARDS.forEach((cfg, i) => {
      const node = shardRefs.current[i];
      if (!node) return;
      const base = shardTargetPt(g, cfg.target);

      if (mode === "static") {
        if (!cfg.linger) {
          node.style.display = "none";
          return;
        }
        node.style.display = "";
        node.classList.remove("is-armed");
        node.style.transform = `translate(${base.x + cfg.ox}px, ${base.y + cfg.oy}px) rotate(${cfg.rot}deg)`;
        node.style.opacity = "0.18";
        return;
      }

      node.style.display = "";
      if (mode === "start") {
        node.classList.remove("is-armed");
        const startX = g.apex.x + (i - 2.5) * 22;
        const startY = -40 - (i % 3) * 12;
        node.style.transform = `translate(${startX}px, ${startY}px) rotate(${cfg.rot * 0.3}deg)`;
        node.style.opacity = "0";
      } else if (mode === "arm-track") {
        // Already armed; just keep the resolved position tracking the real
        // card corners across resizes without touching opacity mid-fade.
        node.style.transform = `translate(${base.x + cfg.ox}px, ${base.y + cfg.oy}px) rotate(${cfg.rot}deg)`;
      } else {
        node.classList.add("is-armed");
        node.style.transform = `translate(${base.x + cfg.ox}px, ${base.y + cfg.oy}px) rotate(${cfg.rot}deg)`;
        node.style.opacity = cfg.linger ? "0.5" : "0.55";
      }
    });
  }

  // Measure the real card boxes (layout-only, transform-independent) so the
  // triangle's apex/base points, and the shards resolving into them, always
  // land exactly on the card corners regardless of viewport width or the
  // cards' reveal-in translateY.
  useEffect(() => {
    const measure = () => {
      const wrap = wrapRef.current;
      const top = topRef.current;
      const left = leftRef.current;
      const right = rightRef.current;
      if (!wrap || !top || !left || !right) return;
      const next: Geometry = {
        w: wrap.offsetWidth,
        h: wrap.offsetHeight,
        apex: { x: top.offsetLeft + top.offsetWidth / 2, y: top.offsetTop + top.offsetHeight },
        baseLeft: { x: left.offsetLeft, y: left.offsetTop + left.offsetHeight },
        baseRight: { x: right.offsetLeft + right.offsetWidth, y: right.offsetTop + right.offsetHeight },
      };
      setGeo(next);
      geoRef.current = next;

      if (!armedRef.current) {
        applyShardState(next, "start");
        return;
      }
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const narrow = window.matchMedia("(max-width: 480px)").matches;
      applyShardState(next, reduceMotion || narrow ? "static" : "arm-track");
    };

    measure();
    const ro = new ResizeObserver(measure);
    if (wrapRef.current) ro.observe(wrapRef.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing a client-only capability check (matchMedia) into state; cannot be derived during render or SSR
      setDrawn(true);
      setArmed(true);
      armedRef.current = true;
      if (geoRef.current) applyShardState(geoRef.current, "static");
      return;
    }
    const el = wrapRef.current;
    if (!el) return;

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            io.unobserve(entry.target);
            requestAnimationFrame(() => {
              setDrawn(true);
              setArmed(true);
              armedRef.current = true;
              if (!geoRef.current) return;

              const narrow = window.matchMedia("(max-width: 480px)").matches;
              if (narrow) {
                applyShardState(geoRef.current, "static");
                return;
              }
              applyShardState(geoRef.current, "arm");
              settleTimeout.current = setTimeout(() => {
                TRIAD_SHARDS.forEach((cfg, i) => {
                  const node = shardRefs.current[i];
                  if (node) node.style.opacity = cfg.linger ? "0.18" : "0";
                });
              }, SHARD_SETTLE_MS);
            });
          }
        });
      },
      { threshold: 0.25 },
    );
    io.observe(el);
    return () => {
      io.disconnect();
      if (settleTimeout.current) clearTimeout(settleTimeout.current);
    };
  }, []);

  return (
    <section id="services" data-quest="Services" className="section-rhythm snap-start border-t border-hairline">
      <Container>
        <RevealOnScroll className="mb-14 max-w-xl">
          <p className="text-[17px] leading-relaxed text-muted">
            Three services, one order. Strategy diagnoses the gaps — the apex that routes work
            into the other two.
          </p>
        </RevealOnScroll>

        <div ref={wrapRef} className="relative mx-auto max-w-[940px]">
          {geo && (
            <svg
              className={`triad-bg pointer-events-none absolute inset-0 z-0 h-full w-full${drawn ? " is-drawn" : ""}`}
              viewBox={`0 0 ${geo.w} ${geo.h}`}
              aria-hidden="true"
            >
              <defs>
                <linearGradient id="triad-line-grad" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#7B6CF0" />
                  <stop offset="1" stopColor="#9DD3FF" />
                </linearGradient>
                <filter id="triad-line-glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="4" />
                </filter>
              </defs>
              <polygon
                className="triad-glow"
                points={`${geo.apex.x},${geo.apex.y} ${geo.baseLeft.x},${geo.baseLeft.y} ${geo.baseRight.x},${geo.baseRight.y}`}
                fill="none"
                stroke="url(#triad-line-grad)"
                strokeWidth="1.5"
                strokeOpacity="0.4"
                filter="url(#triad-line-glow)"
              />
              <polygon
                className="triad-line"
                pathLength={1}
                points={`${geo.apex.x},${geo.apex.y} ${geo.baseLeft.x},${geo.baseLeft.y} ${geo.baseRight.x},${geo.baseRight.y}`}
                fill="none"
                stroke="url(#triad-line-grad)"
                strokeWidth="1"
                strokeOpacity="0.55"
                strokeLinejoin="round"
              />
            </svg>
          )}

          {geo && (
            <div className="triad-shards pointer-events-none absolute inset-0 z-[5] overflow-hidden" aria-hidden="true">
              {TRIAD_SHARDS.map((cfg, i) => (
                <div
                  key={i}
                  ref={(node) => {
                    shardRefs.current[i] = node;
                  }}
                  className="triad-shard"
                  style={{ width: cfg.size, height: cfg.size }}
                >
                  <Shard className="h-full w-full" />
                </div>
              ))}
            </div>
          )}

          <div className="relative z-10 flex flex-col items-center gap-6">
            <div className="w-full max-w-[440px]">
              <ServiceCard slug="strategy" cardRef={topRef} armed={armed} delay={0.5} />
            </div>
            <div className="grid w-full gap-6 sm:grid-cols-2">
              <ServiceCard slug="social" cardRef={leftRef} armed={armed} delay={0.68} />
              <ServiceCard slug="software" cardRef={rightRef} armed={armed} delay={0.68} />
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
