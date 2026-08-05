import RevealOnScroll from "@/components/RevealOnScroll";

export default function Manifesto() {
  return (
    <section className="border-t border-hairline px-5 py-24 sm:px-8 sm:py-36">
      <div className="mx-auto max-w-[1400px]">
        <RevealOnScroll>
          <p className="font-mono text-xs tracking-[0.14em] text-violet">{"// pov"}</p>
          <p className="mt-8 max-w-3xl text-balance font-display text-[clamp(1.8rem,4vw,3rem)] font-semibold leading-[1.2] text-ink">
            Every agency is being asked to do more with less. The ones who win this decade
            aren&apos;t the ones who hire more people — they&apos;re the ones who rebuild the
            operation around AI before the window closes.
          </p>
        </RevealOnScroll>
      </div>
    </section>
  );
}
