"use client";

import { useId, type CSSProperties } from "react";

export default function Shard({
  className,
  style,
}: {
  className?: string;
  style?: CSSProperties;
}) {
  const gid = useId();
  return (
    <svg viewBox="0 0 40 40" className={className} style={style} aria-hidden="true">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#7B6CF0" />
          <stop offset="1" stopColor="#9DD3FF" />
        </linearGradient>
      </defs>
      <polygon points="20,3 4,36 36,33" fill="none" stroke={`url(#${gid})`} strokeWidth={1} strokeLinejoin="round" />
    </svg>
  );
}
