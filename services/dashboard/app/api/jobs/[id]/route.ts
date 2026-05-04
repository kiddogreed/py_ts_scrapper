import { NextRequest, NextResponse } from "next/server";
import pool from "@/lib/db";

type Params = { params: Promise<{ id: string }> };

// GET /api/jobs/[id]
export async function GET(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;

    // Validate UUID format to prevent SQL injection
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    const jobResult = await pool.query(
      `SELECT id, url, status, pattern, retries, max_retries,
              created_at, updated_at, metadata
       FROM jobs WHERE id = $1`,
      [id]
    );

    if (jobResult.rows.length === 0) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    const resultsResult = await pool.query(
      `SELECT id, url, data, scraped_at, created_at
       FROM results WHERE job_id = $1
       ORDER BY created_at DESC`,
      [id]
    );

    return NextResponse.json({
      job: jobResult.rows[0],
      results: resultsResult.rows,
    });
  } catch (err) {
    console.error("GET /api/jobs/[id] error:", err);
    return NextResponse.json({ error: "Failed to fetch job" }, { status: 500 });
  }
}

// DELETE /api/jobs/[id]
export async function DELETE(_req: NextRequest, { params }: Params) {
  try {
    const { id } = await params;

    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    const result = await pool.query(
      `DELETE FROM jobs WHERE id = $1 RETURNING id`,
      [id]
    );

    if (result.rows.length === 0) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    return NextResponse.json({ deleted: id });
  } catch (err) {
    console.error("DELETE /api/jobs/[id] error:", err);
    return NextResponse.json({ error: "Failed to delete job" }, { status: 500 });
  }
}
