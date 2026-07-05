# Election Analyst

Stratify any election result by political subdivision — see how a measure or race
performed in each city council district, supervisor district, or congressional district.

Analogous to how presidential results are shown by congressional district, but for any
contest at any level of government. Well-funded campaigns already do this internally;
this tool makes it freely available.

**Current coverage:** San Diego County, November 2024 General Election.

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Usage

### Web app (easiest)

```bash
streamlit run app.py
```

Opens a browser UI. Select a contest and district type, click **Run Analysis**.

### CLI

```bash
# List available contests and district types
python analyze.py --list

# Run any combination
python analyze.py measure-e council
python analyze.py measure-g supervisor
python analyze.py prop-36 supervisor
python analyze.py prop-36 council

# Force re-download of source data
python analyze.py measure-e council --force
```

Outputs go to `outputs/`:
- `{contest}-by-{district}.csv`
- `{contest}-by-{district}.txt`
- `{contest}-by-{district}_choropleth.png`

### Legacy entry scripts (still work)

```bash
python measure_e.py
python measure_g_prop36_supervisor.py
```

---

## Adding a new contest

Open `contests.py` and append to `CONTESTS`. Two source types are supported:

**From the SD County Registrar XLS** (local measures, some candidate races):
```python
ContestConfig(
    name="measure-d",
    label="SD Measure D (Charter Amendment) — Nov 2024",
    source="registrar_xls",
    search_label="CITY OF SAN DIEGO - MEASURE D",
),
```

**From the CA Statewide Database SOV CSV** (statewide propositions):
```python
ContestConfig(
    name="prop-2",
    label="CA Prop 2 (School Bonds) — Nov 2024",
    source="swdb_data",
    yes_col="PR_2_Y",
    no_col="PR_2_N",
),
```

For candidate/partisan races, set `choice_a_label` / `choice_b_label` and `cmap_colors`:
```python
ContestConfig(
    name="mayor-2024",
    label="SD Mayor — Nov 2024",
    source="registrar_xls",
    search_label="MAYOR",
    choice_a_label="Dem",
    choice_b_label="Rep",
    cmap_colors=("#DAA520", "#ffffff", "#1565C0"),  # gold-white-blue
    legend_label="Dem %",
),
```

That's it — the contest immediately appears in the CLI and web UI.

---

## Adding a new district type

1. Add a download function to `download.py`
2. Add a load function to `spatial.py`
3. Add a `DistrictType` entry to `DISTRICT_TYPES` in `contests.py`
4. Add a dispatch case in `pipeline.py` under `run_analysis()`

---

## Data sources

| Data | Source |
|---|---|
| Precinct vote results (local measures) | [SD County Registrar Statement of Votes](https://www.sdvote.com) |
| Precinct vote results (CA propositions) | [CA Statewide Database (SWDB)](https://statewidedatabase.org) |
| Precinct boundaries | SWDB SR precinct GeoJSON (county 073, G24) |
| SVPREC→SRPREC mapping | SWDB conversion table |
| City Council Districts | [SanGIS / SANDAG](https://geo.sandag.org) |
| Supervisor Districts | [SANDAG FeatureServer](https://geo.sandag.org) |

Data files are downloaded to `data/raw/` on first run and cached locally (gitignored).

---

## Accuracy

99.9%+ of county votes are captured. A small number of precincts on city/county boundaries
are unassigned and excluded from district totals — this is noted in run output.

---

## Contributing

Pull requests welcome. The most useful additions:
- New contests (add to `contests.py`)
- New subdivision types (add to `spatial.py`, `download.py`, `contests.py`, `pipeline.py`)
- Support for other CA counties (generalize the download URLs and boundary sources)
