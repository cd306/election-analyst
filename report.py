"""Format and save aggregated election results."""

from pathlib import Path

import pandas as pd


def _format_table(results: pd.DataFrame, title: str) -> str:
    lines = [title, "=" * len(title), ""]
    header = (
        f"{'District':>10}  {'Yes Votes':>12}  {'No Votes':>11}  "
        f"{'Total':>10}  {'Yes%':>6}  {'No%':>6}  {'Margin':>8}  {'Result':>6}"
    )
    sep = "-" * len(header)
    lines += [header, sep]
    for _, row in results.iterrows():
        result = "PASS" if row["passed"] else "FAIL"
        margin = row["margin_pct"]
        margin_str = f"+{margin:.1f}%" if margin >= 0 else f"{margin:.1f}%"
        lines.append(
            f"{'D' + str(int(row['district_num'])):>10}  "
            f"{int(row['yes_votes']):>12,}  "
            f"{int(row['no_votes']):>11,}  "
            f"{int(row['total_votes']):>10,}  "
            f"{row['yes_pct']:>5.1f}%  "
            f"{row['no_pct']:>5.1f}%  "
            f"{margin_str:>8}  "
            f"{result:>6}"
        )
    lines += [
        sep,
        f"{'TOTAL':>10}  "
        f"{int(results['yes_votes'].sum()):>12,}  "
        f"{int(results['no_votes'].sum()):>11,}  "
        f"{int(results['total_votes'].sum()):>10,}",
        "",
    ]
    return "\n".join(lines)


def print_district_table(results: pd.DataFrame, title: str = "Results by District") -> None:
    print(_format_table(results, title))


def save_csv(results: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)
    print(f"  Saved: {path}")


def save_text_table(results: pd.DataFrame, path: Path, title: str = "Results by District") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_table(results, title))
    print(f"  Saved: {path}")
