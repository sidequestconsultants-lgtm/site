import RevealOnScroll from "@/components/RevealOnScroll";
import Button from "@/components/ui/Button";
import Container from "@/components/Container";
import QuestPin from "@/components/QuestPin";

export default function CtaIntake({ showQuestPin = false }: { showQuestPin?: boolean }) {
  return (
    <section id="start" data-quest="Start" className="section-rhythm relative snap-start border-t border-hairline">
      {showQuestPin && (
        <QuestPin label="Start" progress={6} side="right" className="right-4 top-6 hidden md:flex lg:right-10" />
      )}
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
