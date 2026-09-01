"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import RevealOnScroll from "@/components/RevealOnScroll";
import Container from "@/components/Container";
import QuestWaypoint from "@/components/QuestWaypoint";

type FragAlign = "c" | "r" | "l";

// foreignObject content must declare the xhtml namespace on its root node;
// "xmlns" isn't a typed prop on HTMLDivElement, so it's spread via a plainly
// typed object to sidestep the excess-property check rather than "as any".
const XHTML_NS: Record<string, string> = { xmlns: "http://www.w3.org/1999/xhtml" };

type Fragment = {
  key: string;
  href: string;
  fragClass: "f0" | "f1" | "f2";
  driftClass: "d0" | "d1" | "d2";
  popClass: "p0" | "p1" | "p2";
  tag: string;
  titleLines: [string, string];
  align: FragAlign;
  shapePoints: string;
  edgePoints: string;
  fo: { x: number; y: number; w: number; h: number };
  copy: string;
};

// Exploded triangle fragments — geometry, copy, and positions lifted as-is
// from the locked design (OG prism proportions, viewBox 600x480).
const FRAGMENTS: Fragment[] = [
  {
    key: "strategy",
    href: "/strategy",
    fragClass: "f0",
    driftClass: "d0",
    popClass: "p0",
    tag: "// diagnose",
    titleLines: ["Strategy /", "Ops Audit"],
    align: "c",
    shapePoints: "300,30 200,232 300,288 400,232",
    edgePoints: "200,232 300,30 400,232",
    fo: { x: 176, y: 164, w: 248, h: 86 },
    copy: "Maps the manual grind and designs the AI-augmented system that routes work into the other two.",
  },
  {
    key: "social",
    href: "/social",
    fragClass: "f1",
    driftClass: "d1",
    popClass: "p1",
    tag: "// run",
    titleLines: ["AI Marketing /", "Retainers"],
    align: "r",
    shapePoints: "196,242 100,452 292,452 292,300",
    edgePoints: "196,242 100,452 292,452",
    fo: { x: 112, y: 342, w: 176, h: 86 },
    copy: "AI-run comms, content, creative, and paid — a full team's output, run lean.",
  },
  {
    key: "software",
    href: "/software",
    fragClass: "f2",
    driftClass: "d2",
    popClass: "p2",
    tag: "// build",
    titleLines: ["Custom AI /", "Software"],
    align: "l",
    shapePoints: "404,242 500,452 308,452 308,300",
    edgePoints: "404,242 500,452 308,452",
    fo: { x: 312, y: 342, w: 176, h: 86 },
    copy: "Bespoke AI software for the manual gaps no off-the-shelf product fills.",
  },
];

function MobileCard({ f }: { f: Fragment }) {
  return (
    <Link
      href={f.href}
      className="card-hover accent-violet group relative flex flex-col gap-3 overflow-hidden rounded-md border border-hairline bg-gradient-to-b from-surface to-[#0C0C16] p-6"
    >
      <div className="font-mono text-xs uppercase tracking-wide text-violet">{f.tag}</div>
      <div className="font-display text-lg font-bold uppercase leading-tight text-ink">
        {f.titleLines[0]}
        <br />
        {f.titleLines[1]}
      </div>
      <p className="text-sm leading-relaxed text-muted">{f.copy}</p>
      <span className="mt-auto font-mono text-xs text-cyan">Explore</span>
    </Link>
  );
}

