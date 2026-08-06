import RevealOnScroll from "@/components/RevealOnScroll";
import Button from "@/components/ui/Button";

export default function CtaIntake() {
  return (
    <section className="border-t border-hairline px-5 py-20 sm:px-8 sm:py-28">
      <RevealOnScroll className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-8">
        <h2 className="text-balance font-display text-[clamp(1.8rem,3.6vw,2.8rem)] font-bold uppercase leading-tight text-ink">
          Ready for the detour?
        </h2>
        <Button href="/start">Start a sidequest →</Button>
      </RevealOnScroll>
    </section>
  );
}
