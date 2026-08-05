import type { Metadata } from "next";
import ServicePageTemplate from "@/components/ServicePageTemplate";
import { services } from "@/data/services";

export const metadata: Metadata = {
  title: services.social.name,
  description: services.social.lede,
};

export default function SocialPage() {
  return <ServicePageTemplate slug="social" />;
}
