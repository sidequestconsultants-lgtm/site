import Container from "@/components/Container";

export default function Footer() {
  return (
    <footer className="border-t border-hairline py-9">
      <Container className="flex flex-wrap items-center justify-between gap-4">
        <span className="font-body text-[13px] uppercase tracking-[0.25em] text-ink">
          Sidequest
        </span>
        <span className="font-mono text-xs tracking-wide text-dim">
          © 2026 — the detour that wins.
        </span>
      </Container>
    </footer>
  );
}
