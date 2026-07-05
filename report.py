"""Format and save aggregated election results."""

from pathlib import Path

import pandas as pd


def _format_table(
    results: pd.DataFrame,
    title: str,
    choice_a_label: str = "Yes",
    choice_b_label: str = "No",
) -> str:
    lines = [title, "=" * len(title), ""]
    header = (
        f"{'District':>10}  {f'{choice_a_label} Votes':>12}  {f'{choice_b_label} Votes':>11}  "
        f"{'Total':>10}  {f'{choice_a_label}%':>6}  {f'{choice_b_label}%':>6}  {'Margin':>8}  {'Result':>6}"
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


def print_district_table(
    results: pd.DataFrame,
    title: str = "Results by District",
    choice_a_label: str = "Yes",
    choice_b_label: str = "No",
) -> None:
    print(_format_table(results, title, choice_a_label, choice_b_label))


def save_csv(results: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)
    print(f"  Saved: {path}")


def save_text_table(
    results: pd.DataFrame,
    path: Path,
    title: str = "Results by District",
    choice_a_label: str = "Yes",
    choice_b_label: str = "No",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_table(results, title, choice_a_label, choice_b_label))
    print(f"  Saved: {path}")
