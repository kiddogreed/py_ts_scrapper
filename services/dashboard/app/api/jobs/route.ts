import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import pool from "@/lib/db";
import scraperClient from "@/lib/scraper-client";
import logger from "@/lib/logger";

// GET /api/jobs?status=pending&limit=50&offset=0
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const status = searchParams.get("status");
    const limit = Math.min(Number(searchParams.get("limit") ?? "50"), 200);
    const offset = Number(searchParams.get("offset") ?? "0");

    const params: (string | number)[] = [];
    let where = "";
    if (status) {
      params.push(status);
      where = `WHERE status = $${params.length}`;
    }

    const countResult = await pool.query(
      `SELECT COUNT(*) FROM jobs ${where}`,
      params
    );
    const total = Number(countResult.rows[0].count);

    params.push(limit, offset);
    const jobsResult = await pool.query(
      `SELECT id, url, status, pattern, retries, max_retries,
              created_at, updated_at, metadata
       FROM jobs
       ${where}
       ORDER BY created_at DESC
       LIMIT $${params.length - 1} OFFSET $${params.length}`,
      params
    );

    return NextResponse.json({ jobs: jobsResult.rows, total });
  } catch (err) {
    logger.error({ err }, "GET /api/jobs error");
    return NextResponse.json({ error: "Failed to fetch jobs" }, { status: 500 });
  }
}

// POST /api/jobs — create job + dispatch scrape to FastAPI
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      url,
      pattern = "generic",
      metadata = {},
      javascript = true,
      wait_for,
      intercept_pattern,
    } = body;

    if (!url || typeof url !== "string") {
      return NextResponse.json({ error: "url is required" }, { status: 400 });
    }
    try {
      new URL(url);
    } catch {
      return NextResponse.json({ error: "Invalid URL" }, { status: 400 });
    }

    const jobId = randomUUID();

    await pool.query(
      `INSERT INTO jobs (id, url, status, pattern, metadata)
       VALUES ($1, $2, 'pending', $3, $4)`,
      [jobId, url, pattern, JSON.stringify(metadata)]
    );

    // Mark running, dispatch scrape (non-blocking)
    pool.query(
      `UPDATE jobs SET status = 'running', updated_at = NOW() WHERE id = $1`,
      [jobId]
    );

    scraperClient
      .post("/scrape/", {
        url,
        javascript,
        use_session: true,
        ...(wait_for && { wait_for }),
        ...(intercept_pattern && { intercept_pattern }),
      })
      .then(async (res) => {
        const resultId = randomUUID();
        await pool.query(
          `INSERT INTO results (id, job_id, url, data, scraped_at)
           VALUES ($1, $2, $3, $4, NOW())`,
          [
            resultId,
            jobId,
            url,
            JSON.stringify({
              html: res.data.html ?? "",
              status_code: res.data.status_code ?? 200,
              fingerprint_used: res.data.fingerprint_used ?? {},
              intercepted: res.data.intercepted ?? [],
            }),
          ]
        );
        await pool.query(
          `UPDATE jobs SET status = 'done', updated_at = NOW() WHERE id = $1`,
          [jobId]
        );
      })
      .catch(async (err) => {
        logger.error({ err, jobId }, "scrape dispatch failed");
        await pool.query(
          `UPDATE jobs
           SET status = 'failed', retries = retries + 1, updated_at = NOW()
           WHERE id = $1`,
          [jobId]
        );
      });

    const jobRow = await pool.query(
      `SELECT id, url, status, pattern, retries, max_retries,
              created_at, updated_at, metadata
       FROM jobs WHERE id = $1`,
      [jobId]
    );
    return NextResponse.json({ job: jobRow.rows[0] }, { status: 201 });
  } catch (err) {
    console.error("POST /api/jobs error:", err);
    return NextResponse.json({ error: "Failed to create job" }, { status: 500 });
  }
}
