# -*- coding: utf-8 -*-
"""
Strategy Replacement Tuning Analysis

This script is a production-ready Python version of the original notebook.
It reads input data from input/, runs risk-score/card-level strategy replacement
analysis, and writes all tables/figures/reports to output/.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


@dataclass
class AnalysisConfig:
    """Central config layer: edit this class for new projects / new datasets."""

    input_path: str = "input/data_v5.xlsx"
    output_dir: str = "output"

    # Core fields
    sample_id_col: str = "sample_id"
    month_col: str = "sample_month"
    new_score_col: str = "risk_score"
    old_card_col: str = "card_level"
    target_col: str = "is_dlq_30d"

    # Business rules: 1 = reject, 0 = pass
    new_score_reject_cutoff: float = 6
    old_card_reject_levels: Tuple[str, ...] = ("D", "E")

    # Fixed risk-score bins used by the replacement analysis
    risk_score_bins: Tuple[float, ...] = (0, 2, 3, 4, 5, 6, 10)
    card_level_order: Tuple[str, ...] = ("A", "B", "C", "D", "E")

    # Plot switch
    save_plots: bool = True
    grid_min_score_cutoff: float = 2
    grid_max_score_cutoff: float = 8
    grid_top_n: int = 20


REQUIRED_COLUMNS = [
    "sample_id",
    "sample_month",
    "risk_score",
    "card_level",
    "is_dlq_30d",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input type: {suffix}. Please use .xlsx/.xls/.csv")


def validate_input(df: pd.DataFrame, cfg: AnalysisConfig) -> None:
    required = [
        cfg.sample_id_col,
        cfg.month_col,
        cfg.new_score_col,
        cfg.old_card_col,
        cfg.target_col,
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def save_table(df: pd.DataFrame, output_dir: Path, name: str, index: bool = False) -> Path:
    path = output_dir / name
    df.to_csv(path, index=index, encoding="utf-8-sig")
    return path


def interval_label(interval) -> str:
    if pd.isna(interval):
        return "missing"
    return str(interval)


def calc_bin_stats(
    df: pd.DataFrame,
    feature_col: str,
    target_col: str,
    total_bad_rate: float,
    bins: Optional[Iterable[float]] = None,
    categorical_order: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Calculate bin-level bad rate, lift, WOE and IV.

    This replaces notebook-only scorecardpy display logic with reproducible
    tables that can be saved in a normal Python script.
    """

    data = df[[feature_col, target_col]].copy()
    data = data.loc[data[target_col].notna()].reset_index(drop=True)
    data[target_col] = data[target_col].astype(int)

    if bins is not None:
        data["bin"] = pd.cut(
            data[feature_col],
            bins=list(bins),
            right=False,
            include_lowest=True,
        )
        sort_key = None
    else:
        data["bin"] = data[feature_col].astype("object").where(data[feature_col].notna(), "missing")
        sort_key = categorical_order

    grouped = (
        data.groupby("bin", observed=False)[target_col]
        .agg(total="count", bad="sum")
        .reset_index()
    )
    grouped["good"] = grouped["total"] - grouped["bad"]
    grouped["badprob"] = grouped["bad"] / grouped["total"].replace(0, np.nan)
    grouped["count_distr"] = grouped["total"] / grouped["total"].sum()
    grouped["lift"] = grouped["badprob"] / total_bad_rate if total_bad_rate > 0 else np.nan

    # WOE/IV with small smoothing to avoid division by zero.
    eps = 1e-8
    total_good = grouped["good"].sum()
    total_bad = grouped["bad"].sum()
    grouped["good_distr"] = grouped["good"] / total_good if total_good > 0 else np.nan
    grouped["bad_distr"] = grouped["bad"] / total_bad if total_bad > 0 else np.nan
    grouped["woe"] = np.log((grouped["bad_distr"] + eps) / (grouped["good_distr"] + eps))
    grouped["bin_iv"] = (grouped["bad_distr"] - grouped["good_distr"]) * grouped["woe"]
    grouped["total_iv"] = grouped["bin_iv"].sum()

    grouped.insert(0, "variable", feature_col)
    grouped["bin"] = grouped["bin"].map(interval_label)

    if sort_key:
        grouped["_sort"] = grouped["bin"].map({v: i for i, v in enumerate(sort_key)}).fillna(999)
        grouped = grouped.sort_values("_sort").drop(columns="_sort")

    return grouped[
        [
            "variable",
            "bin",
            "total",
            "good",
            "bad",
            "badprob",
            "count_distr",
            "lift",
            "good_distr",
            "bad_distr",
            "woe",
            "bin_iv",
            "total_iv",
        ]
    ]


