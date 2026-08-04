# -*- coding: utf-8 -*-
"""
规则集性能测试项目主程序

功能：
1. 读取 input/ 下的 Excel 样本数据；
2. 输出基础探索结果；
3. 使用决策树自动挖掘策略规则；
4. 基于预置规则计算规则集覆盖率、纯命中率、综合命中率、坏账率与 lift；
5. 将所有表格、图片统一输出到 output/ 目录。

运行方式：
    python run.py

如需更换输入文件或输出目录，请修改 Config 配置区。
"""

from __future__ import annotations

import argparse
import itertools
import platform
import sys
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn.tree import _tree

warnings.filterwarnings("ignore")


# =============================================================================
# 1. 配置层：后续复用时优先改这里
# =============================================================================

@dataclass
class Config:
    """项目配置。"""

    # 路径配置
    project_dir: Path = Path(__file__).resolve().parents[1]
    input_dir: Path = project_dir / "input"
    output_dir: Path = project_dir / "output"
    table_dir: Path = output_dir / "tables"
    figure_dir: Path = output_dir / "figures"

    # 输入数据配置
    input_file: str = "100daysrisk_strategy_ruleset.xlsx"
    sheet_name: int | str = 0

    # 核心字段配置
    id_col: str = "ID"
    target_col: str = "TARGET"

    # 决策树规则挖掘配置
    test_size: float = 0.2
    split_random_state: int = 42
    tree_random_state: int = 2024
    min_samples_leaf: float = 0.01
    min_samples_split: float = 0.01

    # 原 notebook 的规则挖掘方式：
    # - (2, 1)：两两变量组合，树深 1；
    # - (None, 2)：全部变量入模，树深 2；
    # - (None, 3)：全部变量入模，树深 3。
    # 其中 None 表示使用全部候选变量。
    rule_mining_jobs: Sequence[Tuple[Optional[int], int]] = field(
        default_factory=lambda: [(2, 1), (None, 2), (None, 3)]
    )

    # 自动挖掘规则筛选条件
    min_lift: float = 1.0
    max_hit_rate_pct: float = 5.0

    # 规则集评估配置：来自原 notebook 中手工落地的规则
    # 如需替换策略规则，改 build_rule_flags() 函数即可。
    delete_rules: Sequence[str] = field(
        default_factory=lambda: ["rule7", "rule4", "rule1", "rule5"]
    )


CFG = Config()


# =============================================================================
# 2. 通用工具函数
# =============================================================================

def ensure_dirs(cfg: Config) -> None:
    """创建输出目录。"""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.table_dir.mkdir(parents=True, exist_ok=True)
    cfg.figure_dir.mkdir(parents=True, exist_ok=True)


def print_runtime_info() -> None:
    """打印运行环境版本，方便排查依赖问题。"""
    import matplotlib as mpl
    import sklearn as sk

    print("=" * 80)
    print("Runtime Info")
    print("=" * 80)
    print(f"python     : {sys.version.split()[0]}")
    print(f"platform   : {platform.platform()}")
    print(f"pandas     : {pd.__version__}")
    print(f"numpy      : {np.__version__}")
    print(f"sklearn    : {sk.__version__}")
    print(f"matplotlib : {mpl.__version__}")
    print("=" * 80)


def safe_divide(numerator: float, denominator: float) -> float:
    """安全除法，避免分母为 0 报错。"""
    if denominator == 0 or pd.isna(denominator):
        return np.nan
    return numerator / denominator


