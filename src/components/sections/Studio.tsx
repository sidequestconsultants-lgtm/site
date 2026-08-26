import RevealOnScroll from "@/components/RevealOnScroll";
import Container from "@/components/Container";
import CornerBracket from "@/components/brand/CornerBracket";
import FounderSilhouette from "@/components/brand/FounderSilhouette";
import QuestWaypoint from "@/components/QuestWaypoint";
import { founders, studioLine } from "@/data/team";

export default function Studio() {
  return (
    <section id="studio" data-quest="Studio" className="section-rhythm relative snap-start border-t border-hairline">
      <QuestWaypoint side="right" />
      <Container>
        <RevealOnScroll className="mb-10 max-w-xl">
          <h2 className="text-balance font-display text-[clamp(1.8rem,3.2vw,2.6rem)] font-bold uppercase leading-tight text-ink">
            Studio.
          </h2>
          <p className="mt-4 text-[17px] leading-relaxed text-muted">{studioLine}</p>
        </RevealOnScroll>

        <div className="grid gap-6 sm:grid-cols-3">
          {founders.map((f, i) => (
            <RevealOnScroll key={f.name} delay={i * 0.08}>
              <div
                className={`card-hover accent-${f.accent} group relative flex h-full flex-col gap-5 rounded-md border border-hairline bg-surface p-5`}
              >
                <div className="founder-frame relative aspect-square w-full overflow-hidden rounded border border-hairline">
                  {/* replace silhouette with real photo */}
                  <FounderSilhouette accent={f.accent} />
                  <CornerBracket className="absolute left-1.5 top-1.5 h-3.5 w-3.5" />
                  <CornerBracket className="absolute right-1.5 top-1.5 h-3.5 w-3.5 rotate-90" />
                  <CornerBracket className="absolute bottom-1.5 right-1.5 h-3.5 w-3.5 rotate-180" />
                  <CornerBracket className="absolute bottom-1.5 left-1.5 h-3.5 w-3.5 -rotate-90" />
                  <span className="absolute left-2.5 top-2.5 flex items-center gap-1.5 rounded-full border border-hairline bg-base/70 px-2 py-1 font-mono text-[10px] uppercase tracking-wide text-ink backdrop-blur-sm">
                    <span className={`hud-dot h-1.5 w-1.5 rounded-full ${f.accent === "cyan" ? "bg-cyan" : "bg-violet"}`} />
                    {f.code}
                  </span>
                </div>

                <div>
                  <div className="font-display text-lg font-bold uppercase text-ink">{f.name}</div>
                  <div className="mt-1 font-mono text-[11px] uppercase tracking-wide text-dim">
                    {f.code} · {f.role}
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-muted">{f.owns}</p>
                </div>
              </div>
            </RevealOnScroll>
          ))}
        </div>
      </Container>
    </section>
  );
}
