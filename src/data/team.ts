export interface Founder {
  name: string;
  initials: string;
  code: string;
  role: string;
  owns: string;
  accent: "violet" | "cyan";
}

export const founders: Founder[] = [
  {
    name: "Imad",
    initials: "IM",
    code: "CBO",
    role: "Chief Business Officer",
    owns: "Growth, partnerships, and the client relationship.",
    accent: "violet",
  },
  {
    name: "Urvi",
    initials: "UR",
    code: "COO",
    role: "Chief Operating Officer",
    owns: "Delivery, systems, and the engine that runs the studio.",
    accent: "cyan",
  },
  {
    name: "Tanish",
    initials: "TA",
    code: "CCO",
    role: "Chief Creative Officer",
    owns: "Creative direction, brand, and the quality bar.",
    accent: "violet",
  },
];

export const studioLine =
  "Three founders. Twenty-five years of combined agency and network experience between them — spent inside the grind we now help other agencies get out of.";
