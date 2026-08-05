"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Reticle from "@/components/brand/Reticle";
import Button from "@/components/ui/Button";

const links = [
  { href: "/#services", label: "Services" },
  { href: "/method", label: "Method" },
  { href: "/work", label: "Work" },
  { href: "/studio", label: "Studio" },
];

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={[
        "sticky top-0 z-50 transition-colors duration-300",
        scrolled ? "border-b border-hairline bg-base/85 backdrop-blur" : "border-b border-transparent bg-transparent",
      ].join(" ")}
    >
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-6 px-5 py-4 sm:px-8">
        <Link href="/" className="flex items-center gap-3">
          <Reticle className="h-7 w-7" />
          <span className="font-body text-sm font-medium uppercase tracking-[0.25em] text-ink">
            Sidequest
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="font-body text-sm text-muted transition-colors hover:text-ink"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:block">
          <Button href="/start" className="px-5 py-3 text-xs">
            Start a sidequest →
          </Button>
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
          aria-expanded={open}
          className="flex h-10 w-10 items-center justify-center rounded border border-hairline text-ink md:hidden"
        >
          <span className="font-mono text-xs">{open ? "×" : "≡"}</span>
        </button>
      </div>

      {open && (
        <nav className="flex flex-col gap-1 border-t border-hairline bg-base px-5 pb-6 pt-4 md:hidden">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="py-3 font-body text-sm text-muted transition-colors hover:text-ink"
            >
              {l.label}
            </Link>
          ))}
          <Button href="/start" className="mt-3 justify-center px-5 py-3 text-xs">
            Start a sidequest →
          </Button>
        </nav>
      )}
    </header>
  );
}
