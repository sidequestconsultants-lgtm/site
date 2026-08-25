import TessellationField from "@/components/brand/TessellationField";

// Global backdrop, fixed behind all page content: a full-bleed triangle
// lattice, a soft glow near the top, and a gradient that darkens toward
// the bottom so the lattice reads brighter up top and fades to near-black
// lower down. Sections render with transparent backgrounds so this shows
// through everywhere, not just behind the hero.
export default function SiteBackground() {
  return (
    <div className="site-bg" aria-hidden="true">
      <TessellationField
        className="site-bg-field"
        size={48}
        width={1600}
        height={900}
        strokeWidth={0.7}
        preserveAspectRatio="xMidYMid slice"
      />
      <div className="site-bg-glow" />
      <div className="site-bg-fade" />
    </div>
  );
}
