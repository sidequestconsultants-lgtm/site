import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Method from "@/components/sections/Method";
import CtaIntake from "@/components/sections/CtaIntake";

export const metadata: Metadata = {
  title: "Method",
  description: "Diagnose, build, run — the order the work actually happens in.",
};

export default function MethodPage() {
  return (
    <>
      <PageHeader
        eyebrow="// the method"
        title="Diagnose. Build. Run."
        lede="Three services, one sequence. The audit routes the work — into a build, into a retainer, or both — so nothing gets built or run without a reason."
      />
      <Method />
      <CtaIntake />
    </>
  );
}
