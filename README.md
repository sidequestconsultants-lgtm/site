# Sidequest

AI-first operational studio for marketing agencies. Next.js (App Router, TypeScript,
Tailwind CSS v4), built as a static export.

## Develop

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Outputs a static site to `out/`.

## Brand

The visual system (logo, color, type, components) is documented in
[`brand/sidequest-brand-book.html`](./brand/sidequest-brand-book.html).

A standalone capability-demo dashboard (placeholder data, not wired to any
pipeline) lives at
[`brand/kingfisher-competitive-intelligence.html`](./brand/kingfisher-competitive-intelligence.html).

## Kingfisher CI pipeline

A separate, real ingestion pipeline feeds a *live* version of that same
dashboard from actual YouTube/Instagram data. See
[`pipeline/README.md`](./pipeline/README.md) for the stack, setup, secrets,
and how to run it. The live dashboard and its data live under
[`public/ci/`](./public/ci/) (served at `/ci/` once deployed); the offline,
no-network build is [`dashboard-demo.html`](./dashboard-demo.html).
