import RevealOnScroll from "@/components/RevealOnScroll";
import { founders, studioLine } from "@/data/team";

export default function Studio() {
  return (
    <section id="studio" className="border-t border-hairline px-5 py-20 sm:px-8 sm:py-28">
      <div className="mx-auto flex max-w-[1400px] flex-wrap gap-14">
        <RevealOnScroll className="flex-1" as="div">
          <h2 className="text-balance font-display text-[clamp(1.8rem,3.2vw,2.6rem)] font-bold uppercase leading-tight text-ink">
            Studio.
          </h2>
          <p className="mt-6 max-w-md text-[17px] leading-relaxed text-muted">{studioLine}</p>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="flex flex-1 flex-col">
          {founders.map((f, i) => (
            <div
              key={f.name}
              className={`flex items-baseline justify-between border-hairline py-6 ${i < founders.length - 1 ? "border-b" : ""}`}
            >
              <span className="font-display text-lg font-semibold uppercase text-ink">{f.name}</span>
              <span className="font-mono text-xs tracking-wide text-dim">{f.role}</span>
            </div>
          ))}
        </RevealOnScroll>
      </div>
    </section>
  );
}
