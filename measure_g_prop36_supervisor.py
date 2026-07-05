"""
SD County Measure G (Public Safety / Health Services Sales Tax, Nov 2024)
and CA Prop 36 (Drug & Theft Crime Sentences) results by SD Supervisor District.

Usage:
    python measure_g_prop36_supervisor.py           # uses cached data
    python measure_g_prop36_supervisor.py --force   # re-download all data

Equivalent to:
    python analyze.py measure-g supervisor
    python analyze.py prop-36 supervisor
"""

import argparse

from analyze import cmd_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute Measure G and Prop 36 results by SD County Supervisor District"
    )
    parser.add_argument("--force", action="store_true", help="Re-download data files")
    args = parser.parse_args()
    cmd_run("measure-g", "supervisor", force=args.force)
    cmd_run("prop-36", "supervisor", force=args.force)
