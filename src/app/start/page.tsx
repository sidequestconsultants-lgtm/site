import type { Metadata } from "next";
import { Suspense } from "react";
import PageHeader from "@/components/PageHeader";
import IntakeForm from "@/components/IntakeForm";
import Container from "@/components/Container";

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
      <section className="pb-24 pt-6 sm:pb-32">
        <Container>
          <div className="max-w-2xl">
            <Suspense fallback={null}>
              <IntakeForm />
            </Suspense>
          </div>
        </Container>
      </section>
    </>
  );
}
