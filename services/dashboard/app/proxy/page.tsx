"use client";

import { useQuery } from "@tanstack/react-query";
import axios from "axios";

type ProxyStatus = {
  total: number;
  healthy: number;
  dead: number;
};

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 flex flex-col gap-2">
      <span className="text-xs text-gray-500 uppercase tracking-wide font-medium">
        {label}
      </span>
      <span className={`text-4xl font-bold font-mono ${color}`}>{value}</span>
    </div>
  );
}

export default function ProxyPage() {
  const { data, isLoading, error, dataUpdatedAt } = useQuery({
    queryKey: ["proxy-status"],
    queryFn: async () => {
      const res = await axios.get<ProxyStatus>("/api/proxy");
      return res.data;
    },
    refetchInterval: 10_000,
  });

  const healthPct =
    data && data.total > 0
      ? Math.round((data.healthy / data.total) * 100)
      : null;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Proxy Pool Health</h1>
        {dataUpdatedAt > 0 && (
          <span className="text-xs text-gray-600">
            Updated {new Date(dataUpdatedAt).toLocaleTimeString()}
          </span>
        )}
      </div>

      {isLoading && (
        <div className="text-gray-500 text-sm animate-pulse">Fetching proxy status…</div>
      )}

      {error && (
        <div className="bg-red-950 border border-red-800 rounded-lg p-4 text-red-400 text-sm">
          Failed to reach scraper API. Is it running?
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Total" value={data.total} color="text-white" />
            <StatCard
              label="Healthy"
              value={data.healthy}
              color={data.healthy > 0 ? "text-green-400" : "text-gray-500"}
            />
            <StatCard
              label="Dead"
              value={data.dead}
              color={data.dead > 0 ? "text-red-400" : "text-gray-500"}
            />
          </div>

          {/* Health bar */}
          {data.total > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Pool health</span>
                <span className="font-mono">{healthPct}%</span>
              </div>
              <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    (healthPct ?? 0) >= 80
                      ? "bg-green-500"
                      : (healthPct ?? 0) >= 40
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${healthPct ?? 0}%` }}
                />
              </div>
            </div>
          )}

          {data.total === 0 && (
            <div className="bg-yellow-950 border border-yellow-800 rounded-lg p-4 text-yellow-400 text-sm">
              No proxies configured. Add entries to{" "}
              <code className="font-mono text-yellow-300">
                shared/config/proxies.json
              </code>{" "}
              and restart the scraper API.
            </div>
          )}
        </>
      )}
    </div>
  );
}
