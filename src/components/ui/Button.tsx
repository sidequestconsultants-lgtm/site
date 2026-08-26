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
          "inline-flex w-fit items-center gap-2 rounded-[3px] border border-hairline px-5 py-2.5 font-mono text-[13px] text-ink opacity-85 transition-[opacity,border-color] duration-200 hover:opacity-100 hover:border-[#33334a]",
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
      className={[
        "btn-primary inline-flex w-fit items-center gap-2 rounded-[3px] px-5 py-2.5 font-mono text-[13px] font-bold tracking-wide",
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
