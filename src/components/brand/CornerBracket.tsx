export default function CornerBracket({
  className,
  animateOnce,
}: {
  className?: string;
  animateOnce?: boolean;
}) {
  return (
    <svg
      viewBox="0 0 40 40"
      className={[animateOnce ? "demo-once" : "", className].filter(Boolean).join(" ")}
      aria-hidden="true"
    >
      <path
        d="M2 16 V2 H16"
        fill="none"
        stroke="#EAEDF8"
        strokeWidth={3}
        strokeLinecap="square"
      />
    </svg>
  );
}
