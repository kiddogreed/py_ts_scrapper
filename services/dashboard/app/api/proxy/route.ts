import { NextResponse } from "next/server";
import scraperClient from "@/lib/scraper-client";
import logger from "@/lib/logger";

// GET /api/proxy — proxy status from FastAPI
export async function GET() {
  try {
    const res = await scraperClient.get("/proxy/status");
    return NextResponse.json(res.data);
  } catch (err) {
    logger.error({ err }, "GET /api/proxy error");
    return NextResponse.json(
      { error: "Failed to reach scraper API" },
      { status: 502 }
    );
  }
}
