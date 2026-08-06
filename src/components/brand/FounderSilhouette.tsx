import { useId } from "react";
import { generateField } from "@/lib/tessellation";

const BUST_PATH =
  "M100 18c17 0 31 14 31 31 0 13-8 25-19 30 24 8 42 29 45 55l1 10H42l1-10c3-26 21-47 45-55-11-5-19-17-19-30 0-17 14-31 31-31Z";

export default function FounderSilhouette({ accent = "violet" }: { accent?: "violet" | "cyan" }) {
  const clipId = useId();
  const triangles = generateField(22, 200, 200);
  const strokeColor = accent === "cyan" ? "#9DD3FF" : "#7B6CF0";

  return (
    <svg viewBox="0 0 200 200" className="h-full w-full" aria-hidden="true">
      <defs>
        <clipPath id={clipId}>
          <path d={BUST_PATH} />
        </clipPath>
        <radialGradient id={`${clipId}-vig`} cx="50%" cy="34%" r="70%">
          <stop offset="0%" stopColor="#000" stopOpacity="0" />
          <stop offset="100%" stopColor="#000" stopOpacity="0.4" />
        </radialGradient>
      </defs>
      <rect x="0" y="0" width="200" height="200" fill="var(--color-surface-2)" />
      <g clipPath={`url(#${clipId})`}>
        <g className="founder-field">
          {triangles.map((points, i) => (
            <polygon key={i} points={points} fill="none" stroke={strokeColor} strokeWidth="0.6" strokeOpacity="0.4" />
          ))}
        </g>
        <rect x="0" y="0" width="200" height="200" fill={`url(#${clipId}-vig)`} />
      </g>
      <path d={BUST_PATH} fill="none" stroke={strokeColor} strokeWidth="1.2" strokeOpacity="0.65" />
    </svg>
  );
}
