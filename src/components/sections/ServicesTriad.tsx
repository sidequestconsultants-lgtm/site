"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import RevealOnScroll from "@/components/RevealOnScroll";
import TessellationField from "@/components/brand/TessellationField";
import Container from "@/components/Container";
import { services, type ServiceSlug } from "@/data/services";

const tagColorClass = { dim: "text-dim", cyan: "text-cyan", violet: "text-violet" } as const;

function ServiceCard({ slug, delay }: { slug: ServiceSlug; delay: number }) {
  const s = services[slug];
  return (
    <RevealOnScroll delay={delay} className="h-full">
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
    </RevealOnScroll>
  );
}

export default function ServicesTriad() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const lineRef = useRef<SVGPolygonElement>(null);
  const [drawn, setDrawn] = useState(false);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing a client-only capability check (matchMedia) into state; cannot be derived during render or SSR
      setDrawn(true);
      return;
    }
    const line = lineRef.current;
    const el = wrapRef.current;
    if (!line || !el) return;

    const len = line.getTotalLength();
    line.style.strokeDasharray = String(len);
    line.style.strokeDashoffset = String(len);

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            io.unobserve(entry.target);
            requestAnimationFrame(() => {
              line.style.strokeDashoffset = "0";
              setDrawn(true);
            });
          }
        });
      },
      { threshold: 0.3 },
    );
    io.observe(el);
    return () => io.disconnect();
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
          <svg
            className={`triad-bg pointer-events-none absolute inset-0 z-0 h-full w-full${drawn ? " is-drawn" : ""}`}
            viewBox="0 0 600 420"
            preserveAspectRatio="none"
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
              points="300,10 30,410 570,410"
              fill="none"
              stroke="url(#triad-line-grad)"
              strokeWidth="1.5"
              strokeOpacity="0.4"
              filter="url(#triad-line-glow)"
            />
            <polygon
              ref={lineRef}
              className="triad-line"
              points="300,10 30,410 570,410"
              fill="none"
              stroke="url(#triad-line-grad)"
              strokeWidth="1"
              strokeOpacity="0.55"
              strokeLinejoin="round"
            />
          </svg>

          <div className="relative z-10 flex flex-col items-center gap-6">
            <div className="w-full max-w-[440px]">
              <ServiceCard slug="strategy" delay={0} />
            </div>
            <div className="grid w-full gap-6 sm:grid-cols-2">
              <ServiceCard slug="social" delay={0.08} />
              <ServiceCard slug="software" delay={0.16} />
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
