import RevealOnScroll from "@/components/RevealOnScroll";

const steps = [
  { label: "Diagnose", detail: "The audit — map the grind, find the AI-shaped gaps." },
  { label: "Build", detail: "The tools — bespoke software wired into your stack." },
  { label: "Run", detail: "The retainer — AI-run social, creative, and paid, shipped weekly." },
];

export default function Method() {
  return (
    <section id="method-preview" className="border-t border-hairline px-5 py-20 sm:px-8 sm:py-28">
      <div className="mx-auto max-w-[1400px]">
        <RevealOnScroll className="mb-14 max-w-xl">
          <h2 className="text-balance font-display text-[clamp(1.8rem,3.2vw,2.6rem)] font-bold uppercase leading-tight text-ink">
            The method.
          </h2>
        </RevealOnScroll>

        <div className="flex flex-col gap-0 md:flex-row md:items-stretch md:gap-0">
          {steps.map((step, i) => (
            <RevealOnScroll
              key={step.label}
              delay={i * 0.1}
              className="flex flex-1 items-start gap-5 border-b border-hairline py-8 md:flex-col md:items-start md:gap-6 md:border-b-0 md:border-r md:px-8 md:py-2 md:last:border-r-0 md:first:pl-0"
            >
              <span className="font-mono text-sm text-dim">0{i + 1}</span>
              <div>
                <div className="font-display text-xl font-bold uppercase text-ink">{step.label}</div>
                <p className="mt-2 max-w-xs text-sm leading-relaxed text-muted">{step.detail}</p>
              </div>
            </RevealOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
