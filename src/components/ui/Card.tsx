import Link from "next/link";
import type { ReactNode } from "react";
import TessellationField from "@/components/brand/TessellationField";

type CardProps = {
  title: string;
  description: string;
  href?: string;
  accent?: "violet" | "cyan";
  eyebrow?: string;
  children?: ReactNode;
};

export default function Card({ title, description, href, accent = "violet", eyebrow, children }: CardProps) {
  const strokeColor = accent === "cyan" ? "#9DD3FF" : "#7B6CF0";
  const content = (
    <div
      className={`card-hover accent-${accent} group relative flex flex-col gap-4 overflow-hidden rounded-md border border-hairline bg-gradient-to-b from-surface to-[#0C0C16] p-8`}
    >
      <TessellationField className="card-glow" masked size={50} />
      <svg viewBox="0 0 100 100" className="relative z-10 h-[18px] w-[18px]" aria-hidden="true">
        <path
          d="M42 36 L62 50 L42 64"
          fill="none"
          stroke={strokeColor}
          strokeWidth={10}
          strokeLinecap="square"
        />
      </svg>
      {eyebrow && (
        <div className="relative z-10 font-mono text-[11px] uppercase tracking-wide text-dim">
          {eyebrow}
        </div>
      )}
      <div className="relative z-10 font-display text-lg font-bold uppercase text-ink">
        {title}
      </div>
      <div className="relative z-10 text-sm leading-relaxed text-muted">{description}</div>
      {children}
    </div>
  );

  if (!href) return content;
  return (
    <Link href={href} className="block">
      {content}
    </Link>
  );
}
