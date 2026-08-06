import Link from "next/link";
import RevealOnScroll from "@/components/RevealOnScroll";
import Button from "@/components/ui/Button";
import Prism from "@/components/brand/Prism";
import Container from "@/components/Container";
import { services, type ServiceSlug } from "@/data/services";
import { workItems } from "@/data/work";

const categoryBySlug: Record<ServiceSlug, "Strategy" | "Social" | "Software"> = {
  strategy: "Strategy",
  social: "Social",
  software: "Software",
};

export default function ServicePageTemplate({ slug }: { slug: ServiceSlug }) {
  const s = services[slug];
  const samples = workItems.filter((w) => w.category === categoryBySlug[slug]);

  return (
    <>
      <section className="relative overflow-hidden pb-[clamp(56px,7vw,80px)] pt-12">
        <Container className="grid items-center gap-[clamp(32px,5vw,64px)] md:grid-cols-2">
          <div className="flex flex-col gap-6">
            <div className="font-mono text-xs tracking-[0.12em] text-violet">{s.eyebrow}</div>
            <h1 className="text-balance font-display text-[clamp(2rem,5vw,3.4rem)] font-bold uppercase leading-[1.08] text-ink">
              {s.name}
            </h1>
            <p className="max-w-lg text-[17px] leading-relaxed text-muted">{s.tagline}</p>
            <div className="pt-2">
              <Button href="/start">Start a sidequest →</Button>
            </div>
          </div>
          <div className="mx-auto w-full max-w-[380px] md:mx-0 md:ml-auto">
            <Prism />
          </div>
        </Container>
      </section>

      <section className="border-t border-hairline py-16 sm:py-24">
        <Container>
          <RevealOnScroll className="mb-10">
            <span className="font-mono text-xs uppercase tracking-wide text-dim">Included</span>
          </RevealOnScroll>
          <div className="grid gap-x-12 gap-y-0 md:grid-cols-2">
            {s.capabilities.map((c, i) => (
              <RevealOnScroll
                key={c}
                delay={i * 0.05}
                className="flex items-baseline gap-4 border-b border-hairline py-5"
              >
                <span className="font-mono text-xs text-dim">0{i + 1}</span>
                <span className="text-[15px] text-ink">{c}</span>
              </RevealOnScroll>
            ))}
          </div>
        </Container>
      </section>

      <section className="border-t border-hairline py-16 sm:py-24">
        <Container>
          <RevealOnScroll className="mb-14">
            <span className="font-mono text-xs uppercase tracking-wide text-dim">How it works</span>
          </RevealOnScroll>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {s.process.map((p, i) => (
              <RevealOnScroll key={p.step} delay={i * 0.08}>
                <span className="font-mono text-sm text-dim">0{i + 1}</span>
                <div className="mt-3 font-display text-lg font-bold uppercase text-ink">{p.step}</div>
                <p className="mt-2 text-sm leading-relaxed text-muted">{p.detail}</p>
              </RevealOnScroll>
            ))}
          </div>
        </Container>
      </section>

      {samples.length > 0 && (
        <section className="border-t border-hairline py-16 sm:py-24">
          <Container>
            <RevealOnScroll className="mb-10">
              <span className="font-mono text-xs uppercase tracking-wide text-dim">Samples</span>
            </RevealOnScroll>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {samples.map((item) => (
                <RevealOnScroll
                  key={item.title}
                  className="flex flex-col gap-3 rounded-md border border-hairline bg-surface p-7"
                >
                  <div className="font-display text-lg font-bold uppercase text-ink">{item.title}</div>
                  <p className="text-sm leading-relaxed text-muted">{item.description}</p>
                </RevealOnScroll>
              ))}
            </div>
          </Container>
        </section>
      )}

      <section className="border-t border-hairline py-16 sm:py-24">
        <Container>
          <RevealOnScroll className="mb-10">
            <span className="font-mono text-xs uppercase tracking-wide text-dim">Pairs with</span>
          </RevealOnScroll>
          <div className="grid gap-6 sm:grid-cols-2">
            {s.pairsWith.map((otherSlug) => {
              const other = services[otherSlug];
              return (
                <RevealOnScroll key={otherSlug}>
                  <Link
                    href={`/${otherSlug}`}
                    className={`card-hover accent-${other.accent} group flex flex-col gap-3 rounded-md border border-hairline bg-surface p-7`}
                  >
                    <div className="font-display text-lg font-bold uppercase text-ink">{other.name}</div>
                    <p className="text-sm leading-relaxed text-muted">{other.tagline}</p>
                    <span className="mt-2 font-mono text-xs text-ink opacity-80 transition-opacity group-hover:opacity-100">
                      Explore <span className="text-violet">→</span>
                    </span>
                  </Link>
                </RevealOnScroll>
              );
            })}
          </div>
        </Container>
      </section>

      <section className="border-t border-hairline py-20 sm:py-28">
        <Container>
          <RevealOnScroll className="flex flex-wrap items-center justify-between gap-8">
            <h2 className="text-balance font-display text-[clamp(1.8rem,3.6vw,2.8rem)] font-bold uppercase leading-tight text-ink">
              Ready to start with {s.name.split(" / ")[0]}?
            </h2>
            <Button href={`/start?service=${s.slug}`}>Start a sidequest →</Button>
          </RevealOnScroll>
        </Container>
      </section>
    </>
  );
}