def build_variable_summary(bin_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, table in bin_tables.items():
        rows.append(
            {
                "variable": name,
                "iv": table["total_iv"].iloc[0] if not table.empty else np.nan,
                "max_lift": table["lift"].max() if not table.empty else np.nan,
                "max_badprob": table["badprob"].max() if not table.empty else np.nan,
                "bin_cnt": table.shape[0],
            }
        )
    return pd.DataFrame(rows).sort_values(["iv", "max_lift"], ascending=[False, False])


def decision_matrices(df: pd.DataFrame, cfg: AnalysisConfig) -> Dict[str, pd.DataFrame]:
    x = df.copy()
    x["risk_score_hit"] = (x[cfg.new_score_col] >= cfg.new_score_reject_cutoff).astype(int)
    x["card_level_hit"] = x[cfg.old_card_col].isin(cfg.old_card_reject_levels).astype(int)

    bad_sum = x.pivot_table(
        index="card_level_hit",
        columns="risk_score_hit",
        values=cfg.target_col,
        aggfunc="sum",
        margins=True,
    )
    all_sum = pd.crosstab(x["card_level_hit"], x["risk_score_hit"], margins=True)
    bad_rate = bad_sum / all_sum
    pass_rate = all_sum / len(x)

    # Stable names for downstream outputs.
    bad_sum.index.name = "card_level_hit"
    all_sum.index.name = "card_level_hit"
    bad_rate.index.name = "card_level_hit"
    pass_rate.index.name = "card_level_hit"

    return {
        "data_with_hits": x,
        "bad_sum": bad_sum,
        "all_sum": all_sum,
        "bad_rate": bad_rate,
        "pass_rate": pass_rate,
    }


def replacement_estimation(
    df: pd.DataFrame,
    risk_bin_table: pd.DataFrame,
    decision: Dict[str, pd.DataFrame],
    cfg: AnalysisConfig,
) -> Dict[str, pd.DataFrame]:
    x = decision["data_with_hits"].copy()

    # Rejected by old card model: no observed post-loan target in this sample.
    rejected = x.loc[x[cfg.target_col].isna()].reset_index(drop=True)
    rejected_bins = (
        pd.cut(
            rejected[cfg.new_score_col],
            bins=list(cfg.risk_score_bins),
            right=False,
            include_lowest=True,
        )
        .value_counts()
        .sort_index()
        .to_frame(name="reject_sample_cnt")
        .reset_index()
        .rename(columns={cfg.new_score_col: "bin"})
    )
    # Depending on pandas version, the reset column may be called 'index'.
    if "index" in rejected_bins.columns:
        rejected_bins = rejected_bins.rename(columns={"index": "bin"})
    rejected_bins["bin"] = rejected_bins["bin"].map(interval_label)

    risk_cols = ["bin", "total", "bad", "badprob", "lift", "total_iv"]
    merged = risk_bin_table[risk_cols].merge(rejected_bins, on="bin", how="left")
    merged["reject_sample_cnt"] = merged["reject_sample_cnt"].fillna(0).astype(int)
    merged["estimated_bad_cnt"] = merged["reject_sample_cnt"] * merged["badprob"]
    merged["is_new_model_pass_bin"] = merged["bin"].apply(lambda s: not s.startswith(f"[{int(cfg.new_score_reject_cutoff)},"))

    # More robust pass-bin logic: use interval lower bound when parseable.
    # For current bins and cutoff=6, the first five bins are new-model pass bins.
    pass_bin_count = sum(np.array(cfg.risk_score_bins[:-1]) < cfg.new_score_reject_cutoff)
    merged["is_new_model_pass_bin"] = [i < pass_bin_count for i in range(len(merged))]

    cutoff_estimated_bad = merged.loc[merged["is_new_model_pass_bin"], "estimated_bad_cnt"].sum()

    bad_sum_after = decision["bad_sum"].copy()
    # Cell: old model reject (card_level_hit=1), new model pass (risk_score_hit=0)
    if 1 in bad_sum_after.index and 0 in bad_sum_after.columns:
        bad_sum_after.loc[1, 0] = cutoff_estimated_bad

    bad_rate_after = bad_sum_after / decision["all_sum"]

    return {
        "reject_distribution": rejected_bins,
        "replacement_estimation": merged,
        "bad_sum_after_replacement": bad_sum_after,
        "bad_rate_after_replacement": bad_rate_after,
    }


def plot_badrate_by_bin(table: pd.DataFrame, output_dir: Path, name: str) -> None:
    fig, ax1 = plt.subplots(figsize=(10, 5))
    labels = table["bin"].astype(str).tolist()
    x = np.arange(len(labels))

    ax1.bar(x, table["total"], alpha=0.65, label="sample count")
    ax1.set_ylabel("sample count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=35, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(x, table["badprob"], marker="o", label="bad rate")
    ax2.set_ylabel("bad rate")

    plt.title(f"Bad Rate by {name} Bin")
    fig.tight_layout()
    fig.savefig(output_dir / f"bad_rate_by_{name}.png", dpi=180)
    plt.close(fig)


def plot_replacement(table: pd.DataFrame, output_dir: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(10, 5))
    labels = table["bin"].astype(str).tolist()
    x = np.arange(len(labels))

    ax1.bar(x, table["reject_sample_cnt"], alpha=0.65, label="old-reject sample count")
    ax1.set_ylabel("old-reject sample count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=35, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(x, table["estimated_bad_cnt"], marker="o", label="estimated bad count")
    ax2.set_ylabel("estimated bad count")

    plt.title("Replacement Estimation by Risk Score Bin")
    fig.tight_layout()
    fig.savefig(output_dir / "replacement_estimation_by_risk_score_bin.png", dpi=180)
    plt.close(fig)


def plot_final_summary(summary: Dict[str, float], output_dir: Path) -> None:
    metrics = pd.DataFrame(
        {
            "metric": ["old_card_pass_rate", "new_score_pass_rate", "new_in_old_reject_bad_rate"],
            "value": [
                summary["old_card_pass_rate"],
                summary["new_score_pass_rate"],
                summary["new_pass_old_reject_estimated_bad_rate"],
            ],
        }
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(metrics["metric"], metrics["value"])
    ax.set_ylabel("rate")
    ax.set_ylim(0, max(metrics["value"].max() * 1.25, 0.1))
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(metrics["metric"], rotation=20, ha="right")
    for i, v in enumerate(metrics["value"]):
        ax.text(i, v, f"{v:.2%}", ha="center", va="bottom")
    plt.title("Final Strategy Replacement Summary")
    fig.tight_layout()
    fig.savefig(output_dir / "final_strategy_summary.png", dpi=180)
    plt.close(fig)


def build_text_report(summary: Dict[str, float]) -> str:
    return f"""策略置换调优分析报告
====================

核心结论
--------
1. 旧评分卡模型通过率：{summary['old_card_pass_rate']:.2%}
2. 新风险模型通过率：{summary['new_score_pass_rate']:.2%}
3. 新模型相对旧模型预计通过率提升：{summary['pass_rate_uplift']:.2%}
4. 新模型通过人群整体历史坏账率：{summary['new_score_pass_observed_bad_rate']:.2%}
5. 旧模型拒绝、但新模型通过的人群，按通过样本同风险分箱坏账率估算后的坏账率：{summary['new_pass_old_reject_estimated_bad_rate']:.2%}
6. 旧模型通过、但新模型拒绝的人群历史坏账率：{summary['old_pass_new_reject_observed_bad_rate']:.2%}

方法说明
--------
- 旧模型：card_level in ('D', 'E') 视为拒绝，其余视为通过。
- 新模型：risk_score >= 6 视为拒绝，risk_score < 6 视为通过。
- 对旧模型拒绝样本，由于没有真实贷后表现，使用通过样本中 risk_score 分箱对应坏账率进行估算。
- 置入样本：旧模型拒绝但新模型通过的人群。
- 置出样本：旧模型通过但新模型拒绝的人群。

业务解读
--------
如果置入样本的估算坏账率明显低于置出样本的真实坏账率，同时新模型通过率更高，说明新模型在扩大通过量的同时没有显著放大风险，具备替换旧规则/旧模型的业务价值。
"""


def score_replacement_grid_row(row: pd.Series) -> float:
    pass_uplift = row.get("pass_rate_uplift", np.nan)
    estimated_bad_rate = row.get("new_pass_old_reject_estimated_bad_rate", np.nan)
    old_reject_bad_rate = row.get("old_pass_new_reject_observed_bad_rate", np.nan)
    new_pass_bad_rate = row.get("new_score_pass_observed_bad_rate", np.nan)
    if pd.isna(pass_uplift) or pd.isna(estimated_bad_rate) or pd.isna(old_reject_bad_rate):
        return -np.inf
    risk_gap = old_reject_bad_rate - estimated_bad_rate
    score = (
        1.5 * pass_uplift
        + 1.0 * max(risk_gap, 0.0)
        - 0.5 * max(estimated_bad_rate - new_pass_bad_rate, 0.0)
    )
    return float(score)


def safe_matrix_value(df: pd.DataFrame, row_key, col_key) -> float:
    if row_key not in df.index or col_key not in df.columns:
        return float("nan")
    value = df.loc[row_key, col_key]
    if pd.isna(value):
        return float("nan")
    return float(value)


def compute_summary_from_matrices(
    total_n: int,
    observed_n: int,
    missing_target_n: int,
    total_bad_rate: float,
    all_sum: pd.DataFrame,
    bad_rate_original: pd.DataFrame,
    bad_rate_after: pd.DataFrame,
) -> Dict[str, float]:
    old_card_pass_rate = safe_matrix_value(all_sum, 0, "All") / total_n
    new_score_pass_rate = safe_matrix_value(all_sum, "All", 0) / total_n
    return {
        "total_sample_cnt": int(total_n),
        "observed_target_sample_cnt": int(observed_n),
        "missing_target_sample_cnt": int(missing_target_n),
        "observed_bad_rate": float(total_bad_rate),
        "old_card_pass_rate": float(old_card_pass_rate),
        "new_score_pass_rate": float(new_score_pass_rate),
        "pass_rate_uplift": float(new_score_pass_rate - old_card_pass_rate),
        "new_score_pass_observed_bad_rate": safe_matrix_value(bad_rate_original, "All", 0),
        "new_pass_old_reject_estimated_bad_rate": safe_matrix_value(bad_rate_after, 1, 0),
        "old_pass_new_reject_observed_bad_rate": safe_matrix_value(bad_rate_original, 0, 1),
    }


def build_reject_level_sets(df: pd.DataFrame, cfg: AnalysisConfig) -> List[Tuple[str, ...]]:
    card_levels = [str(v) for v in df[cfg.old_card_col].dropna().astype(str).unique().tolist()]
    ordered_levels = [level for level in cfg.card_level_order if level in card_levels]
    ordered_levels.extend([level for level in sorted(card_levels) if level not in ordered_levels])
    reject_level_sets = [tuple(ordered_levels[idx:]) for idx in range(len(ordered_levels)) if ordered_levels[idx:]]
    if tuple(cfg.old_card_reject_levels) not in reject_level_sets:
        reject_level_sets.append(tuple(cfg.old_card_reject_levels))
    return reject_level_sets


def evaluate_strategy_config(df: pd.DataFrame, cfg: AnalysisConfig) -> Dict[str, float]:
    observed = df.loc[df[cfg.target_col].notna()].reset_index(drop=True).copy()
    observed[cfg.target_col] = observed[cfg.target_col].astype(int)
    total_bad_rate = observed[cfg.target_col].mean()

    risk_bin_table = calc_bin_stats(
        observed,
        cfg.new_score_col,
        cfg.target_col,
        total_bad_rate,
        bins=cfg.risk_score_bins,
    )
    decision = decision_matrices(df, cfg)
    repl = replacement_estimation(df, risk_bin_table, decision, cfg)

    total_n = len(df)
    all_sum = decision["all_sum"]
    bad_rate_after = repl["bad_rate_after_replacement"]
    bad_rate_original = decision["bad_rate"]
    summary = compute_summary_from_matrices(
        total_n=total_n,
        observed_n=len(observed),
        missing_target_n=int(df[cfg.target_col].isna().sum()),
        total_bad_rate=float(total_bad_rate),
        all_sum=all_sum,
        bad_rate_original=bad_rate_original,
        bad_rate_after=bad_rate_after,
    )
    return {
        "score_cutoff": float(cfg.new_score_reject_cutoff),
        "old_reject_levels": ",".join(cfg.old_card_reject_levels),
        **summary,
    }


def run_grid_search(df: pd.DataFrame, cfg: AnalysisConfig, output_dir: Path) -> pd.DataFrame:
    score_candidates = sorted(
        {
            float(v)
            for v in pd.to_numeric(df[cfg.new_score_col], errors="coerce").dropna().unique().tolist()
            if cfg.grid_min_score_cutoff <= float(v) <= cfg.grid_max_score_cutoff
        }
    )
    if not score_candidates:
        score_candidates = [float(cfg.new_score_reject_cutoff)]

    reject_level_sets = build_reject_level_sets(df, cfg)

    rows: List[Dict[str, float]] = []
    for score_cutoff in score_candidates:
        for reject_levels in reject_level_sets:
            candidate_cfg = replace(
                cfg,
                new_score_reject_cutoff=score_cutoff,
                old_card_reject_levels=tuple(reject_levels),
                save_plots=False,
            )
            row = evaluate_strategy_config(df, candidate_cfg)
            row["grid_score"] = score_replacement_grid_row(pd.Series(row))
            rows.append(row)

    result = pd.DataFrame(rows).sort_values(
        ["grid_score", "pass_rate_uplift", "new_pass_old_reject_estimated_bad_rate"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    save_table(result, output_dir, "grid_search_results.csv")
    save_table(result.head(cfg.grid_top_n), output_dir, "grid_search_top_configs.csv")
    return result


def run(cfg: AnalysisConfig) -> Dict[str, float]:
    input_path = Path(cfg.input_path)
    output_dir = Path(cfg.output_dir)
    ensure_dir(output_dir)

    df = load_data(input_path)
    validate_input(df, cfg)

    # Keep original notebook semantics: observed target samples are pass-through samples.
    observed = df.loc[df[cfg.target_col].notna()].reset_index(drop=True)
    observed[cfg.target_col] = observed[cfg.target_col].astype(int)
    total_bad_rate = observed[cfg.target_col].mean()

    sample_overview = pd.DataFrame(
        [
            {"metric": "total_sample_cnt", "value": len(df)},
            {"metric": "observed_target_sample_cnt", "value": len(observed)},
            {"metric": "missing_target_sample_cnt", "value": df[cfg.target_col].isna().sum()},
            {"metric": "observed_bad_cnt", "value": observed[cfg.target_col].sum()},
            {"metric": "observed_bad_rate", "value": total_bad_rate},
        ]
    )
    save_table(sample_overview, output_dir, "sample_overview.csv")

    # Binning analysis.
    bin_tables: Dict[str, pd.DataFrame] = {}
    bin_tables[cfg.new_score_col] = calc_bin_stats(
        observed,
        cfg.new_score_col,
        cfg.target_col,
        total_bad_rate,
        bins=cfg.risk_score_bins,
    )
    card_order = ["A", "B", "C", "D", "E"]
    bin_tables[cfg.old_card_col] = calc_bin_stats(
        observed,
        cfg.old_card_col,
        cfg.target_col,
        total_bad_rate,
        categorical_order=card_order,
    )

    for name, table in bin_tables.items():
        save_table(table, output_dir, f"binning_detail_{name}.csv")

    variable_summary = build_variable_summary(bin_tables)
    save_table(variable_summary, output_dir, "variable_binning_summary.csv")

    # Decision matrix analysis.
    decision = decision_matrices(df, cfg)
    save_table(decision["bad_sum"].reset_index(), output_dir, "decision_matrix_bad_count_original.csv")
    save_table(decision["all_sum"].reset_index(), output_dir, "decision_matrix_total_count.csv")
    save_table(decision["bad_rate"].reset_index(), output_dir, "decision_matrix_bad_rate_original.csv")
    save_table(decision["pass_rate"].reset_index(), output_dir, "decision_matrix_pass_rate.csv")

    # Replacement estimation.
    repl = replacement_estimation(df, bin_tables[cfg.new_score_col], decision, cfg)
    save_table(repl["reject_distribution"], output_dir, "reject_distribution_risk_score.csv")
    save_table(repl["replacement_estimation"], output_dir, "replacement_estimation.csv")
    save_table(
        repl["bad_sum_after_replacement"].reset_index(),
        output_dir,
        "decision_matrix_bad_count_after_replacement.csv",
    )
    save_table(
        repl["bad_rate_after_replacement"].reset_index(),
        output_dir,
        "decision_matrix_bad_rate_after_replacement.csv",
    )

    # Final KPI summary.
    total_n = len(df)
    all_sum = decision["all_sum"]
    bad_rate_after = repl["bad_rate_after_replacement"]
    bad_rate_original = decision["bad_rate"]
    summary = compute_summary_from_matrices(
        total_n=total_n,
        observed_n=len(observed),
        missing_target_n=int(df[cfg.target_col].isna().sum()),
        total_bad_rate=float(total_bad_rate),
        all_sum=all_sum,
        bad_rate_original=bad_rate_original,
        bad_rate_after=bad_rate_after,
    )

    with open(output_dir / "final_summary.json", "w", encoding="utf-8") as f:
        json.dump({"config": asdict(cfg), "summary": summary}, f, ensure_ascii=False, indent=2)
    with open(output_dir / "analysis_report.txt", "w", encoding="utf-8") as f:
        f.write(build_text_report(summary))

    if cfg.save_plots:
        plot_badrate_by_bin(bin_tables[cfg.new_score_col], output_dir, cfg.new_score_col)
        plot_badrate_by_bin(bin_tables[cfg.old_card_col], output_dir, cfg.old_card_col)
        plot_replacement(repl["replacement_estimation"], output_dir)
        plot_final_summary(summary, output_dir)

    grid_df = run_grid_search(df, cfg, output_dir)

    print("Analysis completed.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Top replacement grid-search configs:")
    print(grid_df.head(10).to_string(index=False))
    print(f"Outputs saved to: {output_dir.resolve()}")
    return summary


def parse_args() -> AnalysisConfig:
    parser = argparse.ArgumentParser(description="Run strategy replacement tuning analysis.")
    parser.add_argument("--input", default="input/data_v5.xlsx", help="Input Excel/CSV path.")
    parser.add_argument("--output", default="output", help="Output directory.")
    parser.add_argument("--score-cutoff", type=float, default=6, help="risk_score reject cutoff; >= cutoff means reject.")
    parser.add_argument(
        "--old-reject-levels",
        default="D,E",
        help="Comma-separated old card levels treated as reject, e.g. D,E.",
    )
    parser.add_argument("--no-plots", action="store_true", help="Disable PNG plot outputs.")
    args = parser.parse_args()

    return AnalysisConfig(
        input_path=args.input,
        output_dir=args.output,
        new_score_reject_cutoff=args.score_cutoff,
        old_card_reject_levels=tuple(x.strip() for x in args.old_reject_levels.split(",") if x.strip()),
        save_plots=not args.no_plots,
    )


def build_config(args: AnalysisConfig) -> AnalysisConfig:
    return args


if __name__ == "__main__":
    run(parse_args())


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
