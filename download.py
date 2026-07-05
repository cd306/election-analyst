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


def download_registrar_sov(force: bool = False) -> Path:
    """Download the SD County Registrar Official Final Statement of Votes Cast (2024 Nov).
    Extracts the XLS from the zip and returns its path."""
    xls_dest = DATA_DIR / "Official Final Statement of Votes Case 202411.xls"
    if xls_dest.exists() and not force:
        return xls_dest

    zip_url = "https://www.sdvote.com/content/dam/rov/en/archive/Official Final Statement of Votes Cast 202411.zip"
    zip_dest = DATA_DIR / "sov_202411.zip"
    download_file(zip_url, zip_dest, force=force)

    with zipfile.ZipFile(zip_dest) as z:
        names = z.namelist()
        xls_name = next((n for n in names if n.endswith(".xls")), None)
        if not xls_name:
            raise FileNotFoundError(f"No .xls file found in zip. Contents: {names}")
        z.extract(xls_name, DATA_DIR)
    return DATA_DIR / xls_name


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
