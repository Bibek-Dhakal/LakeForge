"""`lakeforge` command line interface."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .settings import Settings
from .stages import ALL_STAGES


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lakeforge", description="LakeForge lakehouse pipelines")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("seed-db", help="create the SQLite reference source from the public zone lookup")

    p = sub.add_parser("stage", help="run one stage for one month")
    p.add_argument("name", choices=ALL_STAGES)
    p.add_argument("--month", required=True, help="YYYY-MM")

    p = sub.add_parser("run", help="run all stages for a month range (backfill)")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--stages", nargs="*", choices=ALL_STAGES, default=list(ALL_STAGES))

    p = sub.add_parser("verify", help="re-run bronze->gold twice and compare table fingerprints")
    p.add_argument("--month", required=True)

    p = sub.add_parser("benchmark", help="run the pipeline at several data scales")
    p.add_argument("--months", nargs="+", type=int, default=[1, 3])
    p.add_argument("--first-month", default="2024-01")

    sub.add_parser("catalog", help="regenerate the catalog + lineage docs under <lake>/meta")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = Settings.from_env()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    if args.cmd == "seed-db":
        from .ingest.database import seed_source_db

        print(f"seeded {seed_source_db(settings)} zones into {settings.source_db_path}")
    elif args.cmd == "stage":
        from .pipeline import run_stage

        run_stage(settings, args.name, args.month)
    elif args.cmd == "run":
        from .pipeline import run_range

        done = run_range(settings, args.start, args.end, stages=tuple(args.stages))
        print(f"processed batches: {', '.join(done)}")
    elif args.cmd == "verify":
        from .evaluation import verify_idempotency

        result = verify_idempotency(settings, args.month)
        print(json.dumps(result, indent=2))
        return 0 if result["identical"] else 1
    elif args.cmd == "benchmark":
        from .evaluation import run_benchmark

        print(json.dumps(run_benchmark(settings, args.months, args.first_month), indent=2))
    elif args.cmd == "catalog":
        from .catalog import write_catalog

        write_catalog(settings)
        print(f"catalog written to {settings.meta_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
