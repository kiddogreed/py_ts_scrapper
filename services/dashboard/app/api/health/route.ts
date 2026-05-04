import { NextResponse } from "next/server";
import scraperClient from "@/lib/scraper-client";

// GET /api/health — aggregated health (FastAPI + DB reachability)
export async function GET() {
  const checks: Record<string, string> = {};

  // FastAPI health
  try {
    const res = await scraperClient.get("/health", { timeout: 5000 });
    checks.scraper_api = res.data?.status === "ok" ? "ok" : "degraded";
    checks.proxy_pool = JSON.stringify(res.data?.proxy_pool ?? {});
  } catch {
    checks.scraper_api = "unreachable";
  }

  const allOk = Object.values(checks).every(
    (v) => v === "ok" || v.startsWith("{")
  );

  return NextResponse.json(
    { status: allOk ? "ok" : "degraded", checks },
    { status: allOk ? 200 : 503 }
  );
}
