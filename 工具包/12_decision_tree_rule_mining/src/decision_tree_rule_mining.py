"""
Decision Tree Rule Miner
========================

基于决策树自动挖掘多变量组合规则，并输出规则指标、模型指标和可视化图片。

运行方式：
    python run.py

默认输入：
    input/lending_club_loan_two.csv

默认输出：
    output/tables/*.csv / *.md
    output/figures/*.png
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import metrics, tree
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import _tree

warnings.filterwarnings("ignore")


@dataclass
class Config:
    """项目配置层：只需要改这里，就可以复用到其他类似数据集。"""

    input_path: str = "input/lending_club_loan_two.csv"
    output_dir: str = "output"
    target_col: str = "loan_status"
    target_mapping: Dict[str, int] = None
    exclude_cols: Tuple[str, ...] = (
        "loan_status",
        "issue_d",
        "address",
        "emp_title",
        "earliest_cr_line",
        "title",
    )
    test_size: float = 0.2
    random_state: int = 42
    tree_criterion: str = "gini"
    tree_splitter: str = "best"
    tree_max_depth: int = 3
    tree_min_samples_leaf: float = 0.05
    tree_min_samples_split: float = 0.05
    positive_label: int = 1
    negative_label: int = 0
    grid_max_depths: Tuple[int, ...] = (2, 3, 4, 5)
    grid_min_samples_leaf: Tuple[float, ...] = (0.01, 0.03, 0.05)
    grid_min_samples_split: Tuple[float, ...] = (0.02, 0.05, 0.1)
    grid_criteria: Tuple[str, ...] = ("gini", "entropy")
    grid_top_n: int = 20

    def __post_init__(self) -> None:
        if self.target_mapping is None:
            self.target_mapping = {"Fully Paid": 0, "Charged Off": 1}


DEFAULT_CONFIG = Config()


def ensure_dirs(output_dir: Path) -> Tuple[Path, Path]:
    """创建输出目录。"""
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    return tables_dir, figures_dir


def simple_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """输出每个字段的基础统计：唯一值、缺失率、众数占比和数据类型。"""
    stats = []
    for col in df.columns:
        mode_pct = df[col].value_counts(normalize=True, dropna=False).values[0] * 100
        stats.append(
            {
                "feature": col,
                "unique_values": df[col].nunique(dropna=True),
                "percentage_of_null": df[col].isnull().mean() * 100,
                "percentage_of_mode": mode_pct,
                "type": str(df[col].dtype),
            }
        )
    return pd.DataFrame(stats).sort_values("unique_values", ascending=False)


def save_data_profile(df: pd.DataFrame, tables_dir: Path) -> None:
    """保存数据探索结果。"""
    df.head(20).to_csv(tables_dir / "data_preview.csv", index=False)
    df.describe(include="all").T.to_csv(tables_dir / "data_describe.csv", index=True)
    simple_statistics(df).to_csv(tables_dir / "simple_statistics.csv", index=False)

    dtypes_df = pd.DataFrame(
        {
            "feature": df.columns,
            "dtype": [str(dtype) for dtype in df.dtypes],
            "missing_cnt": df.isnull().sum().values,
            "missing_rate": df.isnull().mean().values,
        }
    )
    dtypes_df.to_csv(tables_dir / "field_dtypes_and_missing.csv", index=False)


def plot_target_distribution(df: pd.DataFrame, target_col: str, figures_dir: Path) -> None:
    """保存目标变量分布图。"""
    plt.figure(figsize=(8, 5))
    df[target_col].value_counts(dropna=False).sort_index().plot(kind="bar")
    plt.title("Target Distribution")
    plt.xlabel(target_col)
    plt.ylabel("Sample Count")
    plt.tight_layout()
    plt.savefig(figures_dir / "target_distribution.png", dpi=160)
    plt.close()


def encode_categorical_features(
    df: pd.DataFrame, feature_cols: Iterable[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    对 object/category/string 类型变量做 LabelEncoder 编码。

    注意：LabelEncoder 编码只适合树模型快速挖掘规则使用；如果用于线性模型或强解释性建模，
    建议改成 One-Hot / WOE / Target Encoding 等方式。
    """
    encoded_df = df.copy()
    mapping_rows = []

    for col in feature_cols:
        if encoded_df[col].dtype == "object" or str(encoded_df[col].dtype).startswith("string"):
            encoder = LabelEncoder()
            values = encoded_df[col].astype("string").fillna("__MISSING__")
            encoded_df[col] = encoder.fit_transform(values)
            for raw_value, code in zip(encoder.classes_, encoder.transform(encoder.classes_)):
                mapping_rows.append({"feature": col, "raw_value": raw_value, "encoded_value": int(code)})

    mapping_df = pd.DataFrame(mapping_rows)
    return encoded_df, mapping_df


