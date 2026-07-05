"""Spatial operations: load precinct/district boundaries and assign precincts to districts."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

# California Albers — accurate for centroid computation
_CA_CRS = "EPSG:3310"
# WGS84 — used by both downloaded GeoJSON files
_WGS84 = "EPSG:4326"


def _normalize_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Uppercase all non-geometry columns; keep active geometry column as 'geometry'."""
    geom_col = gdf.geometry.name
    rename = {c: (c.upper() if c != geom_col else "geometry") for c in gdf.columns}
    gdf = gdf.rename(columns=rename)
    if geom_col != "geometry":
        gdf = gdf.set_geometry("geometry")
    return gdf


def load_precinct_boundaries(path: Path) -> gpd.GeoDataFrame:
    """Load SR precinct GeoJSON. Returns GeoDataFrame with [SRPREC, geometry]."""
    gdf = _normalize_columns(gpd.read_file(path))
    if "SRPREC" not in gdf.columns:
        candidates = [c for c in gdf.columns if "PREC" in c or "ID" in c]
        raise KeyError(
            f"Expected 'SRPREC' column in precinct file. Found: {candidates}"
        )
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(_WGS84)
    return gdf[["SRPREC", "geometry"]]


def load_council_districts(
    path: Path, jurisdiction: str = "SAN DIEGO"
) -> gpd.GeoDataFrame:
    """Load council districts GeoJSON filtered to the given JUR_NAME.
    Returns GeoDataFrame with [district_num, geometry]."""
    gdf = _normalize_columns(gpd.read_file(path))
    if "JUR_NAME" not in gdf.columns or "DISTRICT" not in gdf.columns:
        raise KeyError(
            f"Expected 'JUR_NAME' and 'DISTRICT' columns. Found: {list(gdf.columns)}"
        )
    filtered = gdf[gdf["JUR_NAME"].str.upper() == jurisdiction.upper()].copy()
    if filtered.empty:
        available = gdf["JUR_NAME"].unique().tolist()
        raise ValueError(
            f"No districts found for jurisdiction '{jurisdiction}'. "
            f"Available: {available}"
        )
    filtered["district_num"] = filtered["DISTRICT"].astype(int)
    if filtered.crs is None or filtered.crs.to_epsg() != 4326:
        filtered = filtered.to_crs(_WGS84)
    print(f"INFO: Loaded {len(filtered)} council districts for {jurisdiction}")
    return filtered[["district_num", "geometry"]]


def load_supervisor_districts(path: Path) -> gpd.GeoDataFrame:
    """Load SD County Supervisor District GeoJSON.
    Returns GeoDataFrame with [district_num, geometry]."""
    gdf = gpd.read_file(path)
    if "distno" not in gdf.columns:
        raise KeyError(
            f"Expected 'distno' column in supervisor districts file. Found: {list(gdf.columns)}"
        )
    gdf = gdf[["distno", "geometry"]].copy()
    gdf["district_num"] = gdf["distno"].astype(int)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(_WGS84)
    print(f"INFO: Loaded {len(gdf)} supervisor districts")
    return gdf[["district_num", "geometry"]]


def assign_precincts_to_districts(
    precincts: gpd.GeoDataFrame, districts: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Assign each precinct to a district via centroid point-in-polygon join.

    Reprojects to CA Albers (EPSG:3310) for accurate centroid computation,
    then reprojects back to WGS84 for the spatial join.
    Returns DataFrame with columns [SRPREC, district_num].
    Logs any precincts that have no district match."""
    # Compute centroids in projected CRS for accuracy
    precincts_proj = precincts.to_crs(_CA_CRS)
    centroids = gpd.GeoDataFrame(
        precincts[["SRPREC"]].copy(),
        geometry=precincts_proj.geometry.centroid.to_crs(_WGS84),
        crs=_WGS84,
    )

    # Point-in-polygon spatial join
    districts_wgs = districts.to_crs(_WGS84)
    joined = gpd.sjoin(centroids, districts_wgs, how="left", predicate="within")

    # Rename and clean up
    result = joined[["SRPREC", "district_num"]].copy()

    unmatched = result[result["district_num"].isna()]
    matched = result[result["district_num"].notna()]
    print(
        f"INFO: {len(matched)} of {len(result)} precincts matched to "
        f"{districts['district_num'].nunique()} council districts"
    )
    if not unmatched.empty:
        print(
            f"WARNING: {len(unmatched)} precincts had no district match "
            f"(outside city limits or boundary gap). "
            f"Their votes are excluded from district totals."
        )

    result["district_num"] = result["district_num"].astype("Int64")
    return result
