import RevealOnScroll from "@/components/RevealOnScroll";
import Container from "@/components/Container";
import CornerBracket from "@/components/brand/CornerBracket";
import TessellationField from "@/components/brand/TessellationField";
import QuestWaypoint from "@/components/QuestWaypoint";

export default function Manifesto() {
  return (
    <section id="pov" data-quest="POV" className="section-rhythm relative snap-start overflow-hidden border-t border-hairline">
      <QuestWaypoint side="left" />
      <TessellationField
        className="field-mask-center pointer-events-none absolute inset-0 h-full w-full opacity-[0.05]"
        size={46}
      />
      <Container>
        <RevealOnScroll className="relative mx-auto max-w-3xl px-8 py-10 sm:px-14 sm:py-14">
          <CornerBracket className="absolute left-0 top-0 h-6 w-6 opacity-40" />
          <CornerBracket className="absolute right-0 top-0 h-6 w-6 rotate-90 opacity-40" />
          <CornerBracket className="absolute bottom-0 right-0 h-6 w-6 rotate-180 opacity-40" />
          <CornerBracket className="absolute bottom-0 left-0 h-6 w-6 -rotate-90 opacity-40" />

          <p className="font-mono text-xs tracking-[0.14em] text-violet">{"// pov"}</p>
          <p className="mt-8 text-balance font-display text-[clamp(1.8rem,4vw,3rem)] font-semibold leading-[1.3] text-ink">
            Every agency is being asked to do more with less. The ones who win this decade
            aren&apos;t the ones who hire more people — they&apos;re the ones who rebuild the
            operation around AI <span className="gradient-accent">before the window closes</span>.
          </p>
        </RevealOnScroll>
      </Container>
    </section>
  );
}
