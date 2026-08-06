import RevealOnScroll from "@/components/RevealOnScroll";
import Button from "@/components/ui/Button";
import Container from "@/components/Container";

export default function CtaIntake() {
  return (
    <section className="border-t border-hairline py-20 sm:py-28">
      <Container>
        <RevealOnScroll className="flex flex-wrap items-center justify-between gap-8">
          <h2 className="text-balance font-display text-[clamp(1.8rem,3.6vw,2.8rem)] font-bold uppercase leading-tight text-ink">
            Ready for the detour?
          </h2>
          <Button href="/start">Start a sidequest →</Button>
        </RevealOnScroll>
      </Container>
    </section>
  );
}
