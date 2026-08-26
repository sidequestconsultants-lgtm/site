// A single reticle anchor, placed absolutely inside its own section (not
// fixed to the viewport) so it scrolls with the page like any other piece
// of content. QuestDot finds these via [data-quest] section → ".wp" and
// reads their live position every frame to thread the travelling dot
// between them — nothing here tracks position itself.
export default function QuestWaypoint({ side, className }: { side: "left" | "right"; className?: string }) {
  return (
    <div className={["wp", className].filter(Boolean).join(" ")} data-side={side} aria-hidden="true">
      <span className="wpc tl" />
      <span className="wpc tr" />
      <span className="wpc bl" />
      <span className="wpc br" />
      <svg className="chev" viewBox="0 0 12 12" aria-hidden="true">
        <path
          d="M3 2 L9 6 L3 10"
          fill="none"
          stroke="#7B6CF0"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          transform={side === "right" ? "translate(12,0) scale(-1,1)" : undefined}
        />
      </svg>
    </div>
  );
}
