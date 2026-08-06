import type { Metadata } from "next";
import { Suspense } from "react";
import PageHeader from "@/components/PageHeader";
import IntakeForm from "@/components/IntakeForm";

export const metadata: Metadata = {
  title: "Start a sidequest",
  description: "Send us the brief — we'll route it to the right service.",
};

export default function StartPage() {
  return (
    <>
      <PageHeader
        eyebrow="// start a sidequest"
        title="Send the brief."
        lede="Tell us the grind. We'll route it to the right service and get back to you."
      />
      <section className="px-5 pb-24 pt-6 sm:px-8 sm:pb-32">
        <div className="mx-auto max-w-2xl">
          <Suspense fallback={null}>
            <IntakeForm />
          </Suspense>
        </div>
      </section>
    </>
  );
}
