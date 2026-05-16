/**
 * Centralized structured logger for the Next.js dashboard (server-side only).
 *
 * WHY pino? It emits newline-delimited JSON to stdout — the same format used
 * by structlog on the Python side. Both streams can be collected by any log
 * aggregator (Loki, Datadog, CloudWatch) without extra parsing config.
 *
 * In development NODE_ENV the level defaults to "debug"; in production "info".
 * pino is safe to import in API routes (Node.js only) — never import in
 * client components.
 */
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL ?? (process.env.NODE_ENV === "production" ? "info" : "debug"),
  // Always emit plain JSON — Docker's json-file driver wraps it a second time,
  // but that outer envelope is stripped by most log aggregators.
  transport: process.env.NODE_ENV !== "production"
    ? {
        // Human-readable output for local dev; not used in production container
        target: "pino-pretty",
        options: { colorize: true, translateTime: "SYS:standard" },
      }
    : undefined,
  base: {
    service: "dashboard",
    env: process.env.NODE_ENV,
  },
  serializers: {
    err: pino.stdSerializers.err,
  },
});

export default logger;