def simple_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成字段级基础统计：
    - 唯一值数量
    - 空值率
    - 众数占比
    - 字段类型
    """
    stats = []
    for col in df.columns:
        value_counts = df[col].value_counts(normalize=True, dropna=False)
        mode_pct = value_counts.iloc[0] * 100 if len(value_counts) > 0 else np.nan
        stats.append(
            (
                col,
                df[col].nunique(dropna=True),
                df[col].isna().sum() * 100 / len(df),
                mode_pct,
                str(df[col].dtype),
            )
        )

    stats_df = pd.DataFrame(
        stats,
        columns=[
            "feature",
            "unique_values",
            "percentage_of_null",
            "percentage_of_mode",
            "dtype",
        ],
    )
    return stats_df.sort_values("unique_values", ascending=False).reset_index(drop=True)


def get_feature_columns(df: pd.DataFrame, id_col: str, target_col: str) -> List[str]:
    """获取候选特征字段，默认排除 ID 和目标变量。"""
    exclude_cols = {id_col, target_col}
    return [c for c in df.columns if c not in exclude_cols]


def prepare_feature_matrix(df: pd.DataFrame, feature_cols: Sequence[str]) -> pd.DataFrame:
    """
    将特征整理为决策树可用的矩阵。

    原始 notebook 的样例字段均为数值型。这里额外兼容 object/category 字段：
    - 数值型：用中位数填充缺失；
    - 字符型：用字符串 MISSING 填充后做 factorize 编码。
    """
    x = df.loc[:, feature_cols].copy()
    for col in x.columns:
        if pd.api.types.is_numeric_dtype(x[col]):
            median_value = x[col].median()
            if pd.isna(median_value):
                median_value = 0
            x[col] = x[col].fillna(median_value)
        else:
            x[col] = x[col].astype("object").where(x[col].notna(), "MISSING")
            x[col] = pd.factorize(x[col])[0]
    return x


def save_excel_report(tables: Dict[str, pd.DataFrame], output_path: Path) -> None:
    """将多个 DataFrame 保存到同一个 Excel 文件中。"""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, table in tables.items():
            safe_sheet_name = sheet_name[:31]
            table.to_excel(writer, sheet_name=safe_sheet_name, index=False)


# =============================================================================
# 3. 数据读取与探索
# =============================================================================

def load_data(cfg: Config) -> pd.DataFrame:
    """读取 input 下的 Excel 数据。"""
    input_path = cfg.input_dir / cfg.input_file
    if not input_path.exists():
        raise FileNotFoundError(
            f"未找到输入文件：{input_path}\n"
            f"请将 Excel 文件放到 input/ 目录，并确认 Config.input_file 配置正确。"
        )

    df = pd.read_excel(input_path, sheet_name=cfg.sheet_name)
    if cfg.target_col not in df.columns:
        raise ValueError(f"目标变量 {cfg.target_col!r} 不存在，请检查输入数据。")
    return df


def run_data_exploration(df: pd.DataFrame, cfg: Config) -> Dict[str, pd.DataFrame]:
    """输出基础数据探索结果。"""
    y_col = cfg.target_col
    feature_cols = get_feature_columns(df, cfg.id_col, cfg.target_col)
    numeric_features = df[feature_cols].select_dtypes(include=["number"]).columns.tolist()
    object_features = df[feature_cols].select_dtypes(exclude=["number"]).columns.tolist()

    describe_df = df.describe(include="all").reset_index().rename(columns={"index": "metric"})
    simple_stats_df = simple_statistics(df)
    target_distribution_df = (
        df[y_col]
        .value_counts(dropna=False)
        .rename_axis(y_col)
        .reset_index(name="sample_cnt")
    )
    target_distribution_df["sample_pct"] = target_distribution_df["sample_cnt"] / len(df)

    variable_type_df = pd.DataFrame(
        [
            ("numeric_features", len(numeric_features), ", ".join(numeric_features)),
            ("object_features", len(object_features), ", ".join(object_features)),
        ],
        columns=["type", "feature_cnt", "features"],
    )

    # 目标变量分布图
    plt.figure(figsize=(10, 6))
    df[y_col].value_counts(dropna=False).plot(kind="bar")
    plt.title(f"Target Distribution: {y_col}")
    plt.xlabel(y_col)
    plt.ylabel("sample_cnt")
    plt.tight_layout()
    plt.savefig(cfg.figure_dir / "target_distribution.png", dpi=150)
    plt.close()

    return {
        "describe": describe_df,
        "simple_statistics": simple_stats_df,
        "target_distribution": target_distribution_df,
        "variable_types": variable_type_df,
    }


# =============================================================================
# 4. 决策树自动挖掘规则
# =============================================================================

def predict_leaf_values(
    model: tree.DecisionTreeClassifier,
    total_sample: int,
    total_bad: float,
    total_badrate: float,
) -> List[List[float]]:
    """输出每个叶子节点的坏账率、命中率、召回率、lift。"""
    value_list: List[List[float]] = []
    tree_ = model.tree_

    def recurse(node: int) -> None:
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            recurse(tree_.children_left[node])
            recurse(tree_.children_right[node])
        else:
            good = tree_.value[node][0][0]
            bad = tree_.value[node][0][1]
            samples = good + bad
            bad_rate = round(safe_divide(bad * 100, bad + good), 4)
            hit_rate = round(safe_divide(samples * 100, total_sample), 4)
            recall_rate = round(safe_divide(bad * 100, total_bad), 4)
            lift = round(safe_divide(bad_rate * 0.01, total_badrate), 4)
            value_list.append([bad_rate, hit_rate, recall_rate, lift])

    recurse(0)
    return value_list


def extract_tree_rules(
    model: tree.DecisionTreeClassifier,
    feature_names: Sequence[str],
    total_sample: int,
    total_bad: float,
    total_badrate: float,
) -> List[List[object]]:
    """抽取并解析决策树叶子节点对应的规则路径。"""
    left = model.tree_.children_left
    right = model.tree_.children_right
    threshold = model.tree_.threshold
    features = [feature_names[i] if i >= 0 else "undefined" for i in model.tree_.feature]
    leaf_nodes = np.argwhere(left == -1)[:, 0]
    value_list = predict_leaf_values(model, total_sample, total_bad, total_badrate)
    rule_list: List[List[object]] = []

    def decision_flow_extract(child: int, d_flow: Optional[List[object]] = None) -> List[object]:
        if d_flow is None:
            d_flow = [child]
        if child in left:
            parent = np.where(left == child)[0].item()
            split = "le"
        else:
            parent = np.where(right == child)[0].item()
            split = "rg"
        d_flow.append((parent, split, threshold[parent], features[parent]))
        if parent == 0:
            d_flow.reverse()
            return d_flow
        return decision_flow_extract(parent, d_flow)

    for j, child in enumerate(leaf_nodes):
        clauses = []
        for node in decision_flow_extract(child):
            if not isinstance(node, tuple):
                continue
            sign = "<=" if node[1] == "le" else ">"
            clauses.append(f"{node[3]}{sign}{node[2]}")

        rule_name = " and ".join(clauses)
        row = value_list[j] + [rule_name]
        rule_list.append(row)

    return rule_list


def list_all_combinations(items: Sequence[str], r: int) -> List[Tuple[str, ...]]:
    """列出所有大小为 r 的变量组合。"""
    return list(itertools.combinations(items, r))


def mine_rules(df: pd.DataFrame, cfg: Config) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """按照配置自动挖掘规则，并输出全量规则和筛选后规则。"""
    y_col = cfg.target_col
    feature_cols = get_feature_columns(df, cfg.id_col, cfg.target_col)
    x_all = prepare_feature_matrix(df, feature_cols)
    y_all = df[y_col]

    rule_df_list: List[pd.DataFrame] = []

    for combination_size, max_depth in cfg.rule_mining_jobs:
        if combination_size is None:
            combinations_list = [tuple(feature_cols)]
            combination_desc = "all_features"
        else:
            combinations_list = list_all_combinations(feature_cols, combination_size)
            combination_desc = f"{combination_size}_features"

        for combo in combinations_list:
            x = x_all.loc[:, list(combo)]
            y = y_all

            x_train, _, y_train, _ = train_test_split(
                x,
                y,
                test_size=cfg.test_size,
                random_state=cfg.split_random_state,
            )

            model = tree.DecisionTreeClassifier(
                criterion="gini",
                splitter="best",
                random_state=cfg.tree_random_state,
                max_depth=max_depth,
                min_samples_leaf=cfg.min_samples_leaf,
                min_samples_split=cfg.min_samples_split,
            )
            model.fit(x_train, y_train)

            total_bad = y_train.sum()
            total_badrate = y_train.mean()
            total_sample = y_train.count()

            rule_rows = extract_tree_rules(
                model=model,
                feature_names=x.columns.tolist(),
                total_sample=total_sample,
                total_bad=total_bad,
                total_badrate=total_badrate,
            )
            rule_df = pd.DataFrame(
                rule_rows,
                columns=["bad_rate", "hit_rate", "recall_rate", "lift", "rule_name"],
            )
            rule_df.insert(0, "max_depth", max_depth)
            rule_df.insert(0, "combination_type", combination_desc)
            rule_df.insert(0, "feature_combo", ",".join(combo))
            rule_df_list.append(rule_df)

    if not rule_df_list:
        empty = pd.DataFrame(
            columns=[
                "feature_combo",
                "combination_type",
                "max_depth",
                "bad_rate",
                "hit_rate",
                "recall_rate",
                "lift",
                "rule_name",
            ]
        )
        return empty, empty

    all_rules_df = pd.concat(rule_df_list, ignore_index=True)
    dedup_rules_df = all_rules_df.drop_duplicates(subset=["rule_name"]).reset_index(drop=True)
    filtered_rules_df = (
        dedup_rules_df[
            (dedup_rules_df["lift"] > cfg.min_lift)
            & (dedup_rules_df["hit_rate"] <= cfg.max_hit_rate_pct)
        ]
        .sort_values("bad_rate", ascending=False)
        .reset_index(drop=True)
    )
    return dedup_rules_df, filtered_rules_df


# =============================================================================
# 5. 规则集性能测试
# =============================================================================

def build_rule_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    构造原 notebook 中用于规则集性能测试的 8 条规则。

    注意：这里是示例规则，如果更换业务规则，只需要改这个函数。
    """
    required_cols = {"V01", "V02", "V05", "V06", "V10"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"规则集评估缺少必要字段：{sorted(missing_cols)}")

    rule_df = pd.DataFrame(index=df.index)
    rule_df["rule0"] = ((df["V10"] <= 491.5) & (df["V01"] > 0.5)).astype(int)
    rule_df["rule1"] = (df["V10"] <= 491.5).astype(int)
    rule_df["rule2"] = ((df["V10"] <= 491.5) & (df["V01"] <= 0.5)).astype(int)
    rule_df["rule3"] = (df["V05"] > 183.0).astype(int)
    rule_df["rule4"] = ((df["V10"] > 491.5) & (df["V05"] > 183.0)).astype(int)
    rule_df["rule5"] = (df["V02"] > 5.0).astype(int)
    rule_df["rule6"] = ((df["V10"] > 491.5) & (df["V05"] <= 183.0) & (df["V02"] > 5.0)).astype(int)
    rule_df["rule7"] = (df["V06"] > 0.5).astype(int)
    return rule_df


