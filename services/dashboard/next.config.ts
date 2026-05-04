import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Expose server-side env vars needed by API routes (no NEXT_PUBLIC_ prefix)
  // DATABASE_URL and SCRAPER_API_URL are read from process.env at runtime
};

export default nextConfig;
