"""
San Diego Measure E (Public Services Sales Tax, Nov 2024)
Results stratified by City Council District.

Usage:
    python measure_e.py           # downloads data if not present, runs full pipeline
    python measure_e.py --force   # re-download all data files

Equivalent to: python analyze.py measure-e council
"""

import argparse

from analyze import cmd_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute Measure E results by SD City Council district"
    )
    parser.add_argument("--force", action="store_true", help="Re-download data files")
    args = parser.parse_args()
    cmd_run("measure-e", "council", force=args.force)
