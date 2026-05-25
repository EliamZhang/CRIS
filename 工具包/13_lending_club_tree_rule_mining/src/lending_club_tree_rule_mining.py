# -*- coding: utf-8 -*-
"""
Decision Tree Rule Mining

A production-ready Python entrypoint converted and refactored from the original
notebook: 基于决策树生成规则：自动化挖掘.

Default usage:
    python run.py

Custom usage:
    python run.py --input input/lending_club_loan_two.csv --output output --max-depth 3
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import re
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn import metrics, tree
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# Avoid Chinese minus/sign rendering issues in plots. Font fallback depends on local env.
plt.rcParams["axes.unicode_minus"] = False


@dataclass
class Config:
    input_path: str = "input/lending_club_loan_two.csv"
    output_dir: str = "output"
    target_col: str = "loan_status"
    positive_label: str = "Charged Off"
    negative_label: str = "Fully Paid"
    drop_cols: Tuple[str, ...] = (
        "issue_d",
        "address",
        "emp_title",
        "earliest_cr_line",
        "title",
    )
    missing_value: int = -9999
    test_size: float = 0.2
    random_state: int = 42
    max_depth: int = 3
    min_samples_leaf: float = 0.05
    min_samples_split: float = 0.05
    criterion: str = "gini"
    splitter: str = "best"


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Decision tree based automatic rule mining.")
    parser.add_argument("--input", default=Config.input_path, help="Input CSV path.")
    parser.add_argument("--output", default=Config.output_dir, help="Output directory.")
    parser.add_argument("--target-col", default=Config.target_col, help="Target column name.")
    parser.add_argument("--positive-label", default=Config.positive_label, help="Positive/bad label before mapping.")
    parser.add_argument("--negative-label", default=Config.negative_label, help="Negative/good label before mapping.")
    parser.add_argument("--test-size", type=float, default=Config.test_size, help="Test set ratio.")
    parser.add_argument("--random-state", type=int, default=Config.random_state, help="Random seed.")
    parser.add_argument("--max-depth", type=int, default=Config.max_depth, help="Decision tree max_depth.")
    parser.add_argument("--min-samples-leaf", type=float, default=Config.min_samples_leaf, help="Decision tree min_samples_leaf.")
    parser.add_argument("--min-samples-split", type=float, default=Config.min_samples_split, help="Decision tree min_samples_split.")
    args = parser.parse_args()

    return Config(
        input_path=args.input,
        output_dir=args.output,
        target_col=args.target_col,
        positive_label=args.positive_label,
        negative_label=args.negative_label,
        test_size=args.test_size,
        random_state=args.random_state,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        min_samples_split=args.min_samples_split,
    )


def build_config(args: Config) -> Config:
    return args


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def load_data(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path, low_memory=False)
    # Some CSV exports contain trailing blank rows. Drop rows that are completely empty
    # before profiling and modeling, otherwise missing-rate reports will be distorted.
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def simple_statistics(df: pd.DataFrame) -> pd.DataFrame:
    stats = []
    for col in df.columns:
        mode_pct = df[col].value_counts(normalize=True, dropna=False).iloc[0] * 100 if len(df[col]) else np.nan
        stats.append(
            {
                "feature": col,
                "unique_values": df[col].nunique(dropna=True),
                "null_pct": df[col].isna().mean() * 100,
                "mode_pct": mode_pct,
                "dtype": str(df[col].dtype),
            }
        )
    return pd.DataFrame(stats).sort_values(["null_pct", "unique_values"], ascending=[False, False])


def save_data_exploration(df: pd.DataFrame, cfg: Config, output_dir: Path) -> None:
    simple_statistics(df).to_csv(output_dir / "feature_summary.csv", index=False, encoding="utf-8-sig")
    df.describe(include="all").transpose().to_csv(output_dir / "data_describe.csv", encoding="utf-8-sig")

    target_dist = (
        df[cfg.target_col]
        .value_counts(dropna=False)
        .rename_axis(cfg.target_col)
        .reset_index(name="sample_cnt")
    )
    target_dist["sample_pct"] = target_dist["sample_cnt"] / target_dist["sample_cnt"].sum()
    target_dist.to_csv(output_dir / "target_distribution.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(8, 5))
    df[cfg.target_col].value_counts(dropna=False).plot(kind="bar")
    plt.title("Target Distribution")
    plt.xlabel(cfg.target_col)
    plt.ylabel("Sample Count")
    plt.tight_layout()
    plt.savefig(output_dir / "target_distribution.png", dpi=200)
    plt.close()


def encode_features(df: pd.DataFrame, cfg: Config, output_dir: Path) -> Tuple[pd.DataFrame, List[str], Dict[str, Dict[str, int]]]:
    data = df.copy()

    label_map = {cfg.negative_label: 0, cfg.positive_label: 1}
    data[cfg.target_col] = data[cfg.target_col].map(label_map)
    data = data[data[cfg.target_col].notna()].copy()
    data[cfg.target_col] = data[cfg.target_col].astype(int)

    excluded = set(cfg.drop_cols) | {cfg.target_col}
    feature_cols = [c for c in data.columns if c not in excluded]

    object_cols = data[feature_cols].select_dtypes(include=["object", "category"]).columns.tolist()
    encoding_rows = []
    encoding_maps: Dict[str, Dict[str, int]] = {}

    for col in object_cols:
        le = LabelEncoder()
        filled = data[col].astype("object").where(data[col].notna(), "__MISSING__").astype(str)
        data[col] = le.fit_transform(filled)
        mapping = {label: int(code) for code, label in enumerate(le.classes_)}
        encoding_maps[col] = mapping
        encoding_rows.extend({"feature": col, "raw_value": k, "encoded_value": v} for k, v in mapping.items())

    data[feature_cols] = data[feature_cols].fillna(cfg.missing_value)

    pd.DataFrame(encoding_rows).to_csv(output_dir / "category_encoding_mapping.csv", index=False, encoding="utf-8-sig")
    return data, feature_cols, encoding_maps


def fit_decision_tree(X_train: pd.DataFrame, y_train: pd.Series, cfg: Config) -> tree.DecisionTreeClassifier:
    model = tree.DecisionTreeClassifier(
        criterion=cfg.criterion,
        splitter=cfg.splitter,
        random_state=cfg.random_state,
        max_depth=cfg.max_depth,
        min_samples_leaf=cfg.min_samples_leaf,
        min_samples_split=cfg.min_samples_split,
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(
    model: tree.DecisionTreeClassifier,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    output_dir: Path,
) -> pd.DataFrame:
    rows = []
    for dataset_name, X_part, y_part in [
        ("train", X_train, y_train),
        ("test", X_test, y_test),
    ]:
        pred = model.predict(X_part)
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X_part)[:, 1]
            auc = metrics.roc_auc_score(y_part, proba) if y_part.nunique() > 1 else np.nan
        else:
            auc = np.nan
        rows.append(
            {
                "dataset": dataset_name,
                "sample_cnt": int(len(y_part)),
                "bad_cnt": int(y_part.sum()),
                "bad_rate": float(y_part.mean()),
                "accuracy": float(metrics.accuracy_score(y_part, pred)),
                "precision": float(metrics.precision_score(y_part, pred, zero_division=0)),
                "recall": float(metrics.recall_score(y_part, pred, zero_division=0)),
                "f1": float(metrics.f1_score(y_part, pred, zero_division=0)),
                "auc": float(auc) if not pd.isna(auc) else np.nan,
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(output_dir / "model_metrics.csv", index=False, encoding="utf-8-sig")
    return result


def _format_threshold(v: float) -> str:
    return f"{v:.6g}"


def _format_condition(feature: str, operator: str, threshold: float) -> str:
    return f"{feature} {operator} {_format_threshold(threshold)}"


def _format_readable_condition(
    feature: str,
    operator: str,
    threshold: float,
    encoding_maps: Dict[str, Dict[str, int]] | None = None,
    max_values: int = 30,
) -> str:
    """Convert LabelEncoder split conditions back to raw category sets when possible."""
    if not encoding_maps or feature not in encoding_maps:
        return _format_condition(feature, operator, threshold)

    mapping = encoding_maps[feature]
    boundary = int(np.floor(threshold))
    if operator == "<=":
        selected = [(raw, code) for raw, code in mapping.items() if code <= boundary]
    else:
        selected = [(raw, code) for raw, code in mapping.items() if code > boundary]

    selected = [raw for raw, _ in sorted(selected, key=lambda x: x[1])]
    if len(selected) <= max_values:
        values = ", ".join(repr(v) for v in selected)
        return f"{feature} in [{values}]"
    return f"{feature} encoded {operator} {_format_threshold(threshold)}; raw values too many, see category_encoding_mapping.csv"


def _copy_constraints(constraints: Dict[str, dict]) -> Dict[str, dict]:
    return {feature: value.copy() for feature, value in constraints.items()}


def _update_constraints(
    constraints: Dict[str, dict],
    feature: str,
    operator: str,
    threshold: float,
    encoding_maps: Dict[str, Dict[str, int]] | None,
) -> Dict[str, dict]:
    new_constraints = _copy_constraints(constraints)
    item = new_constraints.setdefault(feature, {})
    if encoding_maps and feature in encoding_maps:
        min_code = item.get("min_code", -np.inf)
        max_code = item.get("max_code", np.inf)
        boundary = int(np.floor(threshold))
        if operator == "<=":
            max_code = min(max_code, boundary)
        else:
            min_code = max(min_code, boundary + 1)
        item["min_code"] = min_code
        item["max_code"] = max_code
    else:
        if operator == "<=":
            item["max_value"] = min(item.get("max_value", np.inf), threshold)
        else:
            item["min_value"] = max(item.get("min_value", -np.inf), threshold)
    return new_constraints


def _build_simplified_rule(
    constraints: Dict[str, dict],
    feature_order: List[str],
    encoding_maps: Dict[str, Dict[str, int]] | None,
    max_values: int = 30,
) -> str:
    parts: List[str] = []
    for feature in feature_order:
        if feature not in constraints:
            continue
        item = constraints[feature]
        if encoding_maps and feature in encoding_maps:
            mapping = encoding_maps[feature]
            min_code = item.get("min_code", -np.inf)
            max_code = item.get("max_code", np.inf)
            selected = [
                (raw, code)
                for raw, code in mapping.items()
                if code >= min_code and code <= max_code
            ]
            selected = [raw for raw, _ in sorted(selected, key=lambda x: x[1])]
            if len(selected) <= max_values:
                values = ", ".join(repr(v) for v in selected)
                parts.append(f"{feature} in [{values}]")
            else:
                parts.append(f"{feature} encoded in [{min_code}, {max_code}]; raw values too many, see category_encoding_mapping.csv")
        else:
            min_value = item.get("min_value", -np.inf)
            max_value = item.get("max_value", np.inf)
            if np.isfinite(min_value) and np.isfinite(max_value):
                parts.append(f"{_format_threshold(min_value)} < {feature} <= {_format_threshold(max_value)}")
            elif np.isfinite(min_value):
                parts.append(f"{feature} > {_format_threshold(min_value)}")
            elif np.isfinite(max_value):
                parts.append(f"{feature} <= {_format_threshold(max_value)}")
    return " and ".join(parts) if parts else "ALL"


def extract_tree_rules(
    model: tree.DecisionTreeClassifier,
    feature_names: Iterable[str],
    total_sample: int,
    total_bad: float,
    total_bad_rate: float,
    encoding_maps: Dict[str, Dict[str, int]] | None = None,
) -> pd.DataFrame:
    tree_ = model.tree_
    feature_names = list(feature_names)
    rules: List[dict] = []

    # model.classes_ tells us which position corresponds to class 0 / 1.
    class_to_index = {int(cls): idx for idx, cls in enumerate(model.classes_)}
    good_idx = class_to_index.get(0, 0)
    bad_idx = class_to_index.get(1, 1 if len(model.classes_) > 1 else 0)

    def recurse(node: int, clauses: List[str], constraints: Dict[str, dict]) -> None:
        if tree_.feature[node] != tree._tree.TREE_UNDEFINED:
            feature = feature_names[tree_.feature[node]]
            threshold = tree_.threshold[node]
            recurse(
                tree_.children_left[node],
                clauses + [_format_condition(feature, "<=", threshold)],
                _update_constraints(constraints, feature, "<=", threshold, encoding_maps),
            )
            recurse(
                tree_.children_right[node],
                clauses + [_format_condition(feature, ">", threshold)],
                _update_constraints(constraints, feature, ">", threshold, encoding_maps),
            )
            return

        # In recent scikit-learn versions, tree_.value stores class proportions.
        # Use weighted_n_node_samples to recover sample counts robustly.
        node_weight = float(tree_.weighted_n_node_samples[node])
        values = tree_.value[node][0] * node_weight
        good = float(values[good_idx])
        bad = float(values[bad_idx]) if len(values) > bad_idx else 0.0
        sample_cnt = good + bad
        bad_rate = bad / sample_cnt if sample_cnt else 0.0
        hit_rate = sample_cnt / total_sample if total_sample else 0.0
        recall_rate = bad / total_bad if total_bad else 0.0
        lift = bad_rate / total_bad_rate if total_bad_rate else 0.0

        rules.append(
            {
                "leaf_id": node,
                "sample_cnt": round(sample_cnt, 6),
                "good_cnt": round(good, 6),
                "bad_cnt": round(bad, 6),
                "bad_rate": round(bad_rate, 6),
                "hit_rate": round(hit_rate, 6),
                "recall_rate": round(recall_rate, 6),
                "lift": round(lift, 6),
                "rule": " and ".join(clauses) if clauses else "ALL",
                "rule_readable": _build_simplified_rule(constraints, feature_names, encoding_maps),
            }
        )

    recurse(0, [], {})
    rule_df = pd.DataFrame(rules).sort_values(["bad_rate", "lift", "sample_cnt"], ascending=[False, False, False])
    return rule_df.reset_index(drop=True)


def save_tree_artifacts(model: tree.DecisionTreeClassifier, feature_cols: List[str], output_dir: Path) -> None:
    dot_text = tree.export_graphviz(
        model,
        out_file=None,
        feature_names=feature_cols,
        class_names=["Fully Paid", "Charged Off"],
        filled=True,
        rounded=True,
        special_characters=True,
    )
    (output_dir / "decision_tree.dot").write_text(dot_text, encoding="utf-8")

    plt.figure(figsize=(24, 12))
    tree.plot_tree(
        model,
        feature_names=feature_cols,
        class_names=["Fully Paid", "Charged Off"],
        filled=True,
        rounded=True,
        fontsize=8,
    )
    plt.tight_layout()
    plt.savefig(output_dir / "decision_tree.png", dpi=200)
    plt.close()


def save_environment_info(cfg: Config, output_dir: Path) -> None:
    info = {
        "config": asdict(cfg),
        "python": sys.version,
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
    }
    (output_dir / "run_config_and_environment.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


def run(cfg: Config) -> None:
    input_path = Path(cfg.input_path)
    output_dir = Path(cfg.output_dir)
    ensure_output_dir(output_dir)

    print(f"[1/6] Loading data: {input_path}")
    df = load_data(input_path)

    print("[2/6] Saving data exploration outputs")
    save_data_exploration(df, cfg, output_dir)

    print("[3/6] Encoding features and preparing modeling data")
    data, feature_cols, encoding_maps = encode_features(df, cfg, output_dir)
    X = data[feature_cols]
    y = data[cfg.target_col]

    x_train, x_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=cfg.test_size,
        random_state=cfg.random_state,
        stratify=y if y.nunique() == 2 else None,
    )

    print("[4/6] Training decision tree")
    model = fit_decision_tree(x_train, y_train, cfg)

    print("[5/6] Extracting rules and evaluating model")
    metrics_df = evaluate_model(model, X_train=x_train, X_test=x_test, y_train=y_train, y_test=y_test, output_dir=output_dir)
    total_sample = int(y_train.count())
    total_bad = float(y_train.sum())
    total_bad_rate = float(y_train.mean())
    rule_df = extract_tree_rules(model, feature_cols, total_sample, total_bad, total_bad_rate, encoding_maps)
    rule_df.to_csv(output_dir / "rule_mining_results.csv", index=False, encoding="utf-8-sig")

    print("[6/6] Saving tree chart and environment info")
    save_tree_artifacts(model, feature_cols, output_dir)
    save_environment_info(cfg, output_dir)

    print("\nDone. Main outputs:")
    print(f"- {output_dir / 'rule_mining_results.csv'}")
    print(f"- {output_dir / 'model_metrics.csv'}")
    print(f"- {output_dir / 'decision_tree.png'}")
    print("\nTop rules by bad_rate:")
    show_cols = ["bad_rate", "hit_rate", "recall_rate", "lift", "rule_readable"]
    print(rule_df[show_cols].head(10).to_string(index=False))
    print("\nModel metrics:")
    print(metrics_df.to_string(index=False))


EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_COLS = 16_384


def _sheet_name_from_path(base_dir: Path, csv_path: Path) -> str:
    rel = csv_path.relative_to(base_dir)
    raw = "__".join(rel.with_suffix("").parts)
    safe = re.sub(r"[:\/?*\[\]]+", "_", raw).strip("_")
    return (safe or "sheet")[:31]


def consolidate_csv_outputs(output_dir: Path) -> Path | None:
    csv_files = sorted(output_dir.rglob("*.csv"))
    if not csv_files:
        return None

    excel_path = output_dir / "summary_report.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        used_names: set[str] = set()
        for csv_path in csv_files:
            df = pd.read_csv(csv_path)
            base_name = _sheet_name_from_path(output_dir, csv_path)
            row_parts = max((max(len(df), 1) - 1) // (EXCEL_MAX_ROWS - 1) + 1, 1)
            col_parts = max((max(len(df.columns), 1) - 1) // EXCEL_MAX_COLS + 1, 1)
            for row_idx in range(row_parts):
                row_start = row_idx * (EXCEL_MAX_ROWS - 1)
                row_end = row_start + (EXCEL_MAX_ROWS - 1)
                for col_idx in range(col_parts):
                    col_start = col_idx * EXCEL_MAX_COLS
                    col_end = col_start + EXCEL_MAX_COLS
                    part_df = df.iloc[row_start:row_end, col_start:col_end]
                    suffix = ""
                    if row_parts > 1 or col_parts > 1:
                        suffix = f"_{row_idx + 1}_{col_idx + 1}"
                    sheet_name = f"{base_name[:31 - len(suffix)]}{suffix}"
                    while sheet_name in used_names:
                        sheet_name = f"{sheet_name[:28]}_{len(used_names) % 1000:03d}"[:31]
                    used_names.add(sheet_name)
                    part_df.to_excel(writer, sheet_name=sheet_name, index=False)

    for csv_path in csv_files:
        csv_path.unlink()

    for extra_excel in output_dir.rglob("*.xlsx"):
        if extra_excel != excel_path:
            extra_excel.unlink()

    return excel_path
