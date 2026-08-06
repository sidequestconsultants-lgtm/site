import Hero from "@/components/sections/Hero";
import ServicesTriad from "@/components/sections/ServicesTriad";
import Method from "@/components/sections/Method";
import Work from "@/components/sections/Work";
import Studio from "@/components/sections/Studio";
import Manifesto from "@/components/sections/Manifesto";
import CtaIntake from "@/components/sections/CtaIntake";

export default function Home() {
  return (
    <>
      <Hero />
      <ServicesTriad />
      <Method />
      <Work />
      <Studio />
      <Manifesto />
      <CtaIntake />
    </>
  );
}
