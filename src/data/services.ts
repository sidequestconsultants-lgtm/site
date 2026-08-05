export type ServiceSlug = "strategy" | "social" | "software";

export interface ServiceData {
  slug: ServiceSlug;
  name: string;
  tag: string;
  tagColor: "dim" | "cyan" | "violet";
  accent: "violet" | "cyan";
  eyebrow: string;
  headline: string;
  lede: string;
  ctaLabel: string;
  tagline: string;
  capabilities: string[];
  process: { step: string; detail: string }[];
  pairsWith: ServiceSlug[];
}

export const services: Record<ServiceSlug, ServiceData> = {
  strategy: {
    slug: "strategy",
    name: "Strategy / Ops Audit",
    tag: "DIAGNOSE",
    tagColor: "dim",
    accent: "violet",
    eyebrow: "// strategy · the ops audit",
    headline: "Level up the operation.",
    lede: "We map the manual grind and design the AI-augmented system to replace it — the diagnosis that routes everything else.",
    ctaLabel: "Book an audit →",
    tagline: "The apex service. Diagnoses the gaps and routes the other two.",
    capabilities: [
      "Gap audit across the full operation",
      "AI-opportunity mapping",
      "System design for the AI-augmented workflow",
      "Roadmap, sequenced and owned",
      "Routing into retainer and software work",
    ],
    process: [
      { step: "Audit the operation", detail: "We sit inside the real workflow — not a survey — and map where time actually goes." },
      { step: "Map AI opportunities", detail: "Every manual step gets scored: automate, augment, or leave alone." },
      { step: "Design the system", detail: "A concrete architecture for the AI-augmented operation, not a slide deck." },
      { step: "Route into execution", detail: "The roadmap hands off directly into a retainer, a build, or both." },
    ],
    pairsWith: ["social", "software"],
  },
  social: {
    slug: "social",
    name: "AI Marketing Retainers",
    tag: "RUN",
    tagColor: "cyan",
    accent: "cyan",
    eyebrow: "// ai marketing retainers",
    headline: "Ship more. Grind less.",
    lede: "AI-run social, creative, and paid — the output of a full team at a fraction of the manual cost.",
    ctaLabel: "See retainers →",
    tagline: "The execution engine. Comms, content, and performance, run lean.",
    capabilities: [
      "Comms and content strategy",
      "Social asset production",
      "Gen-AI content at scale",
      "Paid / performance media",
      "Weekly shipping cadence, reported",
    ],
    process: [
      { step: "Onboard & audit channels", detail: "We learn the brand voice and the current channel mix in week one." },
      { step: "Build the content engine", detail: "AI-run production pipelines tuned to your formats and cadence." },
      { step: "Ship weekly", detail: "Social, creative, gen-AI content, and paid — out the door on schedule." },
      { step: "Report & iterate", detail: "Numbers reviewed on a fixed cycle, not buried in a dashboard nobody opens." },
    ],
    pairsWith: ["strategy", "software"],
  },
  software: {
    slug: "software",
    name: "Custom AI Software",
    tag: "BUILD",
    tagColor: "violet",
    accent: "violet",
    eyebrow: "// custom ai software",
    headline: "Bring the problem. We build the tool.",
    lede: "Light, custom AI tools that kill the manual gaps in how you work — built fast, wired into your stack.",
    ctaLabel: "Explore tools →",
    tagline: "The build. Bespoke tools for the gaps no off-the-shelf product fills.",
    capabilities: [
      "Bespoke trackers and dashboards",
      "Workflow automation wired into your stack",
      "Gen-AI features embedded in existing tools",
      "Maintenance inside the retainer",
      "Changes scoped and billed separately",
    ],
    process: [
      { step: "Bring the problem", detail: "You describe the manual gap — we don't need a spec, just the pain." },
      { step: "Scope & prototype", detail: "A working prototype before a contract gets heavy." },
      { step: "Build & wire in", detail: "Shipped into your existing stack, not a standalone island tool." },
      { step: "Maintain inside the retainer", detail: "Upkeep is covered; changes beyond scope are billed clearly." },
    ],
    pairsWith: ["strategy", "social"],
  },
};

export const serviceOrder: ServiceSlug[] = ["strategy", "social", "software"];
