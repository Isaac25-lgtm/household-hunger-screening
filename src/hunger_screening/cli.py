"""Command-line entry point: ``python -m hunger_screening.cli [all|analysis|figures|tables|dashboard-data]``."""

from __future__ import annotations

import argparse
import shutil
import sys

from .config import Paths


def dashboard_data(paths: Paths) -> None:
    """Copy audited aggregate CSV/JSON files used by the dashboard (no microdata)."""
    paths.dashboard_data.mkdir(parents=True, exist_ok=True)
    for p in paths.public.glob("*"):
        if p.suffix in {".csv", ".json"}:
            shutil.copy2(p, paths.dashboard_data / p.name)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hunger-screening")
    ap.add_argument("step", nargs="?", default="all", choices=["all", "analysis", "figures", "tables", "dashboard-data"])
    ap.add_argument("--no-download", action="store_true", help="fail instead of downloading the source archive")
    args = ap.parse_args(argv)
    paths = Paths()
    if args.step in ("all", "analysis"):
        from .pipeline import run

        s = run(paths, allow_download=not args.no_download)
        print(f"analysis: reproduction {s['reproduction']['n_pass']}/{s['reproduction']['n_checks']} pass; "
              f"{s['runtime_seconds']} s")
    if args.step in ("all", "figures"):
        from .generate_figures import render_all

        print(f"figures: {len(render_all(paths.public, paths.figures))} files")
    if args.step in ("all", "tables"):
        from .generate_tables import build_tables

        print(f"tables: {len(build_tables(paths.public, paths.tables))} tables")
    if args.step in ("all", "dashboard-data"):
        dashboard_data(paths)
        print("dashboard data refreshed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
