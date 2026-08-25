"use client";

import { useEffect, useRef, useState } from "react";
import RevealOnScroll from "@/components/RevealOnScroll";
import CornerBracket from "@/components/brand/CornerBracket";
import Container from "@/components/Container";
import QuestPin from "@/components/QuestPin";

const steps = [
  { num: "01", tag: "Diagnose", micro: "// audit", detail: "The audit — map the grind, find the AI-shaped gaps." },
  { num: "02", tag: "Build", micro: "// build", detail: "The tools — bespoke software wired into your stack." },
  { num: "03", tag: "Run", micro: "// ship", detail: "The retainer — AI-run social, creative, and paid, shipped weekly." },
];

export default function Method({ showQuestPin = false }: { showQuestPin?: boolean }) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );

  useEffect(() => {
    if (active) return;
    const el = trackRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActive(true);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.35 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [active]);

  return (
    <section id="method-preview" data-quest="Method" className="section-rhythm relative snap-start border-t border-hairline">
      {showQuestPin && (
        <QuestPin label="Method" progress={3} side="left" className="left-4 top-6 hidden md:flex lg:left-10" />
      )}
      <Container>
        <RevealOnScroll className="mb-6 sm:mb-8">
          <h2 className="text-balance font-display text-[clamp(1.8rem,3.2vw,2.6rem)] font-bold uppercase leading-tight text-ink">
            The method.
          </h2>
        </RevealOnScroll>

        <div ref={trackRef} className={`method-track${active ? " is-active" : ""}`}>
          <div className="method-line-h" aria-hidden="true">
            <div className="fill" />
            <div className="rail-pulse" />
          </div>
          <div className="method-line-v" aria-hidden="true">
            <div className="fill" />
            <div className="rail-pulse" />
          </div>

          <div className="method-steps-row">
            {steps.map((step) => (
              <div key={step.num} className="method-node">
                <div className="method-node-badge">
                  <CornerBracket className="absolute left-0 top-0 h-4 w-4" />
                  <CornerBracket className="absolute right-0 top-0 h-4 w-4 rotate-90" />
                  <CornerBracket className="absolute bottom-0 right-0 h-4 w-4 rotate-180" />
                  <CornerBracket className="absolute bottom-0 left-0 h-4 w-4 -rotate-90" />
                  {step.num}
                  <span className="method-node-dot" />
                </div>
                <div>
                  <div className="method-node-label">{step.tag}</div>
                  <div className="method-node-micro mt-1">{step.micro}</div>
                  <p className="mt-2 max-w-[220px] text-sm leading-relaxed text-muted">{step.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Container>
    </section>
  );
}