def prepare_model_data(df: pd.DataFrame, config: Config) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """目标变量转换、特征选择、类别编码、缺失填充。"""
    working_df = df.copy()

    working_df[config.target_col] = working_df[config.target_col].map(config.target_mapping)
    working_df = working_df[working_df[config.target_col].notnull()].copy()
    working_df[config.target_col] = working_df[config.target_col].astype(int)

    feature_cols = working_df.columns.difference(list(config.exclude_cols)).tolist()
    encoded_df, mapping_df = encode_categorical_features(working_df, feature_cols)
    encoded_df = encoded_df.fillna(-9999)

    x = encoded_df[feature_cols]
    y = encoded_df[config.target_col]
    return x, y, mapping_df


def train_decision_tree(x_train: pd.DataFrame, y_train: pd.Series, config: Config) -> tree.DecisionTreeClassifier:
    """训练决策树模型。"""
    return build_tree_model(
        x_train=x_train,
        y_train=y_train,
        criterion=config.tree_criterion,
        max_depth=config.tree_max_depth,
        min_samples_leaf=config.tree_min_samples_leaf,
        min_samples_split=config.tree_min_samples_split,
        random_state=config.random_state,
        splitter=config.tree_splitter,
    )


def build_tree_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    criterion: str,
    max_depth: int,
    min_samples_leaf: float,
    min_samples_split: float,
    random_state: int,
    splitter: str = "best",
) -> tree.DecisionTreeClassifier:
    model = tree.DecisionTreeClassifier(
        criterion=criterion,
        splitter=splitter,
        random_state=random_state,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        min_samples_split=min_samples_split,
    )
    model.fit(x_train, y_train)
    return model


def evaluate_model(
    model: tree.DecisionTreeClassifier,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    positive_label: int,
) -> pd.DataFrame:
    """输出训练集和测试集的模型评估指标。"""
    rows = []
    for dataset_name, x_data, y_true in [
        ("train", x_train, y_train),
        ("test", x_test, y_test),
    ]:
        y_pred = model.predict(x_data)
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(x_data)[:, list(model.classes_).index(positive_label)]
            auc = metrics.roc_auc_score(y_true, y_prob)
        else:
            auc = np.nan
        rows.append(
            {
                "dataset": dataset_name,
                "sample_cnt": int(len(y_true)),
                "bad_cnt": int((y_true == positive_label).sum()),
                "bad_rate": float((y_true == positive_label).mean()),
                "auc": float(auc),
                "accuracy": float(metrics.accuracy_score(y_true, y_pred)),
                "precision": float(metrics.precision_score(y_true, y_pred, zero_division=0)),
                "recall": float(metrics.recall_score(y_true, y_pred, zero_division=0)),
                "f1": float(metrics.f1_score(y_true, y_pred, zero_division=0)),
            }
        )
    return pd.DataFrame(rows)


def extract_leaf_paths(model: tree.DecisionTreeClassifier, feature_names: List[str]) -> Dict[int, List[str]]:
    """抽取每个叶子节点对应的决策路径。"""
    tree_ = model.tree_
    leaf_paths: Dict[int, List[str]] = {}

    def recurse(node: int, path: List[str]) -> None:
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            feature = feature_names[tree_.feature[node]]
            threshold = tree_.threshold[node]
            recurse(tree_.children_left[node], path + [f"{feature} <= {threshold:.6g}"])
            recurse(tree_.children_right[node], path + [f"{feature} > {threshold:.6g}"])
        else:
            leaf_paths[node] = path

    recurse(0, [])
    return leaf_paths


def extract_tree_rules(
    model: tree.DecisionTreeClassifier,
    x_data: pd.DataFrame,
    y_data: pd.Series,
    positive_label: int,
) -> pd.DataFrame:
    """
    基于指定样本真实落叶结果，统计每条规则的 bad_rate / hit_rate / recall_rate / lift。
    """
    leaf_paths = extract_leaf_paths(model, x_data.columns.tolist())
    leaf_ids = model.apply(x_data)

    total_sample = len(y_data)
    total_bad = int((y_data == positive_label).sum())
    total_badrate = total_bad / total_sample if total_sample else np.nan

    rows = []
    for leaf_id, conditions in leaf_paths.items():
        mask = leaf_ids == leaf_id
        sample_cnt = int(mask.sum())
        bad_cnt = int((y_data[mask] == positive_label).sum())
        good_cnt = int(sample_cnt - bad_cnt)
        bad_rate = bad_cnt / sample_cnt if sample_cnt else np.nan
        hit_rate = sample_cnt / total_sample if total_sample else np.nan
        recall_rate = bad_cnt / total_bad if total_bad else np.nan
        lift = bad_rate / total_badrate if total_badrate else np.nan

        rows.append(
            {
                "leaf_id": int(leaf_id),
                "sample_cnt": sample_cnt,
                "good_cnt": good_cnt,
                "bad_cnt": bad_cnt,
                "bad_rate": bad_rate,
                "hit_rate": hit_rate,
                "recall_rate": recall_rate,
                "lift": lift,
                "rule_name": " and ".join(conditions),
            }
        )

    return pd.DataFrame(rows).sort_values(["bad_rate", "lift"], ascending=False).reset_index(drop=True)


