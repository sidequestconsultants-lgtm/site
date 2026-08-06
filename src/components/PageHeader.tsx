import RevealOnScroll from "@/components/RevealOnScroll";
import Container from "@/components/Container";

export default function PageHeader({
  eyebrow,
  title,
  lede,
}: {
  eyebrow: string;
  title: string;
  lede?: string;
}) {
  return (
    <section className="pb-4 pt-14 sm:pt-20">
      <Container>
        <RevealOnScroll>
          <div className="font-mono text-xs tracking-[0.12em] text-violet">{eyebrow}</div>
          <h1 className="mt-6 text-balance font-display text-[clamp(2rem,5vw,3.4rem)] font-bold uppercase leading-[1.08] text-ink">
            {title}
          </h1>
          {lede && <p className="mt-6 max-w-xl text-[17px] leading-relaxed text-muted">{lede}</p>}
        </RevealOnScroll>
      </Container>
    </section>
  );
}
