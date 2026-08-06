"use client";

import { useState } from "react";
import RevealOnScroll from "@/components/RevealOnScroll";
import { workItems, workNote, type WorkCategory } from "@/data/work";

const filters: ("All" | WorkCategory)[] = ["All", "Strategy", "Social", "Software"];

export default function Work() {
  const [filter, setFilter] = useState<"All" | WorkCategory>("All");
  const visible = filter === "All" ? workItems : workItems.filter((w) => w.category === filter);

  return (
    <section id="work" className="border-t border-hairline px-5 py-20 sm:px-8 sm:py-28">
      <div className="mx-auto max-w-[1400px]">
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
          {visible.map((item, i) => (
            <RevealOnScroll
              key={item.title}
              delay={i * 0.06}
              className="flex flex-col gap-4 rounded-md border border-hairline bg-surface p-7"
            >
              <div className="font-mono text-[11px] uppercase tracking-wide text-dim">{item.category}</div>
              <div className="font-display text-lg font-bold uppercase text-ink">{item.title}</div>
              <p className="text-sm leading-relaxed text-muted">{item.description}</p>
            </RevealOnScroll>
          ))}
        </div>

        <p className="mt-10 max-w-xl text-sm leading-relaxed text-dim">{workNote}</p>
      </div>
    </section>
  );
}