def mutual_cover_rate(rule_flags: pd.DataFrame, rule_a: str, rule_b: str) -> Tuple[float, float]:
    """计算两条规则之间的相互覆盖率。"""
    inner_hit = rule_flags[(rule_flags[rule_a] == 1) & (rule_flags[rule_b] == 1)].shape[0]
    a_hit = rule_flags[rule_flags[rule_a] == 1].shape[0]
    b_hit = rule_flags[rule_flags[rule_b] == 1].shape[0]
    return round(safe_divide(inner_hit, a_hit), 4), round(safe_divide(inner_hit, b_hit), 4)


def calculate_mutual_cover(rule_flags: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """计算规则两两组合的相互覆盖率，并找出完全覆盖关系。"""
    mutual_cover_info = []
    rule_cols = rule_flags.columns.tolist()

    for rule_a, rule_b in list_all_combinations(rule_cols, 2):
        a_cover, b_cover = mutual_cover_rate(rule_flags, rule_a, rule_b)
        group_name = f"{rule_a},{rule_b}"
        mutual_cover_info.append((group_name, rule_a, a_cover))
        mutual_cover_info.append((group_name, rule_b, b_cover))

    mutual_cover_df = pd.DataFrame(
        mutual_cover_info,
        columns=["rule_group", "rule", "mutual_cover_rate"],
    )

    mutual_cover_1 = mutual_cover_df[mutual_cover_df["mutual_cover_rate"] == 1].copy()
    if mutual_cover_1.empty:
        full_cover_df = pd.DataFrame(columns=["rule", "covered_by_or_covering_rules"])
    else:
        mutual_cover_1["rule_group_list"] = mutual_cover_1["rule_group"].str.split(",")
        mutual_cover_1_ex = mutual_cover_1.explode("rule_group_list")
        full_cover_df = (
            mutual_cover_1_ex.groupby("rule")["rule_group_list"]
            .apply(lambda x: ", ".join(sorted(set(x))))
            .reset_index(name="covered_by_or_covering_rules")
            .sort_values("covered_by_or_covering_rules", ascending=False)
        )

    return mutual_cover_df, full_cover_df


def calculate_pure_hit(rule_flags: pd.DataFrame) -> pd.DataFrame:
    """计算单条规则命中率和纯命中率。"""
    rule_cols = rule_flags.columns.tolist()
    tmp = rule_flags.copy()
    tmp["hit_sum"] = tmp[rule_cols].sum(axis=1)

    pure_hit_info = []
    total_sample = len(tmp)
    for rule_col in rule_cols:
        hit_sum = tmp[tmp[rule_col] == 1].shape[0]
        pure_hit_sum = tmp[(tmp[rule_col] == 1) & (tmp["hit_sum"] == 1)].shape[0]
        pure_hit_info.append(
            (
                rule_col,
                hit_sum,
                round(safe_divide(hit_sum, total_sample), 4),
                pure_hit_sum,
                round(safe_divide(pure_hit_sum, total_sample), 4),
            )
        )

    return pd.DataFrame(
        pure_hit_info,
        columns=["rule", "hit_cnt", "hit_rate", "pure_hit_cnt", "pure_hit_rate"],
    )


def evaluate_ruleset(df: pd.DataFrame, cfg: Config) -> Dict[str, pd.DataFrame]:
    """执行规则集性能评估。"""
    y_col = cfg.target_col
    all_rule_flags = build_rule_flags(df)
    selected_rule_flags = all_rule_flags.drop(columns=list(cfg.delete_rules), errors="ignore")

    mutual_cover_df, full_cover_df = calculate_mutual_cover(all_rule_flags)
    pure_hit_df = calculate_pure_hit(selected_rule_flags)

    rule_cols = selected_rule_flags.columns.tolist()
    rule_eval_df = selected_rule_flags.copy()
    rule_eval_df[y_col] = df[y_col].values
    rule_eval_df["hit_sum"] = rule_eval_df[rule_cols].sum(axis=1)
    rule_eval_df["total_hit"] = (rule_eval_df["hit_sum"] >= 1).astype(int)

    hit_sum_distribution_df = (
        rule_eval_df["hit_sum"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("hit_sum")
        .reset_index(name="sample_cnt")
    )
    hit_sum_distribution_df["sample_pct"] = hit_sum_distribution_df["sample_cnt"] / len(rule_eval_df)

    total_hit_distribution_df = (
        rule_eval_df["total_hit"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("total_hit")
        .reset_index(name="sample_cnt")
    )
    total_hit_distribution_df["sample_pct"] = total_hit_distribution_df["sample_cnt"] / len(rule_eval_df)

    hit_sample_cnt = rule_eval_df[rule_eval_df["total_hit"] == 1].shape[0]
    hit_bad_cnt = rule_eval_df[(rule_eval_df["total_hit"] == 1) & (rule_eval_df[y_col] == 1)].shape[0]
    ruleset_bad_rate = safe_divide(hit_bad_cnt, hit_sample_cnt)
    overall_bad_rate = df[y_col].mean()
    ruleset_lift = safe_divide(ruleset_bad_rate, overall_bad_rate)

    ruleset_summary_df = pd.DataFrame(
        [
            ("total_sample", len(df)),
            ("overall_bad_cnt", int(df[y_col].sum())),
            ("overall_bad_rate", overall_bad_rate),
            ("selected_rules", ", ".join(rule_cols)),
            ("ruleset_hit_cnt", hit_sample_cnt),
            ("ruleset_hit_rate", safe_divide(hit_sample_cnt, len(df))),
            ("ruleset_bad_cnt", hit_bad_cnt),
            ("ruleset_bad_rate", ruleset_bad_rate),
            ("ruleset_lift", ruleset_lift),
        ],
        columns=["metric", "value"],
    )

    return {
        "all_rule_flags": all_rule_flags.reset_index(drop=True),
        "selected_rule_flags": selected_rule_flags.reset_index(drop=True),
        "mutual_cover": mutual_cover_df,
        "full_cover_rules": full_cover_df,
        "pure_hit": pure_hit_df,
        "hit_sum_distribution": hit_sum_distribution_df,
        "total_hit_distribution": total_hit_distribution_df,
        "ruleset_summary": ruleset_summary_df,
    }


# =============================================================================
# 6. 主流程
# =============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ruleset performance evaluation")
    parser.add_argument("--input", default=str(CFG.input_dir / CFG.input_file), help="?? Excel ??")
    parser.add_argument("--output", default=str(CFG.output_dir), help="????")
    parser.add_argument("--sheet-name", default=str(CFG.sheet_name), help="Excel sheet ?????")
    parser.add_argument("--target", default=CFG.target_col, help="????")
    parser.add_argument("--id-col", default=CFG.id_col, help="?? ID ??")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> Config:
    cfg = Config()
    cfg.input_dir = Path(args.input).resolve().parent
    cfg.input_file = Path(args.input).name
    cfg.output_dir = Path(args.output)
    cfg.table_dir = cfg.output_dir / "tables"
    cfg.figure_dir = cfg.output_dir / "figures"
    cfg.sheet_name = int(args.sheet_name) if str(args.sheet_name).isdigit() else args.sheet_name
    cfg.target_col = args.target
    cfg.id_col = args.id_col
    return cfg


def run(cfg: Config) -> None:
    ensure_dirs(cfg)
    print_runtime_info()

    print("??????...")
    df = load_data(cfg)
    print(f"???????shape={df.shape}")

    print("????????...")
    exploration_tables = run_data_exploration(df, cfg)

    print("???????????...")
    all_rules_df, filtered_rules_df = mine_rules(df, cfg)
    print(f"???????: {all_rules_df.shape[0]}???????: {filtered_rules_df.shape[0]}")

    print("?????????...")
    ruleset_tables = evaluate_ruleset(df, cfg)

    print("??????...")
    output_tables = {
        **exploration_tables,
        "mined_rules_all": all_rules_df,
        "mined_rules_filtered": filtered_rules_df,
        **{k: v for k, v in ruleset_tables.items() if k not in {"all_rule_flags", "selected_rule_flags"}},
    }

    for name, table in output_tables.items():
        table.to_csv(cfg.table_dir / f"{name}.csv", index=False, encoding="utf-8-sig")

    ruleset_tables["all_rule_flags"].to_csv(
        cfg.table_dir / "all_rule_flags.csv", index=False, encoding="utf-8-sig"
    )
    ruleset_tables["selected_rule_flags"].to_csv(
        cfg.table_dir / "selected_rule_flags.csv", index=False, encoding="utf-8-sig"
    )

    print("=" * 80)
    print("????")
    print(f"Excel ????: {cfg.output_dir / 'summary_report.xlsx'}")
    print(f"CSV ????: {cfg.table_dir}")
    print(f"????: {cfg.figure_dir}")
    print("=" * 80)


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
