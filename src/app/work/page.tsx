import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Work from "@/components/sections/Work";
import CtaIntake from "@/components/sections/CtaIntake";

export const metadata: Metadata = {
  title: "Work",
  description: "Proof, built with our own system.",
};

export default function WorkPage() {
  return (
    <>
      <PageHeader
        eyebrow="// work"
        title="Proof, not promises."
        lede="Pre-revenue, so this is internal: the tools we built to run our own operation, shown as-is."
      />
      <Work />
      <CtaIntake />
    </>
  );
}
