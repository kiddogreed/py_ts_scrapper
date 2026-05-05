# pipeline/parser/main.py
"""
Polyglot Pipeline — Python Parser Stage

Reads a NavigateResult JSON produced by the TypeScript navigator,
parses the HTML using the appropriate extractor, and writes the
structured result to Postgres and stdout.

Usage:
    # From stdin (pipe from TypeScript navigator):
    ts-node index.ts https://example.com | python main.py

    # From file:
    python main.py /tmp/navigate_result.json

    # Specify extractor type:
    python main.py /tmp/navigate_result.json --extractor product
"""
import sys
import json
import asyncio
import asyncpg
import os
import argparse
import logging
from extractors.product import ProductExtractor
from extractors.base import BaseExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("parser.main")

EXTRACTOR_MAP: dict[str, type[BaseExtractor]] = {
    "product": ProductExtractor,
}


def get_extractor(name: str) -> BaseExtractor:
    cls = EXTRACTOR_MAP.get(name)
    if cls is None:
        raise ValueError(f"Unknown extractor '{name}'. Available: {list(EXTRACTOR_MAP)}")
    return cls()


async def write_to_db(navigate_result: dict, structured_data: dict) -> None:
    """Persist result to Postgres. Skips gracefully if DATABASE_URL is unset."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set — skipping Postgres write")
        return

    conn = await asyncpg.connect(database_url)
    try:
        job_id = navigate_result.get("job_id") or structured_data.get("job_id")
        await conn.execute(
            """
            INSERT INTO results (job_id, url, data, scraped_at)
            VALUES ($1, $2, $3, $4)
            """,
            job_id,
            navigate_result["url"],
            json.dumps(structured_data),
            navigate_result.get("timestamp"),
        )
        logger.info("Result written to Postgres for url=%s", navigate_result["url"])
    finally:
        await conn.close()


async def run(navigate_result: dict, extractor_name: str = "product") -> dict:
    extractor = get_extractor(extractor_name)

    structured_data = extractor.extract(
        html=navigate_result["html"],
        source_url=navigate_result["url"],
        intercepted=navigate_result.get("interceptedRequests", []),
    )

    await write_to_db(navigate_result, structured_data)

    return structured_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a NavigateResult JSON into structured product data."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to NavigateResult JSON file. Reads stdin if omitted.",
    )
    parser.add_argument(
        "--extractor",
        default="product",
        choices=list(EXTRACTOR_MAP),
        help="Extractor to use (default: product)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.input_file:
        with open(args.input_file) as f:
            navigate_result = json.load(f)
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            logger.error("No input received on stdin and no file argument provided.")
            sys.exit(1)
        navigate_result = json.loads(raw)

    result = asyncio.run(run(navigate_result, args.extractor))

    # Output structured data to stdout for downstream consumers (n8n, etc.)
    print(json.dumps(result, indent=2))
