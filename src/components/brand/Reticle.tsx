type ReticleVariant = "full" | "mono" | "reversed";

const gradientId = "sq-reticle-grad";

export default function Reticle({
  variant = "full",
  className,
}: {
  variant?: ReticleVariant;
  className?: string;
}) {
  const filter =
    variant === "mono"
      ? "grayscale(1) brightness(1.4)"
      : variant === "reversed"
        ? "invert(1) hue-rotate(180deg)"
        : undefined;

  return (
    <svg
      viewBox="0 0 100 100"
      className={className}
      style={filter ? { filter } : undefined}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#9DD3FF" />
          <stop offset="1" stopColor="#7B6CF0" />
        </linearGradient>
      </defs>
      <g stroke="#EAEDF8" strokeWidth={4} fill="none" strokeLinecap="square">
        <path d="M6 22 V6 H22" />
        <path d="M78 6 H94 V22" />
        <path d="M94 78 V94 H78" />
        <path d="M22 94 H6 V78" />
      </g>
      <path
        d="M42 36 L62 50 L42 64"
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth={8}
        strokeLinecap="square"
        strokeLinejoin="miter"
      />
    </svg>
  );
}
