import Link from "next/link";
import RevealOnScroll from "@/components/RevealOnScroll";
import TessellationField from "@/components/brand/TessellationField";
import { serviceOrder, services } from "@/data/services";

const tagColorClass = { dim: "text-dim", cyan: "text-cyan", violet: "text-violet" } as const;

export default function ServicesTriad() {
  return (
    <section id="services" className="border-t border-hairline px-5 py-20 sm:px-8 sm:py-28">
      <div className="mx-auto max-w-[1400px]">
        <RevealOnScroll className="mb-10 max-w-xl">
          <p className="text-[17px] leading-relaxed text-muted">
            Three services, one order. Strategy diagnoses the gaps — the apex that routes work
            into the other two.
          </p>
        </RevealOnScroll>

        <div className="grid gap-6 md:grid-cols-3">
          {serviceOrder.map((slug, i) => {
            const s = services[slug];
            return (
              <RevealOnScroll key={slug} delay={i * 0.08}>
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
          })}
        </div>
      </div>
    </section>
  );
}
