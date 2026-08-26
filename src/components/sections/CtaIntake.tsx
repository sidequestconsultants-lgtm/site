import RevealOnScroll from "@/components/RevealOnScroll";
import Button from "@/components/ui/Button";
import Container from "@/components/Container";

export default function CtaIntake() {
  return (
    <section
      id="start"
      data-quest="Start"
      className="section-rhythm relative flex min-h-screen snap-start items-center border-t border-hairline"
    >
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
