"""CLI entrypoint: ``python -m collector <command>``.

Commands:
    run       collect -> store -> enrich (the main flow)
    serve     start the FastAPI server (uvicorn)
    seed      load the bundled sample/seed dataset into the database
    estimate  re-run salary estimation over stored postings missing salary
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from .config import get_settings
from .pipeline import enrich, run_pipeline, seed_only
from .sources import available_sources


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def _cmd_run() -> int:
    summary = await run_pipeline()
    print(
        f"Done. collected={summary['collected']} "
        f"enriched={summary['enriched']} total_in_db={summary['total_in_db']}"
    )
    return 0


async def _cmd_seed() -> int:
    count = await seed_only()
    print(f"Seeded {count} postings into the database.")
    return 0


async def _cmd_estimate() -> int:
    enriched = await enrich(get_settings())
    print(f"Enriched {enriched} postings.")
    return 0


def _cmd_serve() -> int:
    import uvicorn

    settings = get_settings()
    print(f"Serving API on http://{settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "collector.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="collector", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Collect, store, and enrich postings.")
    sub.add_parser("serve", help="Start the FastAPI server.")
    sub.add_parser("seed", help="Load the bundled seed dataset.")
    sub.add_parser("estimate", help="Estimate salaries for stored postings.")
    sub.add_parser("sources", help="List registered source adapters.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _configure_logging(args.verbose)

    if args.command == "run":
        return asyncio.run(_cmd_run())
    if args.command == "seed":
        return asyncio.run(_cmd_seed())
    if args.command == "estimate":
        return asyncio.run(_cmd_estimate())
    if args.command == "sources":
        print("Registered sources:", ", ".join(available_sources()))
        return 0
    if args.command == "serve":
        return _cmd_serve()
    return 1


if __name__ == "__main__":
    sys.exit(main())
