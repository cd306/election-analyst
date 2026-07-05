"""
San Diego Measure E (Public Services Sales Tax, Nov 2024)
Results stratified by City Council District.

Usage:
    python measure_e.py           # downloads data if not present, runs full pipeline
    python measure_e.py --force   # re-download all data files

Output:
    outputs/measure_e_by_district.csv
    outputs/measure_e_by_district.txt
    outputs/measure_e_choropleth.png
"""

import argparse
from pathlib import Path

import download
import spatial
import aggregate
import report
import map as mapviz

ELECTION = "G24"
COUNTY = "073"
MEASURE_LABEL = "CITY OF SAN DIEGO - MEASURE E"
TITLE = "San Diego Measure E (Sales Tax) — Nov 2024 Results by Council District"


def run(force: bool = False) -> None:
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("outputs").mkdir(parents=True, exist_ok=True)

    print("==> Downloading data...")
    xls_path = download.download_registrar_sov(force=force)
    precinct_path = download.download_precinct_boundaries(ELECTION, COUNTY, force=force)
    svprec_map_path = download.download_svprec_map(ELECTION, COUNTY, force=force)
    district_path = download.download_council_districts(force=force)

    print("\n==> Building precinct-to-district map...")
    precincts = spatial.load_precinct_boundaries(precinct_path)
    districts = spatial.load_council_districts(district_path, jurisdiction="SAN DIEGO")
    district_map = spatial.assign_precincts_to_districts(precincts, districts)

    print("\n==> Extracting Measure E votes from SOV...")
    sheet = aggregate.find_measure_sheet(xls_path, MEASURE_LABEL)
    print(f"  Found in sheet: {sheet}")
    votes_sv = aggregate.parse_measure_sheet(xls_path, sheet)
    print(f"  Parsed {len(votes_sv)} precincts from SOV")

    svprec_map = aggregate.load_svprec_map(svprec_map_path)
    votes = aggregate.merge_svprec_to_srprec(votes_sv, svprec_map)

    print("\n==> Aggregating by district...")
    merged = aggregate.merge_votes_with_districts(votes, district_map)
    results = aggregate.aggregate_by_district(merged)

    print("\n==> Results:")
    report.print_district_table(results, title=TITLE)
    report.save_csv(results, Path("outputs/measure_e_by_district.csv"))
    report.save_text_table(results, Path("outputs/measure_e_by_district.txt"), title=TITLE)

    print("\n==> Generating map...")
    mapviz.make_choropleth(
        results,
        districts,
        value_col="yes_pct",
        title=TITLE,
        output_path=Path("outputs/measure_e_choropleth.png"),
    )

    print("\nDone. Outputs in outputs/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute Measure E results by SD City Council district"
    )
    parser.add_argument("--force", action="store_true", help="Re-download data files")
    args = parser.parse_args()
    run(force=args.force)
