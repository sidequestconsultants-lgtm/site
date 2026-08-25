import type { Metadata } from "next";
import { Chakra_Petch, Space_Grotesk, Space_Mono } from "next/font/google";
import Nav from "@/components/layout/Nav";
import Footer from "@/components/layout/Footer";
import BootScreen from "@/components/BootScreen";
import SiteBackground from "@/components/brand/SiteBackground";
import "./globals.css";

const chakraPetch = Chakra_Petch({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-chakra",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-grotesk",
  display: "swap",
});

const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Sidequest — AI-First Operational Studio for Agencies",
    template: "%s — Sidequest",
  },
  description:
    "Running the agency is the main quest — the grind. Sidequest is the rewarding detour: AI-first ops audits, marketing retainers, and custom software for marketing agencies.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${chakraPetch.variable} ${spaceGrotesk.variable} ${spaceMono.variable}`}
    >
      <body className="flex min-h-screen flex-col bg-base text-ink font-body">
        <SiteBackground />
        <BootScreen />
        <Nav />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
