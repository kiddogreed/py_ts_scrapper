// pipeline/navigator/index.ts
/**
 * Polyglot Pipeline — Navigator Entry Point
 *
 * CLI usage:
 *   ts-node index.ts <url> [options]
 *
 * Options:
 *   --output <file>     Write result JSON to file (default: stdout)
 *   --wait-for <sel>    CSS selector to wait for before capturing
 *   --intercept <pat>   URL pattern to intercept XHR/fetch responses
 *   --timeout <ms>      Navigation timeout in ms (default: 30000)
 *
 * Examples:
 *   ts-node index.ts https://example.com
 *   ts-node index.ts https://example.com --output /tmp/result.json
 *   ts-node index.ts https://spa.example.com --intercept /api/products --wait-for .product-list
 *
 * The output JSON is a NavigateResult object consumed by pipeline/parser/main.py
 */
import { navigateAndExtract, NavigateOptions } from "./actions/navigate";

function parseArgs(argv: string[]): { url: string; options: NavigateOptions } {
  const args = argv.slice(2);
  const url = args[0];

  if (!url || url.startsWith("--")) {
    process.stderr.write(
      "Usage: ts-node index.ts <url> [--output file] [--wait-for selector] [--intercept pattern] [--timeout ms]\n"
    );
    process.exit(1);
  }

  const options: NavigateOptions = {};

  for (let i = 1; i < args.length; i++) {
    switch (args[i]) {
      case "--output":
        options.outputFile = args[++i];
        break;
      case "--wait-for":
        options.waitForSelector = args[++i];
        break;
      case "--intercept":
        options.interceptPattern = args[++i];
        break;
      case "--timeout":
        options.timeoutMs = parseInt(args[++i], 10);
        break;
      default:
        process.stderr.write(`Unknown option: ${args[i]}\n`);
        process.exit(1);
    }
  }

  return { url, options };
}

const { url, options } = parseArgs(process.argv);

navigateAndExtract(url, options).catch((err) => {
  process.stderr.write(`Navigator error: ${String(err)}\n`);
  process.exit(1);
});
