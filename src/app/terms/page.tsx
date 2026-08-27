import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Container from "@/components/Container";

export const metadata: Metadata = {
  title: "Terms & Conditions",
  description: "The terms for working with Sidequest.",
};

export default function TermsPage() {
  return (
    <>
      <PageHeader eyebrow="// legal" title="Terms & conditions." />
      <section className="pb-24 pt-6 sm:pb-32">
        <Container>
          <p className="max-w-2xl text-[15px] leading-relaxed text-muted">
            Placeholder — full terms coming soon. In the meantime, reach out to{" "}
            <a href="mailto:sidequest.consultants@gmail.com" className="text-ink underline underline-offset-4">
              sidequest.consultants@gmail.com
            </a>{" "}
            with any questions about working with us.
          </p>
        </Container>
      </section>
    </>
  );
}
