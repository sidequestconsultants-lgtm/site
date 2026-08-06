"use client";

import { useState } from "react";
import Link from "next/link";
import Prism from "@/components/brand/Prism";
import Button from "@/components/ui/Button";
import Container from "@/components/Container";
import { serviceOrder, services, type ServiceSlug } from "@/data/services";

const modeLabels: Record<ServiceSlug, string> = {
  strategy: "Strategy",
  social: "Social",
  software: "Software",
};

export default function Hero() {
  const [mode, setMode] = useState<ServiceSlug>("strategy");
  const active = services[mode];

  return (
    <section className="relative overflow-hidden pb-[clamp(64px,8vw,96px)] pt-12">
      <Container className="flex flex-col gap-10">
        <div className="flex w-fit gap-1 rounded-full border border-hairline p-1" role="tablist" aria-label="Choose a service to preview">
          {serviceOrder.map((slug) => (
            <button
              key={slug}
              role="tab"
              aria-selected={mode === slug}
              onClick={() => setMode(slug)}
              className={[
                "rounded-full px-4 py-2 font-mono text-xs uppercase tracking-wide transition-colors sm:px-5",
                mode === slug ? "bg-surface text-ink" : "text-dim hover:text-muted",
              ].join(" ")}
            >
              {modeLabels[slug]}
            </button>
          ))}
        </div>

        <div className="grid items-center gap-[clamp(32px,5vw,64px)] md:grid-cols-2">
          <div className="order-2 flex flex-col gap-7 md:order-1">
            <div className="font-mono text-xs tracking-[0.12em] text-violet">{active.eyebrow}</div>
            <h1 className="text-balance font-display text-[clamp(2.2rem,6vw,4.2rem)] font-bold uppercase leading-[1.04] text-ink">
              {active.headline}
            </h1>
            <p className="max-w-lg text-[17px] leading-relaxed text-muted">{active.lede}</p>
            <div className="flex flex-wrap items-center gap-6 pt-2">
              <Button href={`/${active.slug}`}>{active.ctaLabel}</Button>
              <Link href="/method" className="font-mono text-sm text-ink opacity-85 transition-opacity hover:opacity-100">
                See the method <span className="text-violet">→</span>
              </Link>
            </div>
          </div>

          <div className="order-1 mx-auto w-full max-w-[420px] md:order-2 md:mx-0 md:ml-auto">
            <Prism />
          </div>
        </div>
      </Container>
    </section>
  );
}
