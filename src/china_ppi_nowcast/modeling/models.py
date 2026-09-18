"""Train and load reconstructed candidates and transparent timing benchmarks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor, VotingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..storage import atomic_write_text, stable_hash


@dataclass(frozen=True)
class ModelSpec:
    key: str
    label: str
    prefixes: tuple[str, ...]
    estimator_kind: str
    vintages: tuple[str, ...]
    information_set: str
    required_observed_prefix: str | None = None


SURVEY_WINDOW_CONTRACT = (
    "M-2:21-end, M-1:1-10/11-20/21-end, and M:1-10; final also uses M:11-20; "
    "M:21-end is excluded"
)
TWENTIETH_WINDOW_CONTRACT = "M-1:11-20 and M:11-20 only; available in the final vintage"

CORE_MODEL_SPECS = (
    ModelSpec("category_factor_regression", "Category-factor regression", ("category__",), "factor_ridge", ("early", "final"), SURVEY_WINDOW_CONTRACT),
    ModelSpec("gradient_boosting", "Gradient boosting", ("global__", "category__", "product__", "missing__"), "hist_gradient_boosting", ("early", "final"), SURVEY_WINDOW_CONTRACT),
    ModelSpec("economic_ml_hybrid", "Economic + ML hybrid", ("global__", "category__", "econ__"), "voting_hybrid", ("early", "final"), SURVEY_WINDOW_CONTRACT),
    ModelSpec("product_level_ridge", "Product-level ridge", ("product__", "missing__"), "ridge", ("early", "final"), SURVEY_WINDOW_CONTRACT),
    ModelSpec("sector_first_aggregation", "Sector-first aggregation", ("global__", "category__"), "ridge", ("early", "final"), SURVEY_WINDOW_CONTRACT),
    ModelSpec("random_forest", "Random forest", ("global__", "category__", "product__", "missing__"), "random_forest", ("early", "final"), SURVEY_WINDOW_CONTRACT),
)

FINAL_BENCHMARK_SPECS = (
    ModelSpec(
        "twentieth_to_twentieth_direct",
        "20th-to-20th direct trimmed index",
        ("twentieth_product__",),
        "direct_trimmed_index",
        ("final",),
        TWENTIETH_WINDOW_CONTRACT,
        "twentieth_product__",
    ),
    ModelSpec(
        "twentieth_to_twentieth_ridge",
        "20th-to-20th product ridge",
        ("twentieth_product__", "twentieth_missing__"),
        "ridge",
        ("final",),
        TWENTIETH_WINDOW_CONTRACT,
        "twentieth_product__",
    ),
)

MODEL_SPECS = CORE_MODEL_SPECS + FINAL_BENCHMARK_SPECS


def model_specs_for_vintage(vintage: str | None) -> tuple[ModelSpec, ...]:
    if vintage is None:
        return CORE_MODEL_SPECS
    return tuple(spec for spec in MODEL_SPECS if vintage in spec.vintages)


class DirectTrimmedIndex(RegressorMixin, BaseEstimator):
    """Return the row-wise trimmed mean of observed product changes without fitting weights."""

    def __init__(self, trim_fraction: float = 0.1) -> None:
        self.trim_fraction = trim_fraction

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "DirectTrimmedIndex":
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        output: list[float] = []
        for row in np.asarray(X, dtype=float):
            values = np.sort(row[np.isfinite(row)])
            if not len(values):
                output.append(np.nan)
                continue
            cut = int(len(values) * self.trim_fraction)
            kept = values[cut : len(values) - cut] if cut and len(values) > 2 * cut else values
            output.append(float(np.mean(kept)))
        return np.asarray(output)


def _ridge() -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
            ("scale", StandardScaler()),
            ("regressor", RidgeCV(alphas=np.logspace(-3, 3, 25))),
        ]
    )


def _make_estimator(kind: str, n_rows: int, n_columns: int) -> object:
    if kind == "factor_ridge":
        components = max(1, min(3, n_rows - 1, n_columns))
        return Pipeline(
            [
                ("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
                ("scale", StandardScaler()),
                ("factors", PCA(n_components=components, random_state=20260914)),
                ("regressor", RidgeCV(alphas=np.logspace(-3, 3, 25))),
            ]
        )
    if kind == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(
            loss="squared_error", learning_rate=0.05, max_iter=200, max_leaf_nodes=15,
            l2_regularization=1.0, random_state=20260914
        )
    if kind == "voting_hybrid":
        return VotingRegressor(
            [
                ("ridge", _ridge()),
                ("hist", HistGradientBoostingRegressor(max_iter=150, max_leaf_nodes=10, random_state=20260914)),
            ],
            weights=[1.0, 1.0],
        )
    if kind == "ridge":
        return _ridge()
    if kind == "random_forest":
        return Pipeline(
            [
                ("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
                ("regressor", RandomForestRegressor(
                    n_estimators=200, min_samples_leaf=3, max_features="sqrt",
                    random_state=20260914, n_jobs=-1
                )),
            ]
        )
    if kind == "direct_trimmed_index":
        return DirectTrimmedIndex(trim_fraction=0.1)
    raise ValueError(f"unknown estimator kind: {kind}")


def _columns_for(frame: pd.DataFrame, spec: ModelSpec) -> list[str]:
    return sorted(
        column for column in frame.columns
        if column.startswith(spec.prefixes) and pd.api.types.is_numeric_dtype(frame[column])
    )


def _metric_summary(actual: np.ndarray, estimate: np.ndarray) -> dict[str, float | int]:
    error = estimate - actual
    return {
        "n_oof": int(len(actual)),
        "mae": float(mean_absolute_error(actual, estimate)),
        "rmse": float(mean_squared_error(actual, estimate) ** 0.5),
        "bias": float(error.mean()),
        "directional_accuracy": float(np.mean(np.sign(actual) == np.sign(estimate))),
    }


def _oof_metrics(estimator: object, X: pd.DataFrame, y: pd.Series) -> dict[str, object]:
    splits = min(5, max(2, len(X) // 6))
    cv = TimeSeriesSplit(n_splits=splits)
    truth: list[float] = []
    predicted: list[float] = []
    stressed: list[float] = []
    stress_columns = [
        column for column in X.columns
        if column.startswith(("product__", "category__", "twentieth_product__", "twentieth_category__"))
    ]
    rng = np.random.default_rng(20260914)
    for train_idx, test_idx in cv.split(X):
        fitted = clone(estimator).fit(X.iloc[train_idx], y.iloc[train_idx])
        truth.extend(y.iloc[test_idx].astype(float).tolist())
        predicted.extend(np.asarray(fitted.predict(X.iloc[test_idx]), dtype=float).tolist())
        stressed_X = X.iloc[test_idx].copy()
        if stress_columns:
            mask = rng.random((len(stressed_X), len(stress_columns))) < 0.10
            stressed_X.loc[:, stress_columns] = stressed_X[stress_columns].mask(mask)
        stressed.extend(np.asarray(fitted.predict(stressed_X), dtype=float).tolist())
    actual = np.asarray(truth)
    estimate = np.asarray(predicted)
    stressed_estimate = np.asarray(stressed)
    result: dict[str, object] = _metric_summary(actual, estimate)
    result["missing_panel_stress"] = {
        **_metric_summary(actual, stressed_estimate),
        "mask_fraction": 0.10,
        "mean_absolute_prediction_change": float(np.mean(np.abs(stressed_estimate - estimate))),
    }
    return result


def _baseline_metrics(y: pd.Series, minimum_history: int = 12) -> dict[str, dict[str, float | int]]:
    actual = y.to_numpy(dtype=float)[minimum_history:]
    history_mean = np.array([y.iloc[:i].mean() for i in range(minimum_history, len(y))], dtype=float)
    persistence = y.to_numpy(dtype=float)[minimum_history - 1 : -1]
    return {
        "no_change": _metric_summary(actual, np.zeros_like(actual)),
        "prior_month_persistence": _metric_summary(actual, persistence),
        "expanding_historical_mean": _metric_summary(actual, history_mean),
    }


def _panel_diagnostics(frame: pd.DataFrame) -> dict[str, object]:
    product_columns = sorted(column for column in frame if column.startswith("product__"))
    if not product_columns:
        return {"product_columns": 0, "stable_90pct_products": 0, "median_product_coverage": 0.0}
    coverage = frame[product_columns].notna().mean()
    present = frame[product_columns].notna().astype(int)
    transitions = present.diff().abs().iloc[1:].sum(axis=1) if len(present) > 1 else pd.Series(dtype=float)
    return {
        "product_columns": len(product_columns),
        "stable_90pct_products": int((coverage >= 0.90).sum()),
        "median_product_coverage": float(coverage.median()),
        "median_monthly_entry_exit_count": float(transitions.median()) if len(transitions) else 0.0,
        "maximum_monthly_entry_exit_count": int(transitions.max()) if len(transitions) else 0,
    }


def train_bundle(
    training: pd.DataFrame,
    output_dir: Path,
    target_column: str = "target_mom_pct",
    *,
    validate: bool = False,
    vintage: str | None = None,
    training_metadata: dict[str, object] | None = None,
    bundle_version: str = "reconstructed-v2",
) -> dict[str, object]:
    required = {"target_month", target_column}
    missing = required - set(training.columns)
    if missing:
        raise ValueError(f"training matrix missing columns: {sorted(missing)}")
    frame = training.copy().sort_values("target_month").reset_index(drop=True)
    frame[target_column] = pd.to_numeric(frame[target_column], errors="raise")
    if len(frame) < 24:
        raise ValueError("at least 24 monthly observations are required for reconstructed training")
    output_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    specs = model_specs_for_vintage(vintage)
    for spec in specs:
        columns = _columns_for(frame, spec)
        if not columns:
            raise ValueError(f"no features available for {spec.key} with prefixes {spec.prefixes}")
        X = frame[columns].astype(float)
        y = frame[target_column].astype(float)
        if spec.required_observed_prefix:
            observed_columns = [c for c in columns if c.startswith(spec.required_observed_prefix)]
            observed = X[observed_columns].notna().any(axis=1)
            X = X.loc[observed].reset_index(drop=True)
            y = y.loc[observed].reset_index(drop=True)
        estimator = _make_estimator(spec.estimator_kind, len(X), len(columns))
        metrics = _oof_metrics(estimator, X, y)
        estimator.fit(X, y)
        filename = f"{spec.key}.joblib"
        joblib.dump(estimator, output_dir / filename)
        entries.append(
            {
                "key": spec.key,
                "label": spec.label,
                "estimator_kind": spec.estimator_kind,
                "file": filename,
                "feature_columns": columns,
                "training_rows": len(X),
                "metrics": metrics,
                "uses_economic_features": any(column.startswith("econ__") for column in columns),
                "available_vintages": list(spec.vintages),
                "information_set": spec.information_set,
                "required_observed_prefix": spec.required_observed_prefix,
            }
        )
    fitted_keys = {entry["key"] for entry in entries}
    core_keys = {spec.key for spec in CORE_MODEL_SPECS}
    benchmark_keys = {spec.key for spec in FINAL_BENCHMARK_SPECS}
    checks = {
        "at_least_36_months": len(frame) >= 36,
        "expected_models_fitted": len(entries) == len(specs),
        "six_core_models_fitted": core_keys.issubset(fitted_keys),
        "final_twentieth_benchmarks_fitted": vintage != "final" or benchmark_keys.issubset(fitted_keys),
        "at_least_12_oof_predictions_each": all(int(entry["metrics"]["n_oof"]) >= 12 for entry in entries),
        "all_metrics_finite": all(
            np.isfinite(float(entry["metrics"][key]))
            for entry in entries for key in ("mae", "rmse", "bias", "directional_accuracy")
        ),
        "publication_precedes_actual": bool(
            training_metadata and training_metadata.get("actual_after_cutoff", False)
        ),
        "pseudo_real_time_label_present": bool(
            training_metadata and training_metadata.get("realtime_status") == "pseudo_real_time"
        ),
    }
    validated = bool(validate and all(checks.values()))
    manifest: dict[str, object] = {
        "bundle_version": f"{bundle_version}-{vintage}" if vintage else bundle_version,
        "provenance": "reconstructed",
        "validated": validated,
        "validation_scope": "operational_and_leakage_checks_not_model_superiority",
        "validation_checks": checks,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": len(frame),
        "training_start": str(frame["target_month"].min()),
        "training_end": str(frame["target_month"].max()),
        "training_actual_cutoff": str(pd.to_datetime(frame["actual_published_at"], utc=True).max()) if "actual_published_at" in frame else None,
        "training_hash": stable_hash(frame.fillna("__NA__").to_dict(orient="records")),
        "target_column": target_column,
        "vintage": vintage,
        "models": entries,
        "baselines": _baseline_metrics(frame[target_column].astype(float)),
        "panel_diagnostics": _panel_diagnostics(frame),
        "training_metadata": training_metadata or {},
        "warning": "These estimators are reconstructed candidates, not recovered v0.4 fitted objects.",
    }
    atomic_write_text(output_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def load_bundle(bundle_dir: Path, require_validated: bool = True) -> tuple[dict[str, object], dict[str, object]]:
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"model bundle manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if require_validated and not manifest.get("validated", False):
        raise RuntimeError("model bundle exists but is not marked validated")
    models = {entry["key"]: joblib.load(bundle_dir / entry["file"]) for entry in manifest["models"]}
    return manifest, models


def predict_bundle(bundle_dir: Path, features: pd.DataFrame, require_validated: bool = True) -> list[dict[str, object]]:
    manifest, models = load_bundle(bundle_dir, require_validated=require_validated)
    predictions: list[dict[str, object]] = []
    for entry in manifest["models"]:
        columns = entry["feature_columns"]
        X = features.reindex(columns=columns).apply(pd.to_numeric, errors="coerce")
        required_prefix = entry.get("required_observed_prefix")
        if required_prefix:
            required = [column for column in columns if column.startswith(required_prefix)]
            if not required or not X[required].notna().any(axis=1).all():
                continue
        estimate = float(models[entry["key"]].predict(X)[0])
        predictions.append(
            {
                "model_key": entry["key"],
                "model_label": entry["label"],
                "model_version": manifest["bundle_version"],
                "model_provenance": manifest["provenance"],
                "estimate_mom_pct": estimate,
            }
        )
    return predictions
