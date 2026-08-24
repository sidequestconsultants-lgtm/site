import Hero from "@/components/sections/Hero";
import ServicesTriad from "@/components/sections/ServicesTriad";
import Manifesto from "@/components/sections/Manifesto";
import Method from "@/components/sections/Method";
import Work from "@/components/sections/Work";
import Studio from "@/components/sections/Studio";
import CtaIntake from "@/components/sections/CtaIntake";
import QuestMarker from "@/components/QuestMarker";
import HeroServicesShards from "@/components/HeroServicesShards";

export default function Home() {
  return (
    <>
      <QuestMarker />
      <HeroServicesShards />
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
