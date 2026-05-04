"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import Link from "next/link";
import { useState } from "react";

type Job = {
  id: string;
  url: string;
  status: "pending" | "running" | "done" | "failed" | "dead";
  pattern: string | null;
  retries: number;
  max_retries: number;
  created_at: string;
  updated_at: string;
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

function truncate(str: string, n = 60) {
  return str.length > n ? str.slice(0, n) + "…" : str;
}

function relative(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  return `${Math.floor(diff / 3_600_000)}h ago`;
}

export default function JobsPage() {
  const qc = useQueryClient();
  const [url, setUrl] = useState("");
  const [pattern, setPattern] = useState("generic");
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["jobs", statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: "50" });
      if (statusFilter) params.set("status", statusFilter);
      const res = await axios.get<{ jobs: Job[]; total: number }>(
        `/api/jobs?${params}`
      );
      return res.data;
    },
    refetchInterval: 5_000,
  });

  const create = useMutation({
    mutationFn: (payload: { url: string; pattern: string }) =>
      axios.post("/api/jobs", payload),
    onSuccess: () => {
      setUrl("");
      setError(null);
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (err: unknown) => {
      const msg =
        axios.isAxiosError(err)
          ? err.response?.data?.error ?? err.message
          : "Unknown error";
      setError(String(msg));
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    create.mutate({ url: url.trim(), pattern });
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Scrape Jobs</h1>
        {isFetching && !isLoading && (
          <span className="text-xs text-gray-500 animate-pulse">refreshing…</span>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col gap-3"
      >
        <h2 className="text-sm font-semibold text-gray-300">New Scrape Job</h2>
        <div className="flex gap-3">
          <input
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <select
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="generic">generic</option>
            <option value="microservice">microservice</option>
            <option value="polyglot">polyglot</option>
            <option value="n8n">n8n</option>
          </select>
          <button
            type="submit"
            disabled={create.isPending}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-400 text-white rounded text-sm font-medium transition-colors"
          >
            {create.isPending ? "Dispatching…" : "Scrape"}
          </button>
        </div>
        {error && <p className="text-red-400 text-xs">{error}</p>}
      </form>

      <div className="flex gap-2 text-xs">
        {["", "pending", "running", "done", "failed", "dead"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded border transition-colors ${
              statusFilter === s
                ? "bg-gray-700 border-gray-500 text-white"
                : "bg-gray-900 border-gray-700 text-gray-400 hover:text-white"
            }`}
          >
            {s || "all"}
          </button>
        ))}
        {data && (
          <span className="ml-auto text-gray-500 self-center">{data.total} total</span>
        )}
      </div>

      {isLoading ? (
        <div className="text-gray-500 text-sm animate-pulse">Loading…</div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900 text-gray-400 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 text-left">ID</th>
                <th className="px-4 py-3 text-left">URL</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Pattern</th>
                <th className="px-4 py-3 text-left">Retries</th>
                <th className="px-4 py-3 text-left">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {data?.jobs.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-600">
                    No jobs yet. Submit one above.
                  </td>
                </tr>
              )}
              {data?.jobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-900/60 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">
                    <Link
                      href={`/jobs/${job.id}`}
                      className="hover:text-blue-400 underline underline-offset-2"
                    >
                      {job.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-300 max-w-xs truncate" title={job.url}>
                    <Link href={`/jobs/${job.id}`} className="hover:text-blue-400">
                      {truncate(job.url, 55)}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">
                    {job.pattern ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {job.retries}/{job.max_retries}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs" title={job.created_at}>
                    {relative(job.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
