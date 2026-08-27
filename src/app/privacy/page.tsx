import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Container from "@/components/Container";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How Sidequest handles your data.",
};

export default function PrivacyPage() {
  return (
    <>
      <PageHeader eyebrow="// legal" title="Privacy policy." />
      <section className="pb-24 pt-6 sm:pb-32">
        <Container>
          <p className="max-w-2xl text-[15px] leading-relaxed text-muted">
            Placeholder — full privacy policy coming soon. In the meantime, reach out to{" "}
            <a href="mailto:sidequest.consultants@gmail.com" className="text-ink underline underline-offset-4">
              sidequest.consultants@gmail.com
            </a>{" "}
            with any questions about how we handle your data.
          </p>
        </Container>
      </section>
    </>
  );
}
