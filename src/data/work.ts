export type WorkCategory = "Strategy" | "Social" | "Software";

export interface WorkItem {
  title: string;
  category: WorkCategory;
  description: string;
}

export const workItems: WorkItem[] = [
  {
    title: "Sidequest Ops OS",
    category: "Strategy",
    description: "The Notion-based system we run our own operation on — audited, mapped, and rebuilt before we sold it to anyone else.",
  },
  {
    title: "AI Content Engine",
    category: "Social",
    description: "A proof-of-concept pipeline that scripts, drafts, and formats a week of social output in an afternoon.",
  },
  {
    title: "Client Intake Router",
    category: "Software",
    description: "A lightweight tool that reads an incoming brief and routes it to the right service — built to prove the model works.",
  },
];

export const workNote =
  "Built with our own system, pre-revenue. No case studies dressed up as something they're not — this is the internal proof, shown as-is.";
