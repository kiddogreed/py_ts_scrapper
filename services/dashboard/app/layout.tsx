import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import QueryProvider from "@/components/QueryProvider";
import Link from "next/link";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Scraper Dashboard",
  description: "Production-grade stealth scraping infrastructure",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-gray-950 text-gray-100">
        <QueryProvider>
          <nav className="border-b border-gray-800 bg-gray-900 px-6 py-3 flex items-center gap-6 text-sm">
            <span className="font-bold text-white tracking-tight">
              ⚡ Scraper
            </span>
            <Link
              href="/"
              className="text-gray-400 hover:text-white transition-colors"
            >
              Jobs
            </Link>
            <Link
              href="/proxy"
              className="text-gray-400 hover:text-white transition-colors"
            >
              Proxies
            </Link>
          </nav>
          <main className="flex-1 p-6">{children}</main>
        </QueryProvider>
      </body>
    </html>
  );
}