def score_grid_candidate(metrics_df: pd.DataFrame, rule_df: pd.DataFrame) -> float:
    if metrics_df.empty:
        return -np.inf
    metrics_map = metrics_df.set_index("dataset").to_dict(orient="index")
    test_auc = float(metrics_map.get("test", {}).get("auc", np.nan))
    test_recall = float(metrics_map.get("test", {}).get("recall", np.nan))
    train_auc = float(metrics_map.get("train", {}).get("auc", np.nan))
    best_lift = float(rule_df["lift"].max()) if not rule_df.empty else np.nan
    best_bad_rate = float(rule_df["bad_rate"].max()) if not rule_df.empty else np.nan
    overfit_penalty = abs(train_auc - test_auc) if not np.isnan(train_auc) and not np.isnan(test_auc) else 0.0
    score = (
        (0 if np.isnan(test_auc) else test_auc)
        + 0.05 * max((0 if np.isnan(best_lift) else best_lift) - 1.0, 0.0)
        + 0.03 * (0 if np.isnan(test_recall) else test_recall)
        + 0.02 * (0 if np.isnan(best_bad_rate) else best_bad_rate)
        - 0.10 * overfit_penalty
    )
    return float(score)


def run_tree_grid_search(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    config: Config,
    tables_dir: Path,
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for criterion, max_depth, min_leaf, min_split in itertools.product(
        config.grid_criteria,
        config.grid_max_depths,
        config.grid_min_samples_leaf,
        config.grid_min_samples_split,
    ):
        model = build_tree_model(
            x_train,
            y_train,
            criterion=criterion,
            max_depth=max_depth,
            min_samples_leaf=min_leaf,
            min_samples_split=min_split,
            random_state=config.random_state,
        )
        metrics_df = evaluate_model(model, x_train, y_train, x_test, y_test, config.positive_label)
        train_rule_df = extract_tree_rules(model, x_train, y_train, config.positive_label)
        test_rule_df = extract_tree_rules(model, x_test, y_test, config.positive_label)
        metric_map = metrics_df.set_index("dataset").to_dict(orient="index")
        best_rule = test_rule_df.iloc[0].to_dict() if not test_rule_df.empty else {}
        rows.append(
            {
                "criterion": criterion,
                "max_depth": max_depth,
                "min_samples_leaf": min_leaf,
                "min_samples_split": min_split,
                "train_auc": metric_map.get("train", {}).get("auc", np.nan),
                "test_auc": metric_map.get("test", {}).get("auc", np.nan),
                "train_accuracy": metric_map.get("train", {}).get("accuracy", np.nan),
                "test_accuracy": metric_map.get("test", {}).get("accuracy", np.nan),
                "test_recall": metric_map.get("test", {}).get("recall", np.nan),
                "rule_cnt_train": len(train_rule_df),
                "rule_cnt_test": len(test_rule_df),
                "best_rule_bad_rate_train": train_rule_df["bad_rate"].max() if not train_rule_df.empty else np.nan,
                "best_rule_lift_train": train_rule_df["lift"].max() if not train_rule_df.empty else np.nan,
                "best_rule_bad_rate": best_rule.get("bad_rate", np.nan),
                "best_rule_hit_rate": best_rule.get("hit_rate", np.nan),
                "best_rule_lift": best_rule.get("lift", np.nan),
                "best_rule_name": best_rule.get("rule_name", ""),
                "grid_score": score_grid_candidate(metrics_df, test_rule_df),
            }
        )

    result = pd.DataFrame(rows).sort_values(
        ["grid_score", "test_auc", "best_rule_lift"], ascending=[False, False, False]
    ).reset_index(drop=True)
    result.to_csv(tables_dir / "tree_grid_search_results.csv", index=False)
    result.head(config.grid_top_n).to_csv(tables_dir / "tree_grid_search_top_configs.csv", index=False)
    return result


def save_rule_markdown(rule_df: pd.DataFrame, tables_dir: Path) -> None:
    """保存规则表 Markdown，方便复制到报告。"""
    md_df = rule_df.copy()
    for col in ["bad_rate", "hit_rate", "recall_rate", "lift"]:
        md_df[col] = md_df[col].map(lambda x: f"{x:.4f}" if pd.notnull(x) else "")
    (tables_dir / "decision_tree_rules.md").write_text(md_df.to_markdown(index=False), encoding="utf-8")


def plot_decision_tree(model: tree.DecisionTreeClassifier, x_train: pd.DataFrame, figures_dir: Path) -> None:
    """保存决策树结构图。"""
    plt.figure(figsize=(22, 10))
    tree.plot_tree(
        model,
        feature_names=x_train.columns.tolist(),
        class_names=[str(c) for c in model.classes_],
        filled=True,
        rounded=True,
        fontsize=9,
    )
    plt.tight_layout()
    plt.savefig(figures_dir / "decision_tree_structure.png", dpi=160)
    plt.close()


def plot_rules(rule_df: pd.DataFrame, figures_dir: Path) -> None:
    """保存规则 lift 排名图。"""
    if rule_df.empty:
        return
    plot_df = rule_df.sort_values("lift", ascending=True).copy()
    labels = [f"leaf_{x}" for x in plot_df["leaf_id"]]
    plt.figure(figsize=(10, max(4, len(plot_df) * 0.45)))
    plt.barh(labels, plot_df["lift"])
    plt.title("Decision Tree Rule Lift")
    plt.xlabel("Lift")
    plt.ylabel("Rule Leaf")
    plt.tight_layout()
    plt.savefig(figures_dir / "rule_lift_ranking.png", dpi=160)
    plt.close()


def write_run_summary(
    config: Config,
    df: pd.DataFrame,
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    rule_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    tables_dir: Path,
) -> None:
    """保存本次运行摘要。"""
    best_rule = rule_df.iloc[0].to_dict() if not rule_df.empty else {}
    summary = {
        "config": asdict(config),
        "raw_sample_cnt": int(len(df)),
        "raw_feature_cnt": int(df.shape[1]),
        "train_sample_cnt": int(len(x_train)),
        "test_sample_cnt": int(len(x_test)),
        "rule_cnt": int(len(rule_df)),
        "best_rule_by_bad_rate": best_rule,
        "metrics": metrics_df.to_dict(orient="records"),
    }
    (tables_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def run(config: Config) -> None:
    input_path = Path(config.input_path)
    output_dir = Path(config.output_dir)
    tables_dir, figures_dir = ensure_dirs(output_dir)

    df = pd.read_csv(input_path)
    save_data_profile(df, tables_dir)
    plot_target_distribution(df, config.target_col, figures_dir)

    x, y, mapping_df = prepare_model_data(df, config)
    if not mapping_df.empty:
        mapping_df.to_csv(tables_dir / "categorical_encoding_mapping.csv", index=False)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=y,
    )

    model = train_decision_tree(x_train, y_train, config)
    metrics_df = evaluate_model(model, x_train, y_train, x_test, y_test, config.positive_label)
    metrics_df.to_csv(tables_dir / "model_metrics.csv", index=False)

    rule_df = extract_tree_rules(model, x_train, y_train, config.positive_label)
    rule_df.to_csv(tables_dir / "decision_tree_rules.csv", index=False)
    save_rule_markdown(rule_df, tables_dir)

    plot_decision_tree(model, x_train, figures_dir)
    plot_rules(rule_df, figures_dir)
    write_run_summary(config, df, x_train, x_test, rule_df, metrics_df, tables_dir)
    grid_df = run_tree_grid_search(x_train, y_train, x_test, y_test, config, tables_dir)

    print("Run finished.")
    print(f"Input: {input_path}")
    print(f"Output tables: {tables_dir}")
    print(f"Output figures: {figures_dir}")
    print("Top rules:")
    print(rule_df.head(10).to_string(index=False))
    print("Top tree grid-search configs:")
    print(grid_df.head(10).to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decision Tree Rule Miner")
    parser.add_argument("--input", default=DEFAULT_CONFIG.input_path, help="?? CSV ??")
    parser.add_argument("--output", default=DEFAULT_CONFIG.output_dir, help="????")
    parser.add_argument("--max-depth", type=int, default=DEFAULT_CONFIG.tree_max_depth, help="???????")
    parser.add_argument("--test-size", type=float, default=DEFAULT_CONFIG.test_size, help="?????")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> Config:
    return Config(
        input_path=args.input,
        output_dir=args.output,
        tree_max_depth=args.max_depth,
        test_size=args.test_size,
    )


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
