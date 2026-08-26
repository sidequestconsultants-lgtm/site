import Link from "next/link";
import type { ReactNode } from "react";

type ButtonProps = {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
  size?: "default" | "sm";
  className?: string;
};

// Labels are plain strings ending in "→" (e.g. "Book an audit →") — split
// the arrow into its own span so .sq-btn's .arw sizing rule (bigger than
// the surrounding uppercase mono text, smaller again in .sm) actually has
// something to target, without every call site needing to pass it separately.
function withArrow(children: ReactNode): ReactNode {
  if (typeof children === "string") {
    const trimmed = children.trimEnd();
    if (trimmed.endsWith("→")) {
      const label = trimmed.slice(0, -1).trimEnd();
      return (
        <>
          {label} <span className="arw">→</span>
        </>
      );
    }
  }
  return children;
}

export default function Button({ href, children, variant = "primary", size = "default", className }: ButtonProps) {
  const isExternal = href.startsWith("http") || href.startsWith("mailto:");
  const classes = ["sq-btn", "w-fit", variant === "secondary" && "secondary", size === "sm" && "sm", className]
    .filter(Boolean)
    .join(" ");

  return (
    <Link href={href} className={classes} {...(isExternal ? { target: "_blank", rel: "noreferrer" } : {})}>
      {withArrow(children)}
    </Link>
  );
}
