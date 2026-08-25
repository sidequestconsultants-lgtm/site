"use client";

import { useState } from "react";
import RevealOnScroll from "@/components/RevealOnScroll";
import Container from "@/components/Container";
import TessellationField from "@/components/brand/TessellationField";
import CornerBracket from "@/components/brand/CornerBracket";
import QuestPin from "@/components/QuestPin";
import { workItems, workNote, type WorkCategory } from "@/data/work";

const filters: ("All" | WorkCategory)[] = ["All", "Strategy", "Social", "Software"];
const accentByCategory: Record<WorkCategory, "violet" | "cyan"> = {
  Strategy: "violet",
  Social: "cyan",
  Software: "violet",
};

export default function Work({ showQuestPin = false }: { showQuestPin?: boolean }) {
  const [filter, setFilter] = useState<"All" | WorkCategory>("All");
  const visible = filter === "All" ? workItems : workItems.filter((w) => w.category === filter);

  return (
    <section id="work" data-quest="Work" className="section-rhythm relative snap-start border-t border-hairline">
      {showQuestPin && (
        <QuestPin label="Work" progress={4} side="right" className="right-4 top-6 hidden md:flex lg:right-10" />
      )}
      <Container>
        <RevealOnScroll className="mb-10 flex flex-wrap items-end justify-between gap-6">
          <h2 className="text-balance font-display text-[clamp(1.8rem,3.2vw,2.6rem)] font-bold uppercase leading-tight text-ink">
            Work.
          </h2>
          <div className="flex gap-1 rounded-full border border-hairline p-1">
            {filters.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={[
                  "rounded-full px-4 py-2 font-mono text-xs uppercase tracking-wide transition-colors",
                  filter === f ? "bg-surface text-ink" : "text-dim hover:text-muted",
                ].join(" ")}
              >
                {f}
              </button>
            ))}
          </div>
        </RevealOnScroll>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((item, i) => {
            const accent = accentByCategory[item.category];
            return (
              <RevealOnScroll
                key={item.title}
                delay={i * 0.06}
                className={`card-hover accent-${accent} group relative flex flex-col gap-4 overflow-hidden rounded-md border border-hairline bg-surface p-7`}
              >
                <TessellationField className="card-glow" masked size={50} />
                <CornerBracket className="absolute left-2 top-2 h-3 w-3 opacity-50" />
                <CornerBracket className="absolute right-2 top-2 h-3 w-3 rotate-90 opacity-50" />
                <CornerBracket className="absolute bottom-2 right-2 h-3 w-3 rotate-180 opacity-50" />
                <CornerBracket className="absolute bottom-2 left-2 h-3 w-3 -rotate-90 opacity-50" />

                <div className="relative z-10 flex items-center gap-2">
                  <span className={`hud-dot h-1.5 w-1.5 rounded-full ${accent === "cyan" ? "bg-cyan" : "bg-violet"}`} />
                  <span className="font-mono text-[11px] uppercase tracking-wide text-dim">{item.category}</span>
                </div>
                <div className="relative z-10 font-display text-lg font-bold uppercase text-ink">{item.title}</div>
                <p className="relative z-10 text-sm leading-relaxed text-muted">{item.description}</p>
                <div
                  className={`relative z-10 mt-auto border-t border-hairline pt-3 font-mono text-xs ${accent === "cyan" ? "text-cyan" : "text-violet"}`}
                >
                  {item.readout}
                </div>
              </RevealOnScroll>
            );
          })}
        </div>

        <RevealOnScroll className="mt-8 flex items-start gap-3 border-l-2 border-hairline pl-4">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-dim" />
          <p className="text-sm leading-relaxed text-dim">{workNote}</p>
        </RevealOnScroll>
      </Container>
    </section>
  );
}
