"""Command-line entry point: ``python -m hunger_screening.cli [all|analysis|figures|tables|dashboard-data|investigation]``.

``investigation`` (World Bank HFPS external analyses + Aggarwal extensions + their figures)
needs the World Bank archive extracted locally; ``all`` runs it only when that data exists.
"""

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
    ap.add_argument("step", nargs="?", default="all",
                    choices=["all", "analysis", "figures", "tables", "dashboard-data", "investigation"])
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
    if args.step in ("all", "investigation"):
        from .hfps import load_investigation_config

        extracted = paths.root / load_investigation_config(paths)["hfps"]["extracted_dir"]
        if not extracted.exists():
            if args.step == "investigation":
                print(f"investigation: World Bank data not found at {extracted.relative_to(paths.root)}")
                return 1
            print("investigation: skipped (World Bank data not present)")
            return 0
        from . import extensions, hfps
        from .investigation_figures import render_investigation

        hfps.run(paths)
        extensions.run(paths)
        from . import review_responses

        review_responses.run(paths)
        if (paths.root / "data" / "raw" / "multicountry").exists():
            from . import multicountry

            multicountry.run(paths)
        print(f"investigation: outputs written; {len(render_investigation(paths.public, paths.figures))} figure files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
