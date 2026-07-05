"""CLI entry point: run any registered contest × district type combination.

Usage:
    python analyze.py measure-e council
    python analyze.py prop-36 supervisor --force
    python analyze.py --list
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

import map as mapviz
import pipeline
import report
from contests import CONTESTS, CONTESTS_BY_NAME, DISTRICT_TYPES, DISTRICT_TYPES_BY_NAME


def cmd_list() -> None:
    print("Available contests:")
    for c in CONTESTS:
        print(f"  {c.name:<20}  {c.label}")
    print()
    print("Available district types:")
    for d in DISTRICT_TYPES:
        print(f"  {d.name:<20}  {d.label}")


def cmd_run(contest_name: str, district_name: str, force: bool) -> None:
    if contest_name not in CONTESTS_BY_NAME:
        print(
            f"Unknown contest '{contest_name}'. "
            f"Run `python analyze.py --list` to see options.",
            file=sys.stderr,
        )
        sys.exit(1)
    if district_name not in DISTRICT_TYPES_BY_NAME:
        print(
            f"Unknown district type '{district_name}'. "
            f"Run `python analyze.py --list` to see options.",
            file=sys.stderr,
        )
        sys.exit(1)

    contest = CONTESTS_BY_NAME[contest_name]
    district = DISTRICT_TYPES_BY_NAME[district_name]

    print(f"==> {contest.label} by {district.label}")

    print("\n==> Downloading data...")
    results, districts = pipeline.run_analysis(contest, district, force=force)

    print("\n==> Results:")
    report.print_district_table(
        results,
        title=f"{contest.label} by {district.label}",
        choice_a_label=contest.choice_a_label,
        choice_b_label=contest.choice_b_label,
    )

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    stem = f"{contest.name}-by-{district.name}"

    report.save_csv(results, output_dir / f"{stem}.csv")
    report.save_text_table(
        results,
        output_dir / f"{stem}.txt",
        title=f"{contest.label} by {district.label}",
        choice_a_label=contest.choice_a_label,
        choice_b_label=contest.choice_b_label,
    )

    print("\n==> Generating map...")
    fig = mapviz.make_choropleth(
        results,
        districts,
        value_col="yes_pct",
        title=f"{contest.label}\nby {district.label}",
        cmap_colors=contest.cmap_colors,
        legend_label=contest.legend_label,
    )
    map_path = output_dir / f"{stem}_choropleth.png"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(map_path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {map_path}")
    plt.close(fig)

    print(f"\nDone. Outputs in {output_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stratify election results by political subdivision",
        epilog="Run with --list to see available contests and district types.",
    )
    parser.add_argument("contest", nargs="?", help="Contest slug (e.g. measure-e, prop-36)")
    parser.add_argument("district", nargs="?", help="District type slug (e.g. council, supervisor)")
    parser.add_argument("--force", action="store_true", help="Re-download all data files")
    parser.add_argument("--list", action="store_true", help="List available contests and district types")

    args = parser.parse_args()

    if args.list:
        cmd_list()
        return

    if not args.contest or not args.district:
        parser.print_help()
        sys.exit(1)

    cmd_run(args.contest, args.district, force=args.force)


if __name__ == "__main__":
    main()
