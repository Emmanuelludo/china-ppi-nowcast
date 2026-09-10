"""The fifteen required research-report visualizations.

Each function consumes a tidy DataFrame and returns a Matplotlib ``Figure``. The
dispatcher deliberately refuses to fabricate missing inputs: an unavailable panel
becomes a clearly labelled audit figure and is recorded in the returned manifest.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd

BLUE = "#2364AA"
ORANGE = "#F28E2B"
GREEN = "#2A9D8F"
RED = "#D1495B"
GRAY = "#6B7280"
PALETTE = [BLUE, ORANGE, GREEN, RED, "#8B5CF6", "#8D6E63", "#4C956C"]


def _new(title: str, *, figsize: tuple[float, float] = (9.0, 5.2)):
    fig, ax = plt.subplots(figsize=figsize, facecolor="white", constrained_layout=True)
    ax.set_facecolor("white")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    return fig, ax


def _require(frame: pd.DataFrame, columns: set[str]) -> None:
    missing = columns.difference(frame.columns)
    if missing:
        raise ValueError(f"figure input missing columns: {sorted(missing)}")


def _date(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column])


def historical_basket_composition(frame: pd.DataFrame) -> Figure:
    _require(frame, {"date", "category_id", "active_product_count"})
    pivot = frame.pivot_table(
        index="date", columns="category_id", values="active_product_count", aggfunc="sum"
    ).sort_index()
    fig, ax = _new("Historical NBS product-basket composition")
    ax.stackplot(pd.to_datetime(pivot.index), pivot.T.values, labels=pivot.columns, colors=PALETTE)
    ax.set_ylabel("Active products")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
    return fig


def active_products_over_time(frame: pd.DataFrame) -> Figure:
    _require(frame, {"date", "active_product_count"})
    data = frame.groupby("date", as_index=False)["active_product_count"].sum()
    fig, ax = _new("Number of active products over time")
    ax.plot(_date(data, "date"), data.active_product_count, color=BLUE, linewidth=2)
    ax.set_ylabel("Active products")
    return fig


def product_lineage_history(frame: pd.DataFrame) -> Figure:
    _require(frame, {"decision_date", "predecessor_id", "successor_id", "confidence"})
    data = frame.sort_values("decision_date").reset_index(drop=True)
    fig, ax = _new("Product lineage and replacement history", figsize=(10, 5.8))
    y = np.arange(len(data))
    size = 30 + 100 * data.confidence.fillna(0).clip(0, 1)
    ax.scatter(_date(data, "decision_date"), y, s=size, color=BLUE, alpha=0.8)
    labels = data.predecessor_id.astype(str) + " → " + data.successor_id.astype(str)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Lineage decision date")
    ax.set_ylabel("Documented transition")
    return fig


def diffusion_vs_ppi(frame: pd.DataFrame) -> Figure:
    _require(frame, {"month", "diffusion", "ppi_mom"})
    data = frame.sort_values("month")
    fig, ax = _new("Circulation-price diffusion vs headline PPI")
    ax.plot(_date(data, "month"), data.diffusion, color=BLUE, label="Diffusion")
    other = ax.twinx()
    other.plot(_date(data, "month"), data.ppi_mom, color=ORANGE, label="PPI MoM")
    ax.set_ylabel("Diffusion")
    other.set_ylabel("PPI MoM (%)")
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9), frameon=False)
    return fig


def market_index_vs_ppi(frame: pd.DataFrame) -> Figure:
    _require(frame, {"month", "market_price_change", "ppi_mom"})
    data = frame.sort_values("month")
    fig, ax = _new("Weighted market-price index vs headline PPI")
    ax.plot(_date(data, "month"), data.market_price_change, color=BLUE, label="Market-price index")
    ax.plot(_date(data, "month"), data.ppi_mom, color=ORANGE, label="PPI MoM")
    ax.axhline(0, color=GRAY, linewidth=0.8)
    ax.set_ylabel("Monthly change (%)")
    ax.legend(frameon=False)
    return fig


def category_factors_vs_industry_ppi(frame: pd.DataFrame) -> Figure:
    _require(frame, {"month", "category_id", "category_factor", "industry_ppi"})
    categories = list(frame.category_id.dropna().unique())[:6]
    fig, axes = plt.subplots(
        len(categories), 1, figsize=(9, max(3.2, 2.3 * len(categories))), sharex=True,
        facecolor="white", constrained_layout=True
    )
    axes = np.atleast_1d(axes)
    for ax, category in zip(axes, categories, strict=True):
        data = frame.loc[frame.category_id.eq(category)].sort_values("month")
        ax.plot(_date(data, "month"), data.category_factor, color=BLUE, label="Factor")
        ax.plot(_date(data, "month"), data.industry_ppi, color=ORANGE, label="Industry PPI")
        ax.set_title(str(category), loc="left")
        ax.grid(axis="y", color="#E5E7EB")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Category factors vs corresponding PPI industries", fontweight="bold")
    if len(axes):
        axes[0].legend(frameon=False, ncol=2)
    return fig


def forecast_vs_actual(frame: pd.DataFrame) -> Figure:
    _require(frame, {"target_month", "forecast", "actual"})
    data = frame.sort_values("target_month")
    fig, ax = _new("PPI forecast vs evaluation target")
    ax.plot(_date(data, "target_month"), data.actual, color="#111827", linewidth=2, label="Evaluation target")
    ax.plot(_date(data, "target_month"), data.forecast, color=BLUE, label="Forecast")
    ax.set_ylabel("PPI change (%)")
    ax.legend(frameon=False)
    return fig


def rolling_forecast_errors(frame: pd.DataFrame) -> Figure:
    _require(frame, {"target_month", "error"})
    data = frame.sort_values("target_month").copy()
    data["rolling_mae"] = data.error.abs().rolling(12, min_periods=3).mean()
    fig, ax = _new("Rolling forecast errors")
    ax.bar(_date(data, "target_month"), data.error, color=np.where(data.error.ge(0), ORANGE, BLUE), alpha=0.45)
    ax.plot(_date(data, "target_month"), data.rolling_mae, color=RED, linewidth=2, label="12-month rolling MAE")
    ax.axhline(0, color=GRAY, linewidth=0.8)
    ax.set_ylabel("Forecast error (pp)")
    ax.legend(frameon=False)
    return fig


def vintage_accuracy(frame: pd.DataFrame) -> Figure:
    _require(frame, {"forecast_vintage", "mae", "rmse"})
    order = [value for value in ["early", "mid", "final"] if value in set(frame.forecast_vintage)]
    data = frame.set_index("forecast_vintage").reindex(order or None)
    fig, ax = _new("Early / mid / final nowcast accuracy")
    x = np.arange(len(data))
    ax.bar(x - 0.18, data.mae, width=0.36, label="MAE", color=BLUE)
    ax.bar(x + 0.18, data.rmse, width=0.36, label="RMSE", color=ORANGE)
    ax.set_xticks(x, data.index)
    ax.set_ylabel("Error (pp; lower is better)")
    ax.legend(frameon=False)
    return fig


def model_performance_comparison(frame: pd.DataFrame) -> Figure:
    _require(frame, {"model_id", "rmse"})
    data = frame.sort_values("rmse", ascending=True)
    fig, ax = _new("Out-of-sample model performance comparison")
    ax.barh(data.model_id.astype(str), data.rmse, color=BLUE)
    ax.set_xlabel("RMSE (pp; lower is better)")
    return fig


def feature_importance(frame: pd.DataFrame) -> Figure:
    _require(frame, {"feature", "importance"})
    data = frame.assign(abs_importance=frame.importance.abs()).nlargest(20, "abs_importance").sort_values("importance")
    fig, ax = _new("Feature importance / coefficients", figsize=(9, 6.5))
    ax.barh(data.feature.astype(str), data.importance, color=np.where(data.importance.ge(0), BLUE, ORANGE))
    ax.axvline(0, color=GRAY, linewidth=0.8)
    ax.set_xlabel("Coefficient or model importance")
    return fig


def contribution_decomposition(frame: pd.DataFrame) -> Figure:
    _require(frame, {"contributor_id", "contribution_pp"})
    data = frame.sort_values("contribution_pp")
    fig, ax = _new("Forecast contribution decomposition")
    ax.barh(data.contributor_id.astype(str), data.contribution_pp, color=np.where(data.contribution_pp.ge(0), BLUE, ORANGE))
    ax.axvline(0, color=GRAY, linewidth=0.8)
    ax.set_xlabel("Model contribution (percentage points)")
    return fig


def shock_adjusted_vs_baseline(frame: pd.DataFrame) -> Figure:
    _require(frame, {"target_month", "shock_scenario", "forecast"})
    fig, ax = _new("Shock-adjusted vs baseline nowcast")
    for color, (scenario, data) in zip(PALETTE, frame.groupby("shock_scenario"), strict=False):
        data = data.sort_values("target_month")
        ax.plot(_date(data, "target_month"), data.forecast, label=str(scenario), color=color)
    ax.set_ylabel("PPI forecast (%)")
    ax.legend(frameon=False)
    return fig


def turning_point_detection(frame: pd.DataFrame) -> Figure:
    _require(frame, {"target_month", "actual", "forecast", "actual_turn", "predicted_turn"})
    data = frame.sort_values("target_month")
    dates = _date(data, "target_month")
    fig, ax = _new("Turning-point detection (primary definition: sign reversal)")
    ax.plot(dates, data.actual, color="#111827", label="Actual")
    ax.plot(dates, data.forecast, color=BLUE, label="Forecast")
    ax.scatter(dates[data.actual_turn], data.loc[data.actual_turn, "actual"], marker="o", s=70, color=RED, label="Actual turn")
    ax.scatter(dates[data.predicted_turn], data.loc[data.predicted_turn, "forecast"], marker="x", s=70, color=GREEN, label="Predicted turn")
    ax.axhline(0, color=GRAY, linewidth=0.8)
    ax.legend(frameon=False)
    return fig


def historical_forecast_fan(frame: pd.DataFrame) -> Figure:
    _require(frame, {"target_month", "forecast", "lower_bound", "upper_bound", "actual"})
    data = frame.sort_values("target_month")
    dates = _date(data, "target_month")
    fig, ax = _new("Historical forecast fan chart")
    ax.fill_between(dates, data.lower_bound.astype(float), data.upper_bound.astype(float), color=BLUE, alpha=0.18, label="Empirical interval")
    ax.plot(dates, data.forecast, color=BLUE, label="Forecast")
    ax.plot(dates, data.actual, color="#111827", linewidth=1.7, label="First release")
    ax.set_ylabel("PPI change (%)")
    ax.legend(frameon=False)
    return fig


FIGURE_SPECS: dict[str, tuple[str, Callable[[pd.DataFrame], Figure]]] = {
    "01_basket_composition": ("basket_composition", historical_basket_composition),
    "02_active_products": ("active_products", active_products_over_time),
    "03_product_lineage": ("product_lineage", product_lineage_history),
    "04_diffusion_vs_ppi": ("diffusion_vs_ppi", diffusion_vs_ppi),
    "05_market_index_vs_ppi": ("market_index_vs_ppi", market_index_vs_ppi),
    "06_category_vs_industry": ("category_vs_industry", category_factors_vs_industry_ppi),
    "07_forecast_vs_actual": ("forecast_vs_actual", forecast_vs_actual),
    "08_rolling_errors": ("rolling_errors", rolling_forecast_errors),
    "09_vintage_accuracy": ("vintage_accuracy", vintage_accuracy),
    "10_model_performance": ("model_performance", model_performance_comparison),
    "11_feature_importance": ("feature_importance", feature_importance),
    "12_contributions": ("contributions", contribution_decomposition),
    "13_shock_comparison": ("shock_comparison", shock_adjusted_vs_baseline),
    "14_turning_points": ("turning_points", turning_point_detection),
    "15_forecast_fan": ("forecast_fan", historical_forecast_fan),
}


def _unavailable_figure(title: str, reason: str) -> Figure:
    fig, ax = _new(title)
    ax.axis("off")
    ax.text(0.5, 0.5, f"Not generated\n{reason}", ha="center", va="center", color=GRAY)
    return fig


def build_required_figures(
    inputs: Mapping[str, pd.DataFrame],
    *,
    output_dir: str | Path | None = None,
) -> tuple[dict[str, Figure], pd.DataFrame]:
    """Build all 15 panels and return figures plus a generation audit manifest."""

    figures: dict[str, Figure] = {}
    manifest: list[dict[str, str]] = []
    destination = Path(output_dir) if output_dir is not None else None
    if destination is not None:
        destination.mkdir(parents=True, exist_ok=True)
    for name, (input_key, builder) in FIGURE_SPECS.items():
        if input_key not in inputs or inputs[input_key].empty:
            reason = f"input '{input_key}' is unavailable"
            figure = _unavailable_figure(name.replace("_", " ").title(), reason)
            status = "input_unavailable"
        else:
            try:
                figure = builder(inputs[input_key])
                reason = ""
                status = "generated"
            except (KeyError, TypeError, ValueError) as exc:
                reason = str(exc)
                figure = _unavailable_figure(name.replace("_", " ").title(), reason)
                status = "schema_error"
        figures[name] = figure
        path = ""
        if destination is not None:
            path = str(destination / f"{name}.png")
            figure.savefig(path, dpi=160, facecolor="white", bbox_inches="tight")
        manifest.append(
            {"figure_id": name, "input_key": input_key, "status": status, "reason": reason, "path": path}
        )
    return figures, pd.DataFrame(manifest)
