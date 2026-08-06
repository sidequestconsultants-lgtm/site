import Hero from "@/components/sections/Hero";
import ServicesTriad from "@/components/sections/ServicesTriad";
import Manifesto from "@/components/sections/Manifesto";
import Method from "@/components/sections/Method";
import Work from "@/components/sections/Work";
import Studio from "@/components/sections/Studio";
import CtaIntake from "@/components/sections/CtaIntake";

export default function Home() {
  return (
    <>
      <Hero />
      <ServicesTriad />
      <Manifesto />
      <Method />
      <Work />
      <Studio />
      <CtaIntake />
    </>
  );
}
