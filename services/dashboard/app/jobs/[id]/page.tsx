"use client";

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import Link from "next/link";
import { useParams } from "next/navigation";

type Job = {
  id: string;
  url: string;
  status: string;
  pattern: string | null;
  retries: number;
  max_retries: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
};

type JobResult = {
  id: string;
  url: string;
  data: {
    html?: string;
    status_code?: number;
    fingerprint_used?: Record<string, unknown>;
    intercepted?: unknown[];
  };
  scraped_at: string;
  created_at: string;
};

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-yellow-900 text-yellow-300 border-yellow-700",
  running: "bg-blue-900 text-blue-300 border-blue-700",
  done: "bg-green-900 text-green-300 border-green-700",
  failed: "bg-red-900 text-red-300 border-red-700",
  dead: "bg-gray-800 text-gray-400 border-gray-600",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${STATUS_STYLES[status] ?? "bg-gray-800 text-gray-400 border-gray-600"}`}
    >
      {status}
    </span>
  );
}

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-4 py-2 border-b border-gray-800 last:border-0">
      <span className="w-32 shrink-0 text-gray-500 text-xs uppercase tracking-wide font-medium">
        {label}
      </span>
      <span className="text-gray-200 text-sm font-mono break-all">{value}</span>
    </div>
  );
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ["job", id],
    queryFn: async () => {
      const res = await axios.get<{ job: Job; results: JobResult[] }>(
        `/api/jobs/${id}`
      );
      return res.data;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.job?.status;
      return status === "pending" || status === "running" ? 3_000 : false;
    },
    enabled: Boolean(id),
  });

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto text-gray-500 text-sm animate-pulse py-12">
        Loading job…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto">
        <p className="text-red-400 text-sm">Job not found or failed to load.</p>
        <Link href="/" className="text-blue-400 text-sm hover:underline mt-2 block">
          ← Back to jobs
        </Link>
      </div>
    );
  }

  const { job, results } = data;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back + header */}
      <div>
        <Link
          href="/"
          className="text-gray-500 hover:text-gray-300 text-sm transition-colors"
        >
          ← Jobs
        </Link>
        <div className="flex items-center gap-3 mt-3">
          <h1 className="text-xl font-bold font-mono">{id}</h1>
          <StatusBadge status={job.status} />
        </div>
      </div>

      {/* Job metadata */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Job Details
        </h2>
        <MetaRow label="URL" value={job.url} />
        <MetaRow label="Pattern" value={job.pattern ?? "—"} />
        <MetaRow label="Retries" value={`${job.retries} / ${job.max_retries}`} />
        <MetaRow label="Created" value={new Date(job.created_at).toLocaleString()} />
        <MetaRow label="Updated" value={new Date(job.updated_at).toLocaleString()} />
        {Object.keys(job.metadata).length > 0 && (
          <MetaRow
            label="Metadata"
            value={
              <pre className="text-xs text-gray-400 whitespace-pre-wrap">
                {JSON.stringify(job.metadata, null, 2)}
              </pre>
            }
          />
        )}
      </div>

      {/* Results */}
      <div>
        <h2 className="text-sm font-semibold text-gray-300 mb-3">
          Results ({results.length})
        </h2>

        {results.length === 0 && job.status !== "done" && (
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-600 text-sm">
            {job.status === "pending" || job.status === "running"
              ? "Scrape in progress…"
              : "No results recorded."}
          </div>
        )}

        {results.map((r) => (
          <div
            key={r.id}
            className="bg-gray-900 border border-gray-800 rounded-lg mb-4 overflow-hidden"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 text-xs text-gray-500">
              <span className="font-mono">{r.id.slice(0, 8)}</span>
              <span>
                HTTP {r.data?.status_code ?? "—"} ·{" "}
                {r.scraped_at
                  ? new Date(r.scraped_at).toLocaleString()
                  : "no timestamp"}
              </span>
            </div>

            {/* Fingerprint */}
            {r.data?.fingerprint_used &&
              Object.keys(r.data.fingerprint_used).length > 0 && (
                <details className="border-b border-gray-800">
                  <summary className="px-4 py-2 text-xs text-gray-500 cursor-pointer hover:text-gray-300 select-none">
                    Fingerprint used
                  </summary>
                  <pre className="px-4 py-3 text-xs text-gray-400 overflow-x-auto">
                    {JSON.stringify(r.data.fingerprint_used, null, 2)}
                  </pre>
                </details>
              )}

            {/* Intercepted XHR */}
            {Array.isArray(r.data?.intercepted) &&
              r.data.intercepted.length > 0 && (
                <details className="border-b border-gray-800">
                  <summary className="px-4 py-2 text-xs text-gray-500 cursor-pointer hover:text-gray-300 select-none">
                    Intercepted responses ({r.data.intercepted.length})
                  </summary>
                  <pre className="px-4 py-3 text-xs text-gray-400 overflow-x-auto max-h-64">
                    {JSON.stringify(r.data.intercepted, null, 2)}
                  </pre>
                </details>
              )}

            {/* HTML preview */}
            {r.data?.html && (
              <details>
                <summary className="px-4 py-2 text-xs text-gray-500 cursor-pointer hover:text-gray-300 select-none">
                  HTML ({r.data.html.length.toLocaleString()} chars)
                </summary>
                <pre className="px-4 py-3 text-xs text-gray-400 overflow-x-auto max-h-96 whitespace-pre-wrap">
                  {r.data.html.slice(0, 8_000)}
                  {r.data.html.length > 8_000 && "\n… [truncated]"}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
