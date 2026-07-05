"""Parse SD Registrar SOV XLS, extract contest votes, and aggregate by district."""

import re
from pathlib import Path

import pandas as pd


def find_measure_sheet(xls_path: Path, measure_label: str) -> str:
    """Find which sheet in the SOV XLS contains the given measure.
    Returns the sheet name."""
    xl = pd.ExcelFile(xls_path, engine="xlrd")
    norm_label = measure_label.upper()
    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(xl, sheet, header=None, nrows=8, usecols=[2])
            for val in df[2].dropna().astype(str):
                if norm_label in val.upper():
                    return sheet
        except Exception:
            continue
    raise ValueError(
        f"Could not find sheet for '{measure_label}' in {xls_path.name}. "
        f"Available sheets: {xl.sheet_names[:10]}..."
    )


def parse_measure_sheet(xls_path: Path, sheet_name: str) -> pd.DataFrame:
    """Parse a precinct canvass sheet and return per-precinct vote totals.

    The sheet format is:
      Row 0-3: title/header rows (skip)
      Row 4:   contest title in col 2
      Row 5:   column headers (YES in col 7, NO in col 9)
      Row 6+:  data rows with col 0 = 'NNNN-SVPREC-NAME', col 1 = vote type

    Returns DataFrame with columns [SVPREC, yes_votes, no_votes].
    Only "Total" rows are kept (combines vote-center and mail ballots)."""
    xl = pd.ExcelFile(xls_path, engine="xlrd")
    df = pd.read_excel(xl, sheet_name, header=None)

    # Rows 6+ are data; filter to "Total" rows only
    data = df.iloc[6:].copy()
    data.columns = range(len(data.columns))

    # Keep only "Total" rows (col 1 == "Total")
    totals = data[data[1].astype(str).str.strip() == "Total"].copy()

    # Extract SVPREC from "NNNN-SVPREC-NAME" in col 0
    def extract_svprec(val: str):
        parts = str(val).strip().split("-")
        return parts[1] if len(parts) >= 2 else None

    totals["SVPREC"] = totals[0].apply(extract_svprec)

    # YES is col 7, NO is col 9 (confirmed from header row 5)
    totals = totals.rename(columns={7: "yes_raw", 9: "no_raw"})

    def to_int(col: pd.Series) -> pd.Series:
        cleaned = col.astype(str).str.strip().replace({"***": None, "nan": None, "": None})
        return pd.to_numeric(cleaned, errors="coerce").astype("Int64")

    totals["yes_votes"] = to_int(totals["yes_raw"])
    totals["no_votes"] = to_int(totals["no_raw"])

    result = totals[["SVPREC", "yes_votes", "no_votes"]].dropna(subset=["SVPREC"])
    result = result[result["SVPREC"].str.strip() != ""]

    masked = result["yes_votes"].isna().sum()
    if masked > 0:
        print(f"INFO: {masked} precincts have masked (***) vote counts — excluded from totals")

    return result.reset_index(drop=True)


def load_svprec_map(path: Path) -> pd.DataFrame:
    """Load SWDB SVPREC→SRPREC conversion table. Returns DataFrame [SVPREC, SRPREC]."""
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]
    sv_col = next((c for c in df.columns if "svprec" in c), None)
    sr_col = next((c for c in df.columns if "srprec" in c), None)
    if not sv_col or not sr_col:
        raise KeyError(
            f"Could not find svprec/srprec columns. Columns: {list(df.columns)}"
        )
    result = df[[sv_col, sr_col]].rename(columns={sv_col: "SVPREC", sr_col: "SRPREC"})
    result = result.drop_duplicates(subset=["SVPREC"])
    return result.reset_index(drop=True)


