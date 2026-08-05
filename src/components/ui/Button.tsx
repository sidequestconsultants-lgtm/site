import Link from "next/link";
import type { ReactNode } from "react";

type ButtonProps = {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
  className?: string;
};

export default function Button({ href, children, variant = "primary", className }: ButtonProps) {
  const isExternal = href.startsWith("http") || href.startsWith("mailto:");

  if (variant === "secondary") {
    return (
      <Link
        href={href}
        className={[
          "inline-flex w-fit items-center gap-2 rounded border border-hairline px-6 py-4 font-mono text-sm text-ink opacity-85 transition-opacity hover:opacity-100 hover:border-[#33334a]",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
        {...(isExternal ? { target: "_blank", rel: "noreferrer" } : {})}
      >
        {children}
      </Link>
    );
  }

  return (
    <Link
      href={href}
      className={["btn-primary inline-flex w-fit items-center gap-2 rounded px-6 py-4 font-mono text-sm font-bold tracking-wide", className]
        .filter(Boolean)
        .join(" ")}
      {...(isExternal ? { target: "_blank", rel: "noreferrer" } : {})}
    >
      {children}
    </Link>
  );
}
