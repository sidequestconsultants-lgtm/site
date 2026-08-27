import Link from "next/link";
import Container from "@/components/Container";
import { serviceOrder } from "@/data/services";

const modeLabels: Record<(typeof serviceOrder)[number], string> = {
  strategy: "Strategy",
  social: "Social",
  software: "Software",
};

const companyLinks = [
  { href: "/method", label: "Method" },
  { href: "/work", label: "Work" },
  { href: "/studio", label: "Studio" },
];

const CONTACT_EMAIL = "sidequest.consultants@gmail.com";

function FooterColumn({ title, links }: { title: string; links: { href: string; label: string }[] }) {
  return (
    <div className="flex flex-col gap-3">
      <span className="font-mono text-[11px] uppercase tracking-wide text-dim">{title}</span>
      <ul className="flex flex-col gap-2">
        {links.map((l) => (
          <li key={l.href}>
            <Link href={l.href} className="text-sm text-muted transition-colors hover:text-ink">
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Footer() {
  return (
    <footer className="border-t border-hairline py-16">
      <Container>
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div className="flex flex-col gap-3">
            <span className="font-body text-sm font-medium uppercase tracking-[0.25em] text-ink">Sidequest</span>
            <p className="max-w-xs text-sm leading-relaxed text-muted">
              The rewarding detour — AI-first ops, marketing, and software for agencies ready to rebuild around it.
            </p>
            <span className="font-mono text-xs tracking-wide text-dim">© 2026 Sidequest</span>
          </div>

          <FooterColumn title="Services" links={serviceOrder.map((slug) => ({ href: `/${slug}`, label: modeLabels[slug] }))} />
          <FooterColumn title="Company" links={companyLinks} />
          <FooterColumn
            title="Contact"
            links={[
              { href: `mailto:${CONTACT_EMAIL}`, label: CONTACT_EMAIL },
              { href: "/start", label: "Start a sidequest" },
            ]}
          />
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-between gap-4 border-t border-hairline pt-6">
          <span className="font-mono text-xs tracking-wide text-dim">© 2026 — the detour that wins.</span>
          <div className="flex gap-6 font-mono text-xs text-dim">
            <Link href="/privacy" className="transition-colors hover:text-muted">
              Privacy Policy
            </Link>
            <Link href="/terms" className="transition-colors hover:text-muted">
              Terms &amp; Conditions
            </Link>
          </div>
        </div>
      </Container>
    </footer>
  );
}
