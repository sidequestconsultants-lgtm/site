import type { Metadata } from "next";
import ServicePageTemplate from "@/components/ServicePageTemplate";
import { services } from "@/data/services";

export const metadata: Metadata = {
  title: services.software.name,
  description: services.software.lede,
};

export default function SoftwarePage() {
  return <ServicePageTemplate slug="software" />;
}
