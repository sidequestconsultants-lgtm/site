"use client";

import { useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { serviceOrder, services } from "@/data/services";

const INTAKE_EMAIL = "sidequest.consultants@gmail.com";

export default function IntakeForm() {
  const searchParams = useSearchParams();
  const preselected = searchParams.get("service");
  const initialService = serviceOrder.includes(preselected as never) ? (preselected as (typeof serviceOrder)[number]) : "strategy";

  const [service, setService] = useState(initialService);
  const [sent, setSent] = useState(false);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const name = String(data.get("name") ?? "");
    const email = String(data.get("email") ?? "");
    const agency = String(data.get("agency") ?? "");
    const message = String(data.get("message") ?? "");

    const subject = `Sidequest brief — ${services[service].name}`;
    const body = [
      `Name: ${name}`,
      `Agency: ${agency}`,
      `Email: ${email}`,
      `Service: ${services[service].name}`,
      "",
      message,
    ].join("\n");

    window.location.href = `mailto:${INTAKE_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    setSent(true);
  }

  if (sent) {
    return (
      <div className="rounded-md border border-hairline bg-surface p-10">
        <div className="font-mono text-xs uppercase tracking-wide text-cyan">Brief queued</div>
        <p className="mt-4 max-w-md text-[17px] leading-relaxed text-muted">
          Your email client should have opened with the brief pre-filled. Send it, and we&apos;ll
          be in touch.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <div className="grid gap-6 sm:grid-cols-2">
        <label className="flex flex-col gap-2">
          <span className="font-mono text-[11px] uppercase tracking-wide text-dim">Name</span>
          <input
            name="name"
            required
            className="rounded border border-hairline bg-surface px-4 py-3 text-[15px] text-ink outline-none focus:border-violet"
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="font-mono text-[11px] uppercase tracking-wide text-dim">Email</span>
          <input
            type="email"
            name="email"
            required
            className="rounded border border-hairline bg-surface px-4 py-3 text-[15px] text-ink outline-none focus:border-violet"
          />
        </label>
      </div>

      <label className="flex flex-col gap-2">
        <span className="font-mono text-[11px] uppercase tracking-wide text-dim">Agency</span>
        <input
          name="agency"
          className="rounded border border-hairline bg-surface px-4 py-3 text-[15px] text-ink outline-none focus:border-violet"
        />
      </label>

      <fieldset className="flex flex-col gap-3">
        <legend className="font-mono text-[11px] uppercase tracking-wide text-dim">Service</legend>
        <div className="flex flex-wrap gap-2">
          {serviceOrder.map((slug) => (
            <button
              type="button"
              key={slug}
              onClick={() => setService(slug)}
              className={[
                "rounded-full border px-4 py-2 font-mono text-xs uppercase tracking-wide transition-colors",
                service === slug
                  ? "border-violet bg-surface text-ink"
                  : "border-hairline text-dim hover:text-muted",
              ].join(" ")}
            >
              {services[slug].name}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="flex flex-col gap-2">
        <span className="font-mono text-[11px] uppercase tracking-wide text-dim">
          What&apos;s the grind you want off your plate?
        </span>
        <textarea
          name="message"
          rows={5}
          className="resize-none rounded border border-hairline bg-surface px-4 py-3 text-[15px] text-ink outline-none focus:border-violet"
        />
      </label>

      <button type="submit" className="btn-primary w-fit rounded px-6 py-4 font-mono text-sm font-bold tracking-wide">
        Send the brief →
      </button>
    </form>
  );
}
