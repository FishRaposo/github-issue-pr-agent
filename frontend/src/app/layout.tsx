import type { Metadata } from "next";
import { Inter } from "next/font/google";
import ErrorBoundary from "@/components/ErrorBoundary";
import NavBar from "@/components/NavBar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Issue → PR Console",
  description:
    "Operator console for the GitHub Issue-to-PR agent: process issues, watch the issue → plan → edit → tests → draft-PR pipeline, gate approvals, and audit every action under a strict safety model.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} min-h-screen bg-ink-50 font-sans text-ink-900 antialiased`}
      >
        <NavBar />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </body>
    </html>
  );
}
