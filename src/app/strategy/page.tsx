import type { Metadata } from "next";
import ServicePageTemplate from "@/components/ServicePageTemplate";
import { services } from "@/data/services";

export const metadata: Metadata = {
  title: services.strategy.name,
  description: services.strategy.lede,
};

export default function StrategyPage() {
  return <ServicePageTemplate slug="strategy" />;
}
