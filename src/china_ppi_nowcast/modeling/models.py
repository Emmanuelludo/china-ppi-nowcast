"""Train and load six transparent reconstructed candidate models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
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


MODEL_SPECS = (
    ModelSpec("category_factor_regression", "Category-factor regression", ("category__",), "factor_ridge"),
    ModelSpec("gradient_boosting", "Gradient boosting", ("global__", "category__", "product__", "missing__"), "hist_gradient_boosting"),
    ModelSpec("economic_ml_hybrid", "Economic + ML hybrid", ("global__", "category__", "econ__"), "voting_hybrid"),
    ModelSpec("product_level_ridge", "Product-level ridge", ("product__", "missing__"), "ridge"),
    ModelSpec("sector_first_aggregation", "Sector-first aggregation", ("global__", "category__"), "ridge"),
    ModelSpec("random_forest", "Random forest", ("global__", "category__", "product__", "missing__"), "random_forest"),
)


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
    raise ValueError(f"unknown estimator kind: {kind}")


def _columns_for(frame: pd.DataFrame, spec: ModelSpec) -> list[str]:
    return sorted(
        column for column in frame.columns
        if column.startswith(spec.prefixes) and pd.api.types.is_numeric_dtype(frame[column])
    )


def _oof_metrics(estimator: object, X: pd.DataFrame, y: pd.Series) -> dict[str, float | int]:
    splits = min(5, max(2, len(X) // 6))
    cv = TimeSeriesSplit(n_splits=splits)
    truth: list[float] = []
    predicted: list[float] = []
    for train_idx, test_idx in cv.split(X):
        fitted = clone(estimator).fit(X.iloc[train_idx], y.iloc[train_idx])
        truth.extend(y.iloc[test_idx].astype(float).tolist())
        predicted.extend(np.asarray(fitted.predict(X.iloc[test_idx]), dtype=float).tolist())
    actual = np.asarray(truth)
    estimate = np.asarray(predicted)
    error = estimate - actual
    return {
        "n_oof": int(len(actual)),
        "mae": float(mean_absolute_error(actual, estimate)),
        "rmse": float(mean_squared_error(actual, estimate) ** 0.5),
        "bias": float(error.mean()),
        "directional_accuracy": float(np.mean(np.sign(actual) == np.sign(estimate))),
    }


def train_bundle(training: pd.DataFrame, output_dir: Path, target_column: str = "target_mom_pct") -> dict[str, object]:
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
    for spec in MODEL_SPECS:
        columns = _columns_for(frame, spec)
        if not columns:
            raise ValueError(f"no features available for {spec.key} with prefixes {spec.prefixes}")
        X = frame[columns].astype(float)
        y = frame[target_column].astype(float)
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
                "metrics": metrics,
                "uses_economic_features": any(column.startswith("econ__") for column in columns),
            }
        )
    manifest: dict[str, object] = {
        "bundle_version": "reconstructed-v1",
        "provenance": "reconstructed",
        "validated": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": len(frame),
        "training_start": str(frame["target_month"].min()),
        "training_end": str(frame["target_month"].max()),
        "training_hash": stable_hash(frame.fillna("__NA__").to_dict(orient="records")),
        "target_column": target_column,
        "models": entries,
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
