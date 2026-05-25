# -*- coding: utf-8 -*-
"""
Risk Strategy D-Class Tuning Project

用途：将原 notebook 的策略新增调优流程整理为可直接运行的 Python 项目。
输入统一放在 input/，输出统一写入 output/。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
except Exception as exc:  # pragma: no cover
    raise ImportError("请先安装 matplotlib 和 seaborn：pip install matplotlib seaborn") from exc

try:
    import scorecardpy as sc  # type: ignore
except Exception:  # scorecardpy 是可选依赖；没有安装时使用内置分箱计算
    sc = None


@dataclass
class Config:
    """项目配置层：后续更换数据、字段、规则时，优先修改这里。"""

    input_file: str = "input/data_v4.xlsx"
    output_dir: str = "output"

    # 核心字段
    target_col: str = "is_dlq_30d"  # 30 天逾期标签，1=坏，0=好
    sample_id_col: str = "sample_id"
    sample_month_col: str = "sample_month"

    # 新接入变量
    new_features: Tuple[str, ...] = ("risk_score", "ovd_order_cnt_6m_grade")

    # 交叉分析维度：用于输出二维 lift / 样本占比热力图
    cross_index: str = "risk_score"
    cross_columns: str = "ovd_order_cnt_6m_grade"

    # 规则配置：元组格式为 (规则名称, pandas.eval 可识别的表达式)
    existing_rules: Tuple[Tuple[str, str], ...] = (
        ("positive_biz_cnt_1y_grade", "positive_biz_cnt_1y_grade < 2"),
        ("adr_stability_grade", "adr_stability_grade < 2"),
    )

    single_var_rules: Tuple[Tuple[str, str], ...] = (
        ("positive_biz_cnt_1y_grade", "positive_biz_cnt_1y_grade < 2"),
        ("adr_stability_grade", "adr_stability_grade < 2"),
        ("risk_score", "risk_score > 5"),
    )

    # 保留原 notebook 的策略组合：热力图看 risk_score x ovd_order_cnt_6m_grade，实际策略规则用 risk_score x positive_biz_cnt_1y_grade
    cross_rules: Tuple[Tuple[str, str], ...] = (
        ("positive_biz_cnt_1y_grade", "positive_biz_cnt_1y_grade < 2"),
        ("adr_stability_grade", "adr_stability_grade < 2"),
        ("risk_positive_0", "(risk_score >= 7) & (positive_biz_cnt_1y_grade >= 2)"),
        ("risk_positive_1", "(risk_score == 8) & (positive_biz_cnt_1y_grade == 1)"),
        ("risk_positive_2", "(risk_score == 6) & (positive_biz_cnt_1y_grade == 5)"),
    )

    # 内置分箱兜底参数：当没有安装 scorecardpy 时生效
    fallback_max_bins: int = 6
    low_cardinality_threshold: int = 20
    grid_candidate_features: Tuple[str, ...] = (
        "risk_score",
        "ovd_order_cnt_6m_grade",
        "positive_biz_cnt_1y_grade",
        "adr_stability_grade",
    )
    grid_top_n: int = 30
    grid_min_hit_rate: float = 0.01
    grid_max_hit_rate: float = 0.40
    grid_min_lift: float = 1.10
    grid_min_bad_capture: float = 0.01
    grid_pair_top_k_single_rules: int = 12


CONFIG = Config()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_df(df: pd.DataFrame, path: Path) -> None:
    """统一保存表格，避免中文乱码。"""
    df.to_csv(path, index=False, encoding="utf-8-sig")


def load_data(config: Config) -> pd.DataFrame:
    input_path = Path(config.input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"未找到输入文件：{input_path.resolve()}")

    df = pd.read_excel(input_path)
    required_cols = {
        config.target_col,
        config.sample_id_col,
        config.sample_month_col,
        *config.new_features,
        "positive_biz_cnt_1y_grade",
        "adr_stability_grade",
    }
    missing_cols = sorted(required_cols.difference(df.columns))
    if missing_cols:
        raise ValueError(f"输入数据缺少必要字段：{missing_cols}")
    return df


def prepare_passed_sample(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """筛选有表现标签的通过样本。"""
    data = df.loc[df[config.target_col].notna()].reset_index(drop=True).copy()
    data[config.target_col] = data[config.target_col].astype(int)
    return data


def get_existing_features(df: pd.DataFrame, config: Config) -> List[str]:
    exclude = {
        config.sample_id_col,
        config.sample_month_col,
        config.target_col,
        *config.new_features,
    }
    return [c for c in df.columns if c not in exclude]


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0 or pd.isna(denominator):
        return np.nan
    return numerator / denominator


def _make_bin_series(s: pd.Series, max_bins: int, low_cardinality_threshold: int) -> pd.Series:
    """内置分箱：低基数字段按取值分组，高基数字段按分位数分箱。"""
    s2 = s.copy()
    non_null = s2.dropna()
    if non_null.empty:
        return pd.Series(["MISSING"] * len(s2), index=s2.index)

    unique_cnt = non_null.nunique()
    if unique_cnt <= low_cardinality_threshold:
        binned = s2.astype("object").where(s2.notna(), "MISSING")
        return binned.astype(str)

    try:
        binned = pd.qcut(non_null, q=min(max_bins, unique_cnt), duplicates="drop")
        out = pd.Series("MISSING", index=s2.index, dtype="object")
        out.loc[non_null.index] = binned.astype(str)
        return out
    except Exception:
        binned = pd.cut(non_null, bins=min(max_bins, unique_cnt), duplicates="drop")
        out = pd.Series("MISSING", index=s2.index, dtype="object")
        out.loc[non_null.index] = binned.astype(str)
        return out


def fallback_bins_calc(
    df: pd.DataFrame,
    features: Sequence[str],
    target_col: str,
    overall_bad_rate: float,
    max_bins: int,
    low_cardinality_threshold: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """不依赖 scorecardpy 的 IV / WOE / Lift 计算。"""
    metric_rows: List[Dict[str, float]] = []
    detail_rows: List[Dict[str, object]] = []

    total_bad = float(df[target_col].sum())
    total_good = float(df.shape[0] - total_bad)
    eps = 1e-8

    for feature in features:
        if feature == target_col:
            continue
        if feature not in df.columns:
            continue

        tmp = pd.DataFrame(
            {
                "bin": _make_bin_series(df[feature], max_bins, low_cardinality_threshold),
                target_col: df[target_col].astype(int),
            }
        )
        grouped = tmp.groupby("bin", dropna=False)[target_col].agg(["count", "sum"]).reset_index()
        grouped = grouped.rename(columns={"count": "total", "sum": "bad"})
        grouped["good"] = grouped["total"] - grouped["bad"]
        grouped["badprob"] = grouped["bad"] / grouped["total"]
        grouped["total_pct"] = grouped["total"] / df.shape[0]
        grouped["bad_dist"] = grouped["bad"] / total_bad if total_bad > 0 else np.nan
        grouped["good_dist"] = grouped["good"] / total_good if total_good > 0 else np.nan
        grouped["woe"] = np.log((grouped["bad_dist"] + eps) / (grouped["good_dist"] + eps))
        grouped["bin_iv"] = (grouped["bad_dist"] - grouped["good_dist"]) * grouped["woe"]
        grouped["lift"] = grouped["badprob"] / overall_bad_rate if overall_bad_rate > 0 else np.nan
        total_iv = grouped["bin_iv"].sum()
        max_lift = grouped["lift"].max()

        metric_rows.append({"name": feature, "iv": total_iv, "max_lift": max_lift, "method": "fallback"})
        for _, r in grouped.iterrows():
            detail_rows.append(
                {
                    "variable": feature,
                    "bin": r["bin"],
                    "total": int(r["total"]),
                    "bad": int(r["bad"]),
                    "good": int(r["good"]),
                    "badprob": r["badprob"],
                    "total_pct": r["total_pct"],
                    "woe": r["woe"],
                    "bin_iv": r["bin_iv"],
                    "total_iv": total_iv,
                    "lift": r["lift"],
                    "method": "fallback",
                }
            )

    metrics = pd.DataFrame(metric_rows).sort_values(["iv", "max_lift"], ascending=[False, False])
    details = pd.DataFrame(detail_rows)
    return metrics, details


def scorecardpy_bins_calc(
    df: pd.DataFrame,
    features: Sequence[str],
    target_col: str,
    overall_bad_rate: float,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """优先使用 scorecardpy 复现 notebook 的 tree 分箱。"""
    if sc is None:
        raise ImportError("scorecardpy 未安装")
    use_cols = [target_col] + [c for c in features if c in df.columns and c != target_col]
    bins_info = sc.woebin(df[use_cols], y=target_col, breaks_list={}, method="tree", stop_limit=0)

    metric_rows: List[Dict[str, object]] = []
    detail_parts: List[pd.DataFrame] = []
    for name, bin_df in bins_info.items():
        if name == target_col:
            continue
        v = bin_df.copy()
        if "badprob" in v.columns:
            v["lift"] = v["badprob"] / overall_bad_rate if overall_bad_rate > 0 else np.nan
        else:
            v["lift"] = np.nan
        iv = float(v["total_iv"].max()) if "total_iv" in v.columns else np.nan
        max_lift = float(v["lift"].max()) if "lift" in v.columns else np.nan
        metric_rows.append({"name": name, "iv": iv, "max_lift": max_lift, "method": "scorecardpy"})
        v.insert(0, "variable", name)
        v["method"] = "scorecardpy"
        detail_parts.append(v)

    metrics = pd.DataFrame(metric_rows).sort_values(["iv", "max_lift"], ascending=[False, False])
    details = pd.concat(detail_parts, ignore_index=True) if detail_parts else pd.DataFrame()
    return metrics, details


def bins_calc(
    df: pd.DataFrame,
    features: Sequence[str],
    config: Config,
    overall_bad_rate: float,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """计算变量 IV、Lift 和分箱明细。"""
    try:
        return scorecardpy_bins_calc(df, features, config.target_col, overall_bad_rate)
    except Exception as exc:
        print(f"[INFO] scorecardpy 不可用或分箱失败，使用内置分箱计算。原因：{exc}")
        return fallback_bins_calc(
            df=df,
            features=features,
            target_col=config.target_col,
            overall_bad_rate=overall_bad_rate,
            max_bins=config.fallback_max_bins,
            low_cardinality_threshold=config.low_cardinality_threshold,
        )


def ruleset_calc(df: pd.DataFrame, rules: Sequence[Tuple[str, str]]) -> Tuple[float, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """计算规则集综合命中率、命中数量分布、单一/自然命中率。"""
    data = df.copy()

    for rule_name, _ in rules:
        data[f"{rule_name}_hit"] = 0

    for rule_name, expr in rules:
        try:
            cond = data.eval(expr)
        except Exception as exc:
            raise ValueError(f"规则表达式执行失败：{rule_name} -> {expr}; {exc}") from exc
        data[f"{rule_name}_hit"] = np.where(cond, 1, 0)

    hit_cols = [c for c in data.columns if c.endswith("_hit")]
    data["hit_any"] = data[hit_cols].any(axis=1)
    data["hit_sum"] = data[hit_cols].sum(axis=1)
    overall_hit_rate = float(data["hit_any"].mean())

    hit_count_dist = (
        data["hit_sum"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("hit_sum")
        .reset_index(name="sample_cnt")
    )
    hit_count_dist["sample_pct"] = hit_count_dist["sample_cnt"] / data.shape[0]

    pure_hit_info = []
    for col in hit_cols:
        sample_cnt = int((data[col] == 1).sum())
        pure_hit_sum = int(((data[col] == 1) & (data["hit_sum"] == 1)).sum())
        hit_rate = sample_cnt / data.shape[0]
        pure_hit_rate = pure_hit_sum / data.shape[0]
        pure_hit_pct = _safe_div(pure_hit_rate, hit_rate)
        pure_hit_info.append(
            {
                "rule": col.replace("_hit", ""),
                "hit_sample_cnt": sample_cnt,
                "hit_rate": hit_rate,
                "pure_hit_sample_cnt": pure_hit_sum,
                "pure_hit_rate": pure_hit_rate,
                "pure_hit_pct_in_hit": pure_hit_pct,
            }
        )
    pure_hit_df = pd.DataFrame(pure_hit_info).sort_values(
        ["pure_hit_rate", "pure_hit_pct_in_hit"], ascending=[False, False]
    )

    summary = pd.DataFrame(
        [
            {
                "sample_cnt": data.shape[0],
                "rule_cnt": len(rules),
                "overall_hit_rate": overall_hit_rate,
                "overall_hit_sample_cnt": int(data["hit_any"].sum()),
            }
        ]
    )
    return overall_hit_rate, data, hit_count_dist, pure_hit_df.join(summary, how="cross")


def calc_strategy_effect(
    raw_df: pd.DataFrame,
    passed_df: pd.DataFrame,
    ruled_df: pd.DataFrame,
    target_col: str,
    scenario: str,
) -> pd.DataFrame:
    """计算策略调整前后：坏账率、通过率、下降幅度。"""
    before_sample = passed_df
    after_sample = ruled_df.loc[ruled_df["hit_sum"] == 0].copy()

    before_bad_rate = float(before_sample[target_col].mean())
    after_bad_rate = float(after_sample[target_col].mean()) if after_sample.shape[0] > 0 else np.nan
    before_pass_rate = before_sample.shape[0] / raw_df.shape[0]
    after_pass_rate = after_sample.shape[0] / raw_df.shape[0]

    return pd.DataFrame(
        [
            {
                "scenario": scenario,
                "raw_sample_cnt": raw_df.shape[0],
                "before_passed_sample_cnt": before_sample.shape[0],
                "after_passed_sample_cnt": after_sample.shape[0],
                "rejected_sample_cnt": int(ruled_df["hit_any"].sum()),
                "before_bad_rate": before_bad_rate,
                "after_bad_rate": after_bad_rate,
                "bad_rate_drop_abs": before_bad_rate - after_bad_rate,
                "bad_rate_drop_pct": _safe_div(before_bad_rate - after_bad_rate, before_bad_rate),
                "before_pass_rate": before_pass_rate,
                "after_pass_rate": after_pass_rate,
                "pass_rate_drop_abs": before_pass_rate - after_pass_rate,
                "pass_rate_drop_pct": _safe_div(before_pass_rate - after_pass_rate, before_pass_rate),
            }
        ]
    )


def build_grid_threshold_candidates(series: pd.Series) -> List[float]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return []
    unique_values = sorted(float(v) for v in numeric.unique().tolist())
    if len(unique_values) <= 12:
        return unique_values
    return sorted(
        {
            float(v)
            for v in numeric.quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]).tolist()
            if not pd.isna(v)
        }
    )


def evaluate_grid_mask(
    df: pd.DataFrame,
    raw_df: pd.DataFrame,
    mask: pd.Series,
    target_col: str,
    scenario: str,
    rule_name: str,
    feature_bundle: str,
    left_feature: str,
    left_operator: str,
    left_threshold: float,
    right_feature: str | None = None,
    right_operator: str | None = None,
    right_threshold: float | None = None,
) -> Dict[str, object]:
    hit_df = df.loc[mask].copy()
    total_bad = float(df[target_col].sum())
    hit_cnt = int(mask.sum())
    bad_cnt = int(hit_df[target_col].sum()) if hit_cnt else 0
    bad_rate = float(hit_df[target_col].mean()) if hit_cnt else np.nan
    hit_rate = hit_cnt / len(df) if len(df) else np.nan
    bad_capture = bad_cnt / total_bad if total_bad else np.nan
    overall_bad_rate = float(df[target_col].mean())
    lift = bad_rate / overall_bad_rate if overall_bad_rate > 0 and not np.isnan(bad_rate) else np.nan
    ruled_df = df.copy()
    ruled_df["hit_any"] = mask.astype(int)
    ruled_df["hit_sum"] = mask.astype(int)
    effect = calc_strategy_effect(raw_df, df, ruled_df, target_col, scenario).iloc[0]
    score = (
        (0 if np.isnan(lift) else max(lift - 1.0, 0.0))
        * math.sqrt(max(hit_rate, 0.0))
        * max(bad_capture, 0.0)
        * (1.0 + max(effect["bad_rate_drop_abs"], 0.0))
    )
    return {
        "scenario": scenario,
        "feature_bundle": feature_bundle,
        "rule_name": rule_name,
        "left_feature": left_feature,
        "left_operator": left_operator,
        "left_threshold": left_threshold,
        "right_feature": right_feature,
        "right_operator": right_operator,
        "right_threshold": right_threshold,
        "hit_cnt": hit_cnt,
        "bad_cnt": bad_cnt,
        "hit_rate": hit_rate,
        "bad_rate": bad_rate,
        "lift": lift,
        "bad_capture": bad_capture,
        "after_bad_rate": effect["after_bad_rate"],
        "after_pass_rate": effect["after_pass_rate"],
        "bad_rate_drop_abs": effect["bad_rate_drop_abs"],
        "pass_rate_drop_abs": effect["pass_rate_drop_abs"],
        "grid_score": score,
    }


def build_rule_expr(feature: str, operator: str, threshold: float) -> str:
    return f"`{feature}` {operator} {threshold}"


def run_grid_search(df: pd.DataFrame, passed_df: pd.DataFrame, config: Config, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidate_features = [feature for feature in config.grid_candidate_features if feature in passed_df.columns]
    single_rows: List[Dict[str, object]] = []

    for feature in candidate_features:
        for threshold in build_grid_threshold_candidates(passed_df[feature]):
            for operator in ("<", ">="):
                expr = build_rule_expr(feature, operator, threshold)
                mask = passed_df.eval(expr)
                single_rows.append(
                    evaluate_grid_mask(
                        df=passed_df,
                        raw_df=df,
                        mask=mask,
                        target_col=config.target_col,
                        scenario="single_grid_rule",
                        rule_name=f"{feature} {operator} {threshold}",
                        feature_bundle=feature,
                        left_feature=feature,
                        left_operator=operator,
                        left_threshold=threshold,
                    )
                )

    single_df = pd.DataFrame(single_rows)
    if single_df.empty:
        empty = pd.DataFrame()
        save_df(empty, output_dir / "07_grid_single_rule_candidates.csv")
        save_df(empty, output_dir / "08_grid_top_rules.csv")
        return empty, empty

    single_df = single_df.sort_values(
        ["grid_score", "lift", "bad_capture"], ascending=[False, False, False]
    ).reset_index(drop=True)
    save_df(single_df, output_dir / "07_grid_single_rule_candidates.csv")
    filtered_single = single_df[
        (single_df["hit_rate"] >= config.grid_min_hit_rate)
        & (single_df["hit_rate"] <= config.grid_max_hit_rate)
        & (single_df["lift"] >= config.grid_min_lift)
        & (single_df["bad_capture"] >= config.grid_min_bad_capture)
    ].copy()

    top_single = filtered_single.head(config.grid_pair_top_k_single_rules).copy()
    pair_rows: List[Dict[str, object]] = []
    for left_idx in range(len(top_single) - 1):
        left = top_single.iloc[left_idx]
        left_rule = left["rule_name"]
        left_feature = left["left_feature"]
        left_operator = left["left_operator"]
        left_threshold = float(left["left_threshold"])
        left_mask = passed_df.eval(build_rule_expr(left_feature, left_operator, left_threshold))
        for right_idx in range(left_idx + 1, len(top_single)):
            right = top_single.iloc[right_idx]
            right_feature = right["left_feature"]
            if left_feature == right_feature:
                continue
            right_rule = right["rule_name"]
            right_operator = right["left_operator"]
            right_threshold = float(right["left_threshold"])
            right_mask = passed_df.eval(build_rule_expr(right_feature, right_operator, right_threshold))
            pair_rows.append(
                evaluate_grid_mask(
                    df=passed_df,
                    raw_df=df,
                    mask=(left_mask & right_mask),
                    target_col=config.target_col,
                    scenario="pair_grid_rule",
                    rule_name=f"{left_rule} and {right_rule}",
                    feature_bundle=f"{left_feature} + {right_feature}",
                    left_feature=left_feature,
                    left_operator=left_operator,
                    left_threshold=left_threshold,
                    right_feature=right_feature,
                    right_operator=right_operator,
                    right_threshold=right_threshold,
                )
            )

    pair_df = pd.DataFrame(pair_rows)
    if not pair_df.empty:
        save_df(pair_df, output_dir / "07_grid_pair_rule_candidates.csv")
    combined = pd.concat([filtered_single, pair_df], ignore_index=True) if not pair_df.empty else filtered_single.copy()
    combined = combined.sort_values(
        ["grid_score", "lift", "bad_capture"], ascending=[False, False, False]
    ).reset_index(drop=True)
    save_df(combined.head(config.grid_top_n), output_dir / "08_grid_top_rules.csv")
    return filtered_single, combined


def cross_analysis(df: pd.DataFrame, config: Config, overall_bad_rate: float, output_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """二维交叉分析，输出 lift 矩阵、样本占比矩阵和热力图。"""
    count_matrix = pd.crosstab(df[config.cross_index], df[config.cross_columns])
    bad_matrix = df.pivot_table(
        index=config.cross_index,
        columns=config.cross_columns,
        values=config.target_col,
        aggfunc="sum",
    ).reindex(index=count_matrix.index, columns=count_matrix.columns)
    bad_rate_matrix = bad_matrix / count_matrix.replace(0, np.nan)
    lift_matrix = bad_rate_matrix / overall_bad_rate
    pct_matrix = count_matrix * 100 / df.shape[0]

    lift_matrix.to_csv(output_dir / "05_cross_lift_matrix.csv", encoding="utf-8-sig")
    pct_matrix.to_csv(output_dir / "05_cross_sample_pct_matrix.csv", encoding="utf-8-sig")

    plt.figure(figsize=(18, 7))
    plt.subplot(1, 2, 1)
    sns.heatmap(lift_matrix, cmap="coolwarm", annot=True, fmt=".2f", linewidths=0.5)
    plt.xlabel(config.cross_columns)
    plt.ylabel(config.cross_index)
    plt.title("Lift Matrix")

    plt.subplot(1, 2, 2)
    sns.heatmap(pct_matrix, cmap="coolwarm", annot=True, fmt=".2f", linewidths=0.5)
    plt.xlabel(config.cross_columns)
    plt.ylabel(config.cross_index)
    plt.title("Sample Percent (%)")

    plt.tight_layout()
    plt.savefig(output_dir / "05_cross_heatmap.png", dpi=160, bbox_inches="tight")
    plt.close()
    return lift_matrix, pct_matrix


def write_overview(df: pd.DataFrame, passed_df: pd.DataFrame, config: Config, output_dir: Path) -> pd.DataFrame:
    overview = pd.DataFrame(
        [
            {"metric": "raw_sample_cnt", "value": df.shape[0]},
            {"metric": "passed_observed_sample_cnt", "value": passed_df.shape[0]},
            {"metric": "passed_observed_sample_pct", "value": passed_df.shape[0] / df.shape[0]},
            {"metric": "overall_bad_rate", "value": passed_df[config.target_col].mean()},
            {"metric": "input_columns", "value": ", ".join(df.columns.astype(str))},
        ]
    )
    save_df(overview, output_dir / "00_data_overview.csv")
    return overview


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Strategy D-class tuning")
    parser.add_argument("--input", default=CONFIG.input_file, help="?? Excel ??")
    parser.add_argument("--output", default=CONFIG.output_dir, help="????")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> Config:
    cfg = Config()
    cfg.input_file = args.input
    cfg.output_dir = args.output
    return cfg


def run(config: Config = CONFIG) -> None:
    output_dir = Path(config.output_dir)
    ensure_dir(output_dir)

    df = load_data(config)
    passed_df = prepare_passed_sample(df, config)
    overall_bad_rate = float(passed_df[config.target_col].mean())
    print(f"????: {df.shape[0]}????????: {passed_df.shape[0]}??????: {overall_bad_rate:.4%}")

    overview = write_overview(df, passed_df, config, output_dir)

    existing_features = get_existing_features(passed_df, config)
    existing_metrics, existing_bins = bins_calc(passed_df, existing_features, config, overall_bad_rate)
    save_df(existing_metrics, output_dir / "01_existing_var_metrics.csv")
    save_df(existing_bins, output_dir / "01_existing_var_bins.csv")

    new_metrics, new_bins = bins_calc(passed_df, list(config.new_features), config, overall_bad_rate)
    save_df(new_metrics, output_dir / "02_new_var_metrics.csv")
    save_df(new_bins, output_dir / "02_new_var_bins.csv")

    _, existing_ruled_df, existing_hit_dist, existing_hit_summary = ruleset_calc(passed_df, config.existing_rules)
    save_df(existing_hit_dist, output_dir / "03_existing_rules_hit_dist.csv")
    save_df(existing_hit_summary, output_dir / "03_existing_rules_hit_summary.csv")

    _, single_ruled_df, single_hit_dist, single_hit_summary = ruleset_calc(passed_df, config.single_var_rules)
    save_df(single_hit_dist, output_dir / "04_single_rule_hit_dist.csv")
    save_df(single_hit_summary, output_dir / "04_single_rule_hit_summary.csv")
    single_effect = calc_strategy_effect(df, passed_df, single_ruled_df, config.target_col, "single_risk_score_rule")
    save_df(single_effect, output_dir / "04_single_rule_effect.csv")

    cross_analysis(passed_df, config, overall_bad_rate, output_dir)

    _, cross_ruled_df, cross_hit_dist, cross_hit_summary = ruleset_calc(passed_df, config.cross_rules)
    save_df(cross_hit_dist, output_dir / "06_cross_rule_hit_dist.csv")
    save_df(cross_hit_summary, output_dir / "06_cross_rule_hit_summary.csv")
    cross_effect = calc_strategy_effect(df, passed_df, cross_ruled_df, config.target_col, "cross_rule")
    save_df(cross_effect, output_dir / "06_cross_rule_effect.csv")
    _, grid_top = run_grid_search(df, passed_df, config, output_dir)

    run_summary = {
        "config": asdict(config),
        "data_overview": overview.to_dict(orient="records"),
        "top_existing_vars": existing_metrics.head(5).to_dict(orient="records"),
        "top_new_vars": new_metrics.head(5).to_dict(orient="records"),
        "single_rule_effect": single_effect.to_dict(orient="records"),
        "cross_rule_effect": cross_effect.to_dict(orient="records"),
    }
    (output_dir / "run_summary.json").write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n运行完成，输出文件已保存到:", output_dir.resolve())
    print("核心结果:")
    print(pd.concat([single_effect, cross_effect], ignore_index=True).to_string(index=False))


    if not grid_top.empty:
        print("Top grid-search rules:")
        print(grid_top.head(10).to_string(index=False))


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
