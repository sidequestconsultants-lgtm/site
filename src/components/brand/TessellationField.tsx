import { generateField } from "@/lib/tessellation";

export default function TessellationField({
  size = 50,
  width = 1000,
  height = 600,
  stroke = "#7B6CF0",
  strokeWidth = 0.7,
  className,
  masked = false,
  preserveAspectRatio = "xMidYMid slice",
}: {
  size?: number;
  width?: number;
  height?: number;
  stroke?: string;
  strokeWidth?: number;
  className?: string;
  masked?: boolean;
  preserveAspectRatio?: string;
}) {
  const triangles = generateField(size, width, height);
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio={preserveAspectRatio}
      className={[masked ? "field-mask" : "", className].filter(Boolean).join(" ")}
      aria-hidden="true"
    >
      {triangles.map((points, i) => (
        <polygon key={i} points={points} fill="none" stroke={stroke} strokeWidth={strokeWidth} />
      ))}
    </svg>
  );
}
