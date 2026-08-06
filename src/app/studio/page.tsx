import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Studio from "@/components/sections/Studio";
import Manifesto from "@/components/sections/Manifesto";
import CtaIntake from "@/components/sections/CtaIntake";

export const metadata: Metadata = {
  title: "Studio",
  description: "Three founders, twenty-five years of agency and network experience.",
};

export default function StudioPage() {
  return (
    <>
      <PageHeader
        eyebrow="// studio"
        title="Built by operators."
        lede="We ran the grind before we built a studio to help other agencies get out of it."
      />
      <Studio />
      <Manifesto />
      <CtaIntake />
    </>
  );
}
