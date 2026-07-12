"""Download raw data files from SD Registrar and SWDB."""

import zipfile
from pathlib import Path
from urllib.parse import quote

import requests

DATA_DIR = Path("data/raw")

_HEADERS = {"User-Agent": "Mozilla/5.0"}


def download_file(url: str, dest: Path, force: bool = False) -> Path:
    """Download url to dest. Skips if dest exists unless force=True.
    Handles .zip extraction automatically."""
    if dest.exists() and not force:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {url}")
    r = requests.get(url, timeout=180, stream=True, headers=_HEADERS)
    if r.status_code == 404:
        raise FileNotFoundError(f"404 Not Found: {url}")
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


_SOV_REGISTRY = {
    "202411": {
        "zip_url": "https://www.sdvote.com/content/dam/rov/en/archive/Official Final Statement of Votes Cast 202411.zip",
        "zip_dest": "sov_202411.zip",
        "ext": ".xls",
    },
    "202606": {
        "zip_url": "https://www.sdvote.com/content/dam/rov/en/archive/Statement of Votes Cast 202606.zip",
        "zip_dest": "sov_202606.zip",
        "ext": ".xlsx",
    },
}


def download_registrar_sov(election_ym: str = "202411", force: bool = False) -> Path:
    """Download the SD County Registrar Statement of Votes Cast for a given election.

    election_ym: YYYYMM string, e.g. '202411' (Nov 2024) or '202606' (Jun 2026).
    Returns path to the extracted spreadsheet."""
    if election_ym not in _SOV_REGISTRY:
        raise ValueError(
            f"Unknown SOV election '{election_ym}'. "
            f"Available: {list(_SOV_REGISTRY)}. Add an entry to _SOV_REGISTRY in download.py."
        )
    entry = _SOV_REGISTRY[election_ym]
    ext = entry["ext"]

    # Check if already extracted
    for candidate in DATA_DIR.glob(f"*{election_ym}*{ext}"):
        if not force:
            return candidate
    # Also check nested extraction paths
    for candidate in DATA_DIR.rglob(f"*{ext}"):
        if election_ym in str(candidate) and not force:
            return candidate

    zip_dest = DATA_DIR / entry["zip_dest"]
    download_file(entry["zip_url"], zip_dest, force=force)

    with zipfile.ZipFile(zip_dest) as z:
        names = z.namelist()
        spreadsheet = next((n for n in names if n.endswith(ext)), None)
        if not spreadsheet:
            raise FileNotFoundError(f"No {ext} file found in zip. Contents: {names}")
        z.extractall(DATA_DIR)
        # Handle nested directories in zip
        extracted = DATA_DIR / spreadsheet
        if not extracted.exists():
            raise FileNotFoundError(f"Expected extracted file at {extracted}")
    return extracted


def download_precinct_boundaries(
    election: str = "G24", county: str = "073", force: bool = False
) -> Path:
    """Download and extract SWDB SR precinct boundary GeoJSON zip."""
    url = (
        f"https://statewidedatabase.org/pub/data/{election}/c{county}/"
        f"srprec_{county}_{election.lower()}_v01.geojson.zip"
    )
    zip_dest = DATA_DIR / f"srprec_{county}_{election.lower()}_v01.geojson.zip"
    download_file(url, zip_dest, force=force)
    geojson = zip_dest.with_suffix("")
    if not geojson.exists():
        with zipfile.ZipFile(zip_dest) as z:
            z.extractall(DATA_DIR)
    if not geojson.exists():
        raise FileNotFoundError(
            f"Expected extracted GeoJSON at {geojson} — check zip contents"
        )
    return geojson


def download_svprec_map(
    election: str = "G24", county: str = "073", force: bool = False
) -> Path:
    """Download SWDB SVPREC→SRPREC conversion table."""
    url = (
        f"https://statewidedatabase.org/pub/data/{election}/c{county}/"
        f"c{county}_rg_rr_sr_svprec_{election.lower()}.csv"
    )
    dest = DATA_DIR / f"svprec_map_{county}_{election.lower()}.csv"
    download_file(url, dest, force=force)
    return dest


def download_sov_data(
    election: str = "G24", county: str = "073", force: bool = False
) -> Path:
    """Download SWDB main SOV data CSV (statewide props, federal/state races)."""
    url = (
        f"https://statewidedatabase.org/pub/data/{election}/c{county}/"
        f"sov_data_by_{election.lower()}_svprec.csv"
    )
    dest = DATA_DIR / "sov_data_svprec.csv"
    download_file(url, dest, force=force)
    return dest


def download_supervisor_districts(force: bool = False) -> Path:
    """Download SD County Supervisor District boundaries from SANDAG FeatureServer."""
    url = (
        "https://geo.sandag.org/server/rest/services/Hosted/Supervisor_Districts/"
        "FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
    )
    dest = DATA_DIR / "supervisor_districts.geojson"
    download_file(url, dest, force=force)
    return dest


def download_council_districts(force: bool = False) -> Path:
    """Download San Diego County council district boundaries GeoJSON from SanGIS."""
    url = "https://geo.sandag.org/server/rest/directories/downloads/Council_Districts.geojson"
    dest = DATA_DIR / "council_districts.geojson"
    download_file(url, dest, force=force)
    return dest
