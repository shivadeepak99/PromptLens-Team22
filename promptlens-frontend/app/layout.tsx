import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";
import Navbar from "@/components/Navbar";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PromptLens Data Warehouse",
  description: "Enterprise prompt analytics dashboard, ML analyzer, and reporting.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} h-full antialiased bg-slate-900`}>
      <body className="min-h-full text-slate-100 flex flex-col">
        <Navbar />
        <main className="flex-1 fade-in w-full">{children}</main>
      </body>
    </html>
  );
}
