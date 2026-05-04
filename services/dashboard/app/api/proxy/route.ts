import { NextResponse } from "next/server";
import scraperClient from "@/lib/scraper-client";

// GET /api/proxy — proxy status from FastAPI
export async function GET() {
  try {
    const res = await scraperClient.get("/proxy/status");
    return NextResponse.json(res.data);
  } catch (err) {
    console.error("GET /api/proxy error:", err);
    return NextResponse.json(
      { error: "Failed to reach scraper API" },
      { status: 502 }
    );
  }
}
