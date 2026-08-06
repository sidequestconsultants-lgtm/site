import type { ElementType, ReactNode } from "react";

export default function Container({
  children,
  className,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: ElementType;
}) {
  return (
    <Tag className={["mx-auto w-full max-w-[1200px] px-[clamp(20px,4vw,48px)]", className].filter(Boolean).join(" ")}>
      {children}
    </Tag>
  );
}
