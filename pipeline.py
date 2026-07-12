"""Generic analysis pipeline: download → spatial join → votes → aggregate."""

from pathlib import Path
from typing import Tuple

import geopandas as gpd
import pandas as pd

import aggregate
import download
import spatial
from contests import ContestConfig, DistrictType


def run_analysis(
    contest: ContestConfig,
    district_type: DistrictType,
    force: bool = False,
) -> Tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """Run the full pipeline for a contest × district type combination.

    Returns (results_df, districts_gdf). The caller handles all I/O
    (printing, saving files, rendering maps)."""
    Path("data/raw").mkdir(parents=True, exist_ok=True)

    # --- shared downloads ---
    precinct_path = download.download_precinct_boundaries(
        contest.election, contest.county, force=force
    )
    svprec_map_path = download.download_svprec_map(
        contest.election, contest.county, force=force
    )

    # --- district boundaries ---
    if district_type.name == "council":
        district_path = download.download_council_districts(force=force)
        districts = spatial.load_council_districts(district_path, jurisdiction="SAN DIEGO")
    elif district_type.name == "supervisor":
        district_path = download.download_supervisor_districts(force=force)
        districts = spatial.load_supervisor_districts(district_path)
    else:
        raise ValueError(
            f"Unknown district type '{district_type.name}'. "
            f"Add a dispatch case in pipeline.py."
        )

    # --- precinct → district spatial join ---
    precincts = spatial.load_precinct_boundaries(precinct_path)
    district_map = spatial.assign_precincts_to_districts(precincts, districts)
    svprec_map = aggregate.load_svprec_map(svprec_map_path)

    # --- vote extraction ---
    if contest.source == "registrar_xls":
        xls_path = download.download_registrar_sov(contest.election_ym, force=force)
        sheet = aggregate.find_measure_sheet(xls_path, contest.search_label)
        print(f"  Found in sheet: {sheet}")
        votes_sv = aggregate.parse_measure_sheet(xls_path, sheet)
        print(f"  Parsed {len(votes_sv)} precincts from SOV XLS")
    elif contest.source == "swdb_data":
        sov_path = download.download_sov_data(contest.election, contest.county, force=force)
        votes_sv = aggregate.load_swdb_prop_votes(sov_path, contest.yes_col, contest.no_col)
        print(f"  Loaded {len(votes_sv)} precincts from SWDB SOV data")
    else:
        raise ValueError(
            f"Unknown contest source '{contest.source}'. "
            f"Must be 'registrar_xls' or 'swdb_data'."
        )

    # --- aggregate ---
    votes = aggregate.merge_svprec_to_srprec(votes_sv, svprec_map)
    merged = aggregate.merge_votes_with_districts(votes, district_map)
    results = aggregate.aggregate_by_district(merged)

    return results, districts
