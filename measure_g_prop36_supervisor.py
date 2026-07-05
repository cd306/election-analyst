"""
SD County Measure G (Public Safety / Health Services Sales Tax, Nov 2024)
and CA Prop 36 (Drug & Theft Crime Sentences) results stratified by
SD County Supervisor District.

Usage:
    python measure_g_prop36_supervisor.py           # uses cached data
    python measure_g_prop36_supervisor.py --force   # re-download all data

Outputs:
    outputs/measure_g_by_supervisor.csv / .txt / _choropleth.png
    outputs/prop36_by_supervisor.csv / .txt / _choropleth.png
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

MEASURE_G_LABEL = "MEASURE G"
MEASURE_G_TITLE = "SD County Measure G (Sales Tax) — Nov 2024 Results by Supervisor District"

PROP36_YES_COL = "PR_36_Y"
PROP36_NO_COL = "PR_36_N"
PROP36_TITLE = "CA Prop 36 (Drug & Theft Sentences) — Nov 2024 Results by SD Supervisor District"


def _run_analysis(
    name: str,
    title: str,
    votes_sv,
    svprec_map,
    district_map,
    districts,
    output_prefix: str,
) -> None:
    print(f"\n==> Aggregating {name} by supervisor district...")
    votes = aggregate.merge_svprec_to_srprec(votes_sv, svprec_map)
    merged = aggregate.merge_votes_with_districts(votes, district_map)
    results = aggregate.aggregate_by_district(merged)

    print(f"\n==> {name} Results:")
    report.print_district_table(results, title=title)
    report.save_csv(results, Path(f"outputs/{output_prefix}_by_supervisor.csv"))
    report.save_text_table(
        results, Path(f"outputs/{output_prefix}_by_supervisor.txt"), title=title
    )

    print(f"\n==> Generating {name} map...")
    mapviz.make_choropleth(
        results,
        districts,
        value_col="yes_pct",
        title=title,
        output_path=Path(f"outputs/{output_prefix}_by_supervisor_choropleth.png"),
        legend_label="Yes %",
    )


def run(force: bool = False) -> None:
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("outputs").mkdir(parents=True, exist_ok=True)

    print("==> Downloading data...")
    xls_path = download.download_registrar_sov(force=force)
    precinct_path = download.download_precinct_boundaries(ELECTION, COUNTY, force=force)
    svprec_map_path = download.download_svprec_map(ELECTION, COUNTY, force=force)
    sov_data_path = download.download_sov_data(ELECTION, COUNTY, force=force)
    supervisor_path = download.download_supervisor_districts(force=force)

    print("\n==> Building precinct-to-supervisor-district map...")
    precincts = spatial.load_precinct_boundaries(precinct_path)
    districts = spatial.load_supervisor_districts(supervisor_path)
    district_map = spatial.assign_precincts_to_districts(precincts, districts)

    svprec_map = aggregate.load_svprec_map(svprec_map_path)

    # --- Measure G ---
    print("\n==> Extracting Measure G votes from SOV XLS...")
    sheet = aggregate.find_measure_sheet(xls_path, MEASURE_G_LABEL)
    print(f"  Found in sheet: {sheet}")
    votes_g = aggregate.parse_measure_sheet(xls_path, sheet)
    print(f"  Parsed {len(votes_g)} precincts from SOV")
    _run_analysis(
        "Measure G", MEASURE_G_TITLE, votes_g, svprec_map, district_map,
        districts, "measure_g"
    )

    # --- Prop 36 ---
    print("\n==> Extracting Prop 36 votes from SWDB SOV data...")
    votes_36 = aggregate.load_swdb_prop_votes(sov_data_path, PROP36_YES_COL, PROP36_NO_COL)
    print(f"  Loaded {len(votes_36)} precincts from SWDB SOV data")
    _run_analysis(
        "Prop 36", PROP36_TITLE, votes_36, svprec_map, district_map,
        districts, "prop36"
    )

    print("\nDone. Outputs in outputs/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute Measure G and Prop 36 results by SD County Supervisor District"
    )
    parser.add_argument("--force", action="store_true", help="Re-download data files")
    args = parser.parse_args()
    run(force=args.force)