export default function ServicesTriad() {
  const [hotIndex, setHotIndex] = useState<number | null>(null);
  const [revealed, setRevealed] = useState(false);
  // Unlike a plain reduced-motion flag (which only ever changes a class on
  // an otherwise-identical tree), isMobile picks between two structurally
  // different subtrees — SVG fragments vs. stacked cards. Reading
  // window.innerWidth in a lazy initializer would make the client's first
  // render disagree with the server-prerendered (always-desktop) HTML and
  // throw a hydration error, so this starts false unconditionally and only
  // flips client-side in the effect below, after hydration has committed.
  const [isMobile, setIsMobile] = useState(false);
  const triadRef = useRef<HTMLDivElement>(null);
  const popRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 619px)");
    const onChange = () => setIsMobile(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  // The pop panels are positioned via fixed percentages relative to the
  // triad (p1/p2 deliberately sit slightly past its left/right edge), which
  // is fine while the triad has room to spare but clips off-screen once it
  // sits close to a narrow viewport's edge. Nudge each pop back in view via
  // a --clamp-x custom property that composes into its existing transform
  // (see .pop/.p0/.pop.show in globals.css) — a margin-based nudge doesn't
  // work here since p2 is anchored with `right` and no `left`, so the
  // browser just recomputes its auto `left` to compensate and keeps the
  // right edge exactly where it was regardless of margin-left.
  useEffect(() => {
    if (isMobile) return;
    const clamp = () => {
      const margin = 16;
      // clientWidth (not window.innerWidth, which includes the scrollbar
      // gutter) is what actually bounds horizontal overflow.
      const viewportWidth = document.documentElement.clientWidth;
      popRefs.current.forEach((el) => {
        if (!el) return;
        el.style.setProperty("--clamp-x", "0px");
        const rect = el.getBoundingClientRect();
        let dx = 0;
        if (rect.right > viewportWidth - margin) dx = viewportWidth - margin - rect.right;
        else if (rect.left < margin) dx = margin - rect.left;
        if (dx !== 0) el.style.setProperty("--clamp-x", `${dx}px`);
      });
    };
    clamp();
    window.addEventListener("resize", clamp);
    return () => window.removeEventListener("resize", clamp);
  }, [isMobile]);

  useEffect(() => {
    if (isMobile) return;
    const el = triadRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setRevealed(true);
            io.disconnect();
          }
        });
      },
      { threshold: 0.3 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [isMobile]);

  return (
    <section id="services" data-quest="Services" className="section-rhythm relative snap-start border-t border-hairline">
      <QuestWaypoint side="left" />
      <Container>
        <RevealOnScroll className="mb-14 max-w-xl">
          <p className="text-[17px] leading-relaxed text-muted">
            Three services, one order. Strategy diagnoses the gaps — the apex that routes work
            into the other two.
          </p>
        </RevealOnScroll>

        {isMobile ? (
          <div className="flex flex-col gap-6">
            {FRAGMENTS.map((f) => (
              <MobileCard key={f.key} f={f} />
            ))}
          </div>
        ) : (
          <div ref={triadRef} className={`triad triad-reveal${revealed ? " is-in" : ""}`}>
            <svg viewBox="0 0 600 480" xmlns="http://www.w3.org/2000/svg" aria-label="Services as three exploded triangle fragments">
              {FRAGMENTS.map((f, i) => (
                <a key={f.key} href={f.href}>
                  <g
                    className={`frag ${f.fragClass}${hotIndex === i ? " hot" : ""}`}
                    data-i={i}
                    onMouseEnter={() => setHotIndex(i)}
                    onMouseLeave={() => setHotIndex((h) => (h === i ? null : h))}
                  >
                    <g className={f.driftClass}>
                      <g className="lift">
                        <polygon className="shape" points={f.shapePoints} />
                        <polyline className="edge" points={f.edgePoints} />
                        <foreignObject x={f.fo.x} y={f.fo.y} width={f.fo.w} height={f.fo.h}>
                          <div {...XHTML_NS} className={`fo ${f.align}`}>
                            <div className="tag">{f.tag}</div>
                            <div className="ttl">
                              {f.titleLines[0]}
                              <br />
                              {f.titleLines[1]}
                            </div>
                          </div>
                        </foreignObject>
                      </g>
                    </g>
                  </g>
                </a>
              ))}
            </svg>
            {FRAGMENTS.map((f, i) => (
              <div
                key={f.key}
                ref={(node) => {
                  popRefs.current[i] = node;
                }}
                className={`pop ${f.popClass}${hotIndex === i ? " show" : ""}`}
              >
                <div className="pt">{f.tag}</div>
                <p>{f.copy}</p>
                <Link href={f.href} className="go">
                  Explore
                </Link>
              </div>
            ))}
          </div>
        )}
      </Container>
    </section>
  );
}
