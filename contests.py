"""Contest and district type registry.

To add a new contest, append a ContestConfig to CONTESTS.
To add a new district type, append a DistrictType to DISTRICT_TYPES
and add its dispatch cases in pipeline.py.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContestConfig:
    name: str                    # kebab slug used in filenames: "measure-e"
    label: str                   # display label: "SD Measure E (Sales Tax) — Nov 2024"
    source: str                  # "registrar_xls" | "swdb_data"
    search_label: str = ""       # registrar_xls: substring to find the XLS sheet
    yes_col: str = ""            # swdb_data: yes-vote column name e.g. "PR_36_Y"
    no_col: str = ""             # swdb_data: no-vote column name e.g. "PR_36_N"
    choice_a_label: str = "Yes"  # shown in tables and map legend
    choice_b_label: str = "No"
    cmap_colors: tuple = ("#d73027", "#ffffff", "#1a9850")  # red-white-green
    legend_label: str = "Yes %"
    election_ym: str = "202411"  # YYYYMM for Registrar SOV zip lookup
    election: str = "G24"        # SWDB election label for precinct boundaries + SVPREC map
    county: str = "073"          # FIPS county code (073 = San Diego)


@dataclass(frozen=True)
class DistrictType:
    name: str         # slug: "council" | "supervisor"
    label: str        # full label: "SD City Council District"
    short_label: str  # for compact dropdowns: "Council"


CONTESTS = [
    ContestConfig(
        name="measure-e",
        label="SD Measure E (Sales Tax) — Nov 2024",
        source="registrar_xls",
        search_label="CITY OF SAN DIEGO - MEASURE E",
    ),
    ContestConfig(
        name="measure-g",
        label="SD County Measure G (Sales Tax) — Nov 2024",
        source="registrar_xls",
        search_label="MEASURE G",
    ),
    ContestConfig(
        name="prop-36",
        label="CA Prop 36 (Drug & Theft Sentences) — Nov 2024",
        source="swdb_data",
        yes_col="PR_36_Y",
        no_col="PR_36_N",
    ),
    # June 2026 Primary — uses G24 precinct geometry (SWDB P26 not yet published)
    ContestConfig(
        name="measure-a-2026",
        label="SD Measure A (Empty Homes Tax) — Jun 2026",
        source="registrar_xls",
        search_label="CITY OF SAN DIEGO MEASURE A",
        election_ym="202606",
        election="G24",   # best available SWDB precinct data until P26 is published
        county="073",
    ),
]

DISTRICT_TYPES = [
    DistrictType(
        name="council",
        label="SD City Council District",
        short_label="Council",
    ),
    DistrictType(
        name="supervisor",
        label="SD County Supervisor District",
        short_label="Supervisor",
    ),
]

CONTESTS_BY_NAME = {c.name: c for c in CONTESTS}
DISTRICT_TYPES_BY_NAME = {d.name: d for d in DISTRICT_TYPES}
