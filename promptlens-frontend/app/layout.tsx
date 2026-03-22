import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";
import Navbar from "@/components/Navbar";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PromptLens",
  description: "Prompt analytics dashboard, analyzer, and AI chat interface.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} h-full antialiased`}>
      <body className="min-h-full bg-slate-950 text-slate-100">
        <div className="relative min-h-screen">
          <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_10%_20%,rgba(34,211,238,0.15),transparent_28%),radial-gradient(circle_at_90%_10%,rgba(52,211,153,0.12),transparent_30%),radial-gradient(circle_at_50%_90%,rgba(56,189,248,0.1),transparent_30%)]" />
          <Navbar />
          <main className="fade-in">{children}</main>
        </div>
      </body>
    </html>
  );
}