def merge_svprec_to_srprec(
    votes: pd.DataFrame, svprec_map: pd.DataFrame
) -> pd.DataFrame:
    """Map SVPREC to SRPREC so votes can join to precinct geometries.
    Returns DataFrame with columns [SRPREC, yes_votes, no_votes]."""
    votes["SVPREC"] = votes["SVPREC"].astype(str).str.strip()
    svprec_map["SVPREC"] = svprec_map["SVPREC"].astype(str).str.strip()
    merged = votes.merge(svprec_map, on="SVPREC", how="left")
    unmatched = merged["SRPREC"].isna().sum()
    if unmatched > 0:
        print(f"WARNING: {unmatched} SVPRECs had no SRPREC match in conversion table")
    return merged[["SRPREC", "yes_votes", "no_votes"]]


def merge_votes_with_districts(
    votes: pd.DataFrame, mapping: pd.DataFrame
) -> pd.DataFrame:
    """Join vote data to precinct→district mapping.
    Returns [SRPREC, district_num, yes_votes, no_votes]."""
    mapping = mapping.copy()
    mapping["SRPREC"] = mapping["SRPREC"].astype(str).str.strip()
    votes["SRPREC"] = votes["SRPREC"].astype(str).str.strip()
    merged = votes.merge(mapping, on="SRPREC", how="left")
    unmatched = merged[merged["district_num"].isna()]
    if not unmatched.empty:
        lost_yes = pd.to_numeric(unmatched["yes_votes"], errors="coerce").sum()
        lost_no = pd.to_numeric(unmatched["no_votes"], errors="coerce").sum()
        print(
            f"WARNING: {len(unmatched)} precincts have no district assignment "
            f"({int(lost_yes):,} yes, {int(lost_no):,} no votes excluded — outside city limits)."
        )
    return merged


def load_swdb_prop_votes(path: Path, yes_col: str, no_col: str) -> pd.DataFrame:
    """Extract votes for a proposition from the SWDB wide-format SOV data CSV.

    Returns DataFrame with columns [SVPREC, yes_votes, no_votes]."""
    df = pd.read_csv(path, dtype=str, usecols=["svprec", yes_col, no_col])
    df = df.rename(columns={"svprec": "SVPREC"})
    df["SVPREC"] = df["SVPREC"].astype(str).str.strip()

    def to_int(col: pd.Series) -> pd.Series:
        cleaned = col.astype(str).str.strip().replace({"***": None, "nan": None, "": None})
        return pd.to_numeric(cleaned, errors="coerce").astype("Int64")

    df["yes_votes"] = to_int(df[yes_col])
    df["no_votes"] = to_int(df[no_col])
    result = df[["SVPREC", "yes_votes", "no_votes"]].dropna(subset=["SVPREC"])
    result = result[result["SVPREC"] != "nan"]
    return result.reset_index(drop=True)


def aggregate_by_district(merged: pd.DataFrame) -> pd.DataFrame:
    """Group by district_num, sum votes, compute percentages."""
    with_district = merged.dropna(subset=["district_num"]).copy()
    with_district["district_num"] = with_district["district_num"].astype(int)
    with_district["yes_votes"] = (
        pd.to_numeric(with_district["yes_votes"], errors="coerce").fillna(0).astype(int)
    )
    with_district["no_votes"] = (
        pd.to_numeric(with_district["no_votes"], errors="coerce").fillna(0).astype(int)
    )

    grouped = (
        with_district.groupby("district_num")[["yes_votes", "no_votes"]]
        .sum()
        .reset_index()
    )
    grouped["total_votes"] = grouped["yes_votes"] + grouped["no_votes"]
    grouped["yes_pct"] = (grouped["yes_votes"] / grouped["total_votes"] * 100).round(2)
    grouped["no_pct"] = (grouped["no_votes"] / grouped["total_votes"] * 100).round(2)
    grouped["margin_pct"] = (grouped["yes_pct"] - grouped["no_pct"]).round(2)
    grouped["margin_votes"] = grouped["yes_votes"] - grouped["no_votes"]
    grouped["passed"] = grouped["yes_pct"] > 50
    return grouped.sort_values("district_num").reset_index(drop=True)
