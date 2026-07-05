"""Choropleth map of election results by district."""

from pathlib import Path
from typing import Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd


def make_choropleth(
    results: pd.DataFrame,
    districts: gpd.GeoDataFrame,
    value_col: str = "yes_pct",
    title: str = "Results by Council District",
    output_path: Optional[Path] = None,
) -> None:
    """Merge results onto districts and draw a choropleth.

    Colormap: RdYlGn centered at 50% for pass/fail clarity.
    Districts are annotated with number and yes%."""
    merged = districts.merge(
        results[["district_num", "yes_pct", "no_pct", "margin_pct", "passed"]],
        on="district_num",
        how="left",
    )

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Diverging colormap centered at 50 (vmin=0, vcenter=50, vmax=100)
    norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=50, vmax=100)
    cmap = plt.cm.RdYlGn

    merged.plot(
        column=value_col,
        ax=ax,
        cmap=cmap,
        norm=norm,
        edgecolor="white",
        linewidth=1.5,
        missing_kwds={"color": "lightgrey", "label": "No data"},
    )

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Yes %", fontsize=11)

    # Annotate each district
    for _, row in merged.iterrows():
        if row.geometry is None or pd.isna(row.get("yes_pct")):
            continue
        centroid = row.geometry.centroid
        label = f"D{int(row['district_num'])}\n{row['yes_pct']:.1f}%"
        ax.annotate(
            label,
            xy=(centroid.x, centroid.y),
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color="black",
        )

    ax.set_axis_off()
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    fig.text(
        0.5, 0.01,
        "Source: CA Statewide Database · SanGIS",
        ha="center",
        fontsize=8,
        color="grey",
    )

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"  Saved: {output_path}")
        plt.close(fig)
    else:
        plt.show()
