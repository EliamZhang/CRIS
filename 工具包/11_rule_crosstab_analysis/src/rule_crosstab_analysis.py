# -*- coding: utf-8 -*-
"""Rule crosstab analysis business logic."""

from __future__ import annotations

import argparse
import io
import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

INPUT_FILE = Path("input/lending_club_loan_two.csv")
OUTPUT_DIR = Path("output")
TARGET_COL = "loan_status"
TARGET_MAPPING = {"Fully Paid": 0, "Charged Off": 1}
EXCLUDE_COLS = ["issue_d", "address", "emp_title", "earliest_cr_line", "title"]
INT_RATE_BINS = [-math.inf, 7, 8, 11.5, 12.5, 14.5, 16.5, 21.5, math.inf]
DTI_BINS = [-math.inf, 8, 13, 17, 21, 23, 26, 30, math.inf]
IV_BIN_COUNT = 10
IV_THRESHOLD = 0.10
MAX_CATEGORY_UNIQUE_FOR_PLOT = 30
RULES = [
    {"rule_name": "int_rate > 21.5 and grade == G", "int_rate_gt": 21.5, "grade_in": ["G"]},
    {"rule_name": "int_rate > 21.5 and grade in (F, G)", "int_rate_gt": 21.5, "grade_in": ["F", "G"]},
]

AUTO_SEARCH_MAX_FEATURES = 14
AUTO_SEARCH_MAX_CATEGORY_UNIQUE = 12
AUTO_SEARCH_MAX_BIN_COUNT = 6
AUTO_SEARCH_MIN_SAMPLE_COUNT = 300
AUTO_SEARCH_MIN_HIT_RATE = 0.005
AUTO_SEARCH_MAX_HIT_RATE = 0.35
AUTO_SEARCH_MIN_LIFT = 1.20
AUTO_SEARCH_MIN_BAD_RATE = 0.22
AUTO_SEARCH_MIN_BAD_CAPTURE = 0.02
AUTO_SEARCH_TOP_CELLS_PER_PAIR = 5
AUTO_SEARCH_TOP_PAIR_COUNT = 30
AUTO_SEARCH_HEATMAP_PAIR_COUNT = 6
AUTO_SEARCH_TOP_N_RULES = 50
EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_COLS = 16_384


@dataclass
class RuntimeConfig:
    input_file: Path
    output_dir: Path


def build_sheet_name(name: str) -> str:
    safe = re.sub(r"[:\\/?*\[\]]+", "_", str(name)).strip()
    return (safe or "sheet")[:31]


def write_summary_report(output_dir: Path, sheets: dict[str, pd.DataFrame]) -> Path:
    output_path = output_dir / "summary_report.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        used_names: set[str] = set()
        for sheet_name, df in sheets.items():
            base_name = build_sheet_name(sheet_name)
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
                    final_name = f"{base_name[:31 - len(suffix)]}{suffix}"
                    while final_name in used_names:
                        final_name = f"{final_name[:28]}_{len(used_names) % 1000:03d}"[:31]
                    used_names.add(final_name)
                    part_df.to_excel(writer, sheet_name=final_name, index=False)
    return output_path


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def setup_plot_style() -> None:
    plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def load_data(input_file: Path) -> pd.DataFrame:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    return pd.read_csv(input_file)


def simple_statistics(df: pd.DataFrame) -> pd.DataFrame:
    stats = []
    for col in df.columns:
        vc = df[col].value_counts(normalize=True, dropna=False)
        mode_pct = float(vc.iloc[0] * 100) if len(vc) else np.nan
        stats.append(
            {
                "feature": col,
                "unique_values": df[col].nunique(dropna=True),
                "percentage_of_null": float(df[col].isna().mean() * 100),
                "percentage_of_mode": mode_pct,
                "type": str(df[col].dtype),
            }
        )
    return pd.DataFrame(stats).sort_values("unique_values", ascending=False)


def save_basic_eda(df: pd.DataFrame, output_dir: Path) -> None:
    pd.DataFrame({"rows": [df.shape[0]], "columns": [df.shape[1]]}).to_csv(
        output_dir / "01_data_shape.csv", index=False, encoding="utf-8-sig"
    )
    df.describe(include="all").to_csv(output_dir / "02_describe.csv", encoding="utf-8-sig")

    buffer = io.StringIO()
    df.info(buf=buffer)
    (output_dir / "03_info.txt").write_text(buffer.getvalue(), encoding="utf-8")

    simple_statistics(df).to_csv(output_dir / "04_simple_statistics.csv", index=False, encoding="utf-8-sig")


def prepare_target(df: pd.DataFrame, target_col: str, target_mapping: dict) -> pd.DataFrame:
    if target_col not in df.columns:
        raise KeyError(f"Target column not found: {target_col}")

    df = df.copy()
    if df[target_col].dtype == "object":
        df[target_col] = df[target_col].map(target_mapping)

    df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
    df = df[df[target_col].isin([0, 1])].copy()
    df[target_col] = df[target_col].astype(int)
    return df


def split_features(df: pd.DataFrame, target_col: str, exclude_cols: Iterable[str]) -> tuple[list[str], list[str]]:
    exclude = set(exclude_cols) | {target_col}
    candidate_cols = [c for c in df.columns if c not in exclude]
    num_cols = df[candidate_cols].select_dtypes(include=["number"]).columns.tolist()
    obj_cols = df[candidate_cols].select_dtypes(include=["object", "category"]).columns.tolist()
    return num_cols, obj_cols


def plot_target_distribution(df: pd.DataFrame, target_col: str, output_dir: Path) -> None:
    plt.figure(figsize=(8, 5))
    df[target_col].value_counts(dropna=False).sort_index().plot(kind="bar")
    plt.title("Target Distribution")
    plt.xlabel(target_col)
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(output_dir / "05_target_distribution.png", dpi=160)
    plt.close()


def plot_categorical_badrate(
    df: pd.DataFrame,
    obj_cols: list[str],
    target_col: str,
    output_dir: Path,
    max_unique: int,
) -> None:
    plot_cols = [c for c in obj_cols if df[c].nunique(dropna=True) <= max_unique]
    if not plot_cols:
        return

    n = len(plot_cols)
    ncols = 2
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, max(5, 4 * nrows)))
    axes = np.array(axes).reshape(-1)

    for ax, col in zip(axes, plot_cols):
        tmp = df.groupby(col, dropna=False)[target_col].mean().reset_index(name="bad_rate")
        tmp[col] = tmp[col].astype(str)
        ax.bar(tmp[col], tmp["bad_rate"])
        ax.set_title(f"{col} bad rate")
        ax.tick_params(axis="x", labelrotation=45)
        ax.set_xlabel(col)
        ax.set_ylabel("bad_rate")

    for ax in axes[len(plot_cols):]:
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_dir / "06_categorical_badrate.png", dpi=160)
    plt.close()


def _make_numeric_bins(series: pd.Series, bin_count: int) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    valid_unique = x.nunique(dropna=True)
    if valid_unique <= 1:
        return pd.Series(["missing" if pd.isna(v) else "single_bin" for v in x], index=series.index)

    q = min(bin_count, valid_unique)
    try:
        bins = pd.qcut(x, q=q, duplicates="drop")
    except Exception:
        bins = pd.cut(x, bins=q, duplicates="drop")

    bins = bins.astype("object")
    bins[pd.isna(x)] = "missing"
    return bins.astype(str)


def calculate_numeric_iv(
    df: pd.DataFrame,
    num_cols: list[str],
    target_col: str,
    output_dir: Path,
    bin_count: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    total_bad = df[target_col].sum()
    total_good = (1 - df[target_col]).sum()
    eps = 0.5

    iv_rows = []
    bin_detail_rows = []

    for col in num_cols:
        binned = _make_numeric_bins(df[col], bin_count)
        tmp = pd.DataFrame({"bin": binned, target_col: df[target_col]})
        grouped = tmp.groupby("bin", dropna=False)[target_col].agg(["count", "sum"]).reset_index()
        grouped = grouped.rename(columns={"sum": "bad"})
        grouped["good"] = grouped["count"] - grouped["bad"]
        grouped["bad_rate"] = grouped["bad"] / grouped["count"].replace(0, np.nan)
        grouped["bad_dist"] = (grouped["bad"] + eps) / (total_bad + eps * len(grouped))
        grouped["good_dist"] = (grouped["good"] + eps) / (total_good + eps * len(grouped))
        grouped["woe"] = np.log(grouped["bad_dist"] / grouped["good_dist"])
        grouped["bin_iv"] = (grouped["bad_dist"] - grouped["good_dist"]) * grouped["woe"]
        total_iv = float(grouped["bin_iv"].sum())

        iv_rows.append({"variable": col, "iv": total_iv})
        grouped.insert(0, "variable", col)
        grouped["total_iv"] = total_iv
        bin_detail_rows.append(grouped)

    iv_table = pd.DataFrame(iv_rows).sort_values("iv", ascending=False)
    bin_detail = pd.concat(bin_detail_rows, ignore_index=True) if bin_detail_rows else pd.DataFrame()

    iv_table.to_csv(output_dir / "07_iv_table.csv", index=False, encoding="utf-8-sig")
    bin_detail.to_csv(output_dir / "08_iv_bins_detail.csv", index=False, encoding="utf-8-sig")
    return iv_table, bin_detail


def save_iv_selected(iv_table: pd.DataFrame, threshold: float, output_dir: Path) -> None:
    iv_table[iv_table["iv"] > threshold].to_csv(
        output_dir / "09_iv_selected_gt_threshold.csv", index=False, encoding="utf-8-sig"
    )


def plot_heatmap(df: pd.DataFrame, path: Path, title: str) -> None:
    plt.figure(figsize=(14, 8))
    sns.heatmap(df, annot=True, fmt=".2f", linewidths=0.5)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def build_cross_tables(
    df: pd.DataFrame,
    target_col: str,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = {"int_rate", "grade", target_col}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Cross table requires columns: {sorted(missing)}")

    work = df.copy()
    work["int_rate_bins"] = pd.cut(work["int_rate"], bins=INT_RATE_BINS)
    if "dti" in work.columns:
        work["dti_bins"] = pd.cut(work["dti"], bins=DTI_BINS)

    loan_cnt = pd.crosstab(work["int_rate_bins"], work["grade"], dropna=False)
    loan_bad_sum = work.pivot_table(index="int_rate_bins", columns="grade", values=target_col, aggfunc="sum")
    cross_badrate = loan_bad_sum / loan_cnt.replace(0, np.nan)
    loan_pct = loan_cnt / len(work)

    loan_cnt.to_csv(output_dir / "10_cross_loan_count.csv", encoding="utf-8-sig")
    loan_bad_sum.to_csv(output_dir / "11_cross_bad_count.csv", encoding="utf-8-sig")
    cross_badrate.to_csv(output_dir / "12_cross_bad_rate.csv", encoding="utf-8-sig")
    loan_pct.to_csv(output_dir / "13_cross_sample_pct.csv", encoding="utf-8-sig")
    plot_heatmap(cross_badrate.fillna(0), output_dir / "14_cross_bad_rate_heatmap.png", "int_rate_bins x grade bad rate")
    plot_heatmap(loan_pct.fillna(0), output_dir / "15_cross_sample_pct_heatmap.png", "int_rate_bins x grade sample pct")
    return loan_cnt, loan_bad_sum, cross_badrate, loan_pct


def evaluate_rules(df: pd.DataFrame, target_col: str, output_dir: Path) -> pd.DataFrame:
    overall_bad_rate = df[target_col].mean()
    total_bad = df[target_col].sum()
    total_good = (1 - df[target_col]).sum()
    rows = []

    for rule in RULES:
        mask = pd.Series(True, index=df.index)
        if "int_rate_gt" in rule:
            mask &= df["int_rate"] > rule["int_rate_gt"]
        if "grade_in" in rule:
            mask &= df["grade"].isin(rule["grade_in"])

        hit_df = df[mask]
        hit_cnt = len(hit_df)
        bad_cnt = int(hit_df[target_col].sum()) if hit_cnt else 0
        good_cnt = hit_cnt - bad_cnt
        bad_rate = float(hit_df[target_col].mean()) if hit_cnt else np.nan
        hit_rate = hit_cnt / len(df) if len(df) else np.nan
        lift = bad_rate / overall_bad_rate if overall_bad_rate and not np.isnan(bad_rate) else np.nan

        rows.append(
            {
                "rule_name": rule["rule_name"],
                "hit_cnt": hit_cnt,
                "bad_cnt": bad_cnt,
                "good_cnt": good_cnt,
                "hit_rate": hit_rate,
                "bad_rate": bad_rate,
                "overall_bad_rate": overall_bad_rate,
                "bad_capture": bad_cnt / total_bad if total_bad else np.nan,
                "good_capture": good_cnt / total_good if total_good else np.nan,
                "lift": lift,
            }
        )

    result = pd.DataFrame(rows).sort_values(["lift", "bad_cnt"], ascending=[False, False])
    result.to_csv(output_dir / "16_rule_evaluation.csv", index=False, encoding="utf-8-sig")
    return result


def _format_feature_value(series: pd.Series) -> pd.Series:
    out = series.astype("object")
    out[pd.isna(out)] = "missing"
    return out.astype(str)


def build_auto_search_feature_frame(
    df: pd.DataFrame,
    target_col: str,
    num_cols: list[str],
    obj_cols: list[str],
    iv_table: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metadata_rows = []
    feature_frame = pd.DataFrame(index=df.index)

    iv_rank = {row["variable"]: idx for idx, row in iv_table.reset_index(drop=True).iterrows()}
    ranked_num_cols = sorted(num_cols, key=lambda col: iv_rank.get(col, len(iv_rank)))

    selected_num_cols = ranked_num_cols[:AUTO_SEARCH_MAX_FEATURES]
    for col in selected_num_cols:
        feature_frame[col] = _make_numeric_bins(df[col], AUTO_SEARCH_MAX_BIN_COUNT)
        metadata_rows.append(
            {
                "feature": col,
                "feature_type": "numeric_binned",
                "source_column": col,
                "unique_values": feature_frame[col].nunique(dropna=False),
                "selection_reason": "top_iv_numeric",
            }
        )

    eligible_obj_cols = [
        col for col in obj_cols if 1 < df[col].nunique(dropna=True) <= AUTO_SEARCH_MAX_CATEGORY_UNIQUE
    ]
    for col in eligible_obj_cols[:AUTO_SEARCH_MAX_FEATURES]:
        feature_frame[col] = _format_feature_value(df[col])
        metadata_rows.append(
            {
                "feature": col,
                "feature_type": "categorical",
                "source_column": col,
                "unique_values": feature_frame[col].nunique(dropna=False),
                "selection_reason": "low_cardinality_categorical",
            }
        )

    metadata = pd.DataFrame(metadata_rows).sort_values(["feature_type", "feature"]).reset_index(drop=True)
    return feature_frame, metadata


def _score_rule_row(row: pd.Series) -> float:
    if pd.isna(row["lift"]) or pd.isna(row["bad_rate"]):
        return -np.inf
    return float(
        row["lift"] * math.sqrt(max(row["hit_rate"], 0)) * max(row["bad_capture"], 0)
    )


def _build_pair_rule_name(feature_1: str, value_1: str, feature_2: str, value_2: str) -> str:
    return f"{feature_1} == {value_1} and {feature_2} == {value_2}"


def evaluate_pair_segments(
    feature_frame: pd.DataFrame,
    target: pd.Series,
    feature_1: str,
    feature_2: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    total_count = len(feature_frame)
    total_bad = int(target.sum())
    total_good = total_count - total_bad
    overall_bad_rate = total_bad / total_count if total_count else np.nan

    work = pd.DataFrame(
        {
            "feature_1_value": feature_frame[feature_1].astype(str),
            "feature_2_value": feature_frame[feature_2].astype(str),
            "target": target.values,
        }
    )

    grouped = (
        work.groupby(["feature_1_value", "feature_2_value"], dropna=False)["target"]
        .agg(["count", "sum"])
        .reset_index()
        .rename(columns={"count": "hit_cnt", "sum": "bad_cnt"})
    )
    grouped["bad_cnt"] = grouped["bad_cnt"].astype(int)
    grouped["good_cnt"] = grouped["hit_cnt"] - grouped["bad_cnt"]
    grouped["hit_rate"] = grouped["hit_cnt"] / total_count
    grouped["bad_rate"] = grouped["bad_cnt"] / grouped["hit_cnt"].replace(0, np.nan)
    grouped["overall_bad_rate"] = overall_bad_rate
    grouped["bad_capture"] = grouped["bad_cnt"] / total_bad if total_bad else np.nan
    grouped["good_capture"] = grouped["good_cnt"] / total_good if total_good else np.nan
    grouped["lift"] = grouped["bad_rate"] / overall_bad_rate if overall_bad_rate else np.nan
    grouped["feature_1"] = feature_1
    grouped["feature_2"] = feature_2
    grouped["rule_name"] = grouped.apply(
        lambda row: _build_pair_rule_name(
            feature_1, row["feature_1_value"], feature_2, row["feature_2_value"]
        ),
        axis=1,
    )
    grouped["score"] = grouped.apply(_score_rule_row, axis=1)

    eligible = grouped[
        (grouped["hit_cnt"] >= AUTO_SEARCH_MIN_SAMPLE_COUNT)
        & (grouped["hit_rate"] >= AUTO_SEARCH_MIN_HIT_RATE)
        & (grouped["hit_rate"] <= AUTO_SEARCH_MAX_HIT_RATE)
        & (grouped["lift"] >= AUTO_SEARCH_MIN_LIFT)
        & (grouped["bad_rate"] >= AUTO_SEARCH_MIN_BAD_RATE)
        & (grouped["bad_capture"] >= AUTO_SEARCH_MIN_BAD_CAPTURE)
        & grouped["bad_rate"].notna()
    ].copy()
    eligible = eligible.sort_values(["score", "lift", "bad_cnt"], ascending=[False, False, False])

    pair_summary = pd.DataFrame(
        [
            {
                "feature_1": feature_1,
                "feature_2": feature_2,
                "cell_count": len(grouped),
                "eligible_cell_count": len(eligible),
                "best_rule_name": eligible.iloc[0]["rule_name"] if not eligible.empty else None,
                "best_feature_1_value": eligible.iloc[0]["feature_1_value"] if not eligible.empty else None,
                "best_feature_2_value": eligible.iloc[0]["feature_2_value"] if not eligible.empty else None,
                "best_hit_cnt": eligible.iloc[0]["hit_cnt"] if not eligible.empty else 0,
                "best_bad_cnt": eligible.iloc[0]["bad_cnt"] if not eligible.empty else 0,
                "best_hit_rate": eligible.iloc[0]["hit_rate"] if not eligible.empty else np.nan,
                "best_bad_rate": eligible.iloc[0]["bad_rate"] if not eligible.empty else np.nan,
                "best_lift": eligible.iloc[0]["lift"] if not eligible.empty else np.nan,
                "best_bad_capture": eligible.iloc[0]["bad_capture"] if not eligible.empty else np.nan,
                "best_score": eligible.iloc[0]["score"] if not eligible.empty else np.nan,
            }
        ]
    )
    return eligible, pair_summary


def generate_auto_search_heatmaps(
    feature_frame: pd.DataFrame,
    target: pd.Series,
    pair_summary: pd.DataFrame,
    output_dir: Path,
) -> None:
    for old_file in output_dir.glob("30_auto_pair_heatmap_*.png"):
        old_file.unlink()

    top_pairs = pair_summary.head(AUTO_SEARCH_HEATMAP_PAIR_COUNT)
    for position, (_, row) in enumerate(top_pairs.iterrows(), start=1):
        feature_1 = row["feature_1"]
        feature_2 = row["feature_2"]
        work = pd.DataFrame(
            {
                feature_1: feature_frame[feature_1].astype(str),
                feature_2: feature_frame[feature_2].astype(str),
                "target": target.values,
            }
        )
        heatmap_df = work.pivot_table(index=feature_1, columns=feature_2, values="target", aggfunc="mean")
        if heatmap_df.empty:
            continue
        file_name = output_dir / f"30_auto_pair_heatmap_{position:02d}.png"
        plot_heatmap(heatmap_df.fillna(0), file_name, f"{feature_1} x {feature_2} bad rate")


def search_best_cross_rules(
    df: pd.DataFrame,
    target_col: str,
    num_cols: list[str],
    obj_cols: list[str],
    iv_table: pd.DataFrame,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_frame, metadata = build_auto_search_feature_frame(df, target_col, num_cols, obj_cols, iv_table)
    metadata.to_csv(output_dir / "19_auto_cross_feature_metadata.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {
                "min_sample_count": AUTO_SEARCH_MIN_SAMPLE_COUNT,
                "min_hit_rate": AUTO_SEARCH_MIN_HIT_RATE,
                "max_hit_rate": AUTO_SEARCH_MAX_HIT_RATE,
                "min_lift": AUTO_SEARCH_MIN_LIFT,
                "min_bad_rate": AUTO_SEARCH_MIN_BAD_RATE,
                "min_bad_capture": AUTO_SEARCH_MIN_BAD_CAPTURE,
                "top_cells_per_pair": AUTO_SEARCH_TOP_CELLS_PER_PAIR,
                "top_pair_count": AUTO_SEARCH_TOP_PAIR_COUNT,
                "top_n_rules": AUTO_SEARCH_TOP_N_RULES,
            }
        ]
    ).to_csv(output_dir / "22_auto_cross_search_config.csv", index=False, encoding="utf-8-sig")

    feature_names = metadata["feature"].tolist()
    if len(feature_names) < 2:
        empty_summary = pd.DataFrame(
            columns=[
                "feature_1",
                "feature_2",
                "cell_count",
                "eligible_cell_count",
                "best_rule_name",
                "best_feature_1_value",
                "best_feature_2_value",
                "best_hit_cnt",
                "best_bad_cnt",
                "best_hit_rate",
                "best_bad_rate",
                "best_lift",
                "best_bad_capture",
                "best_score",
            ]
        )
        empty_rules = pd.DataFrame(
            columns=[
                "feature_1",
                "feature_2",
                "feature_1_value",
                "feature_2_value",
                "rule_name",
                "hit_cnt",
                "bad_cnt",
                "good_cnt",
                "hit_rate",
                "bad_rate",
                "overall_bad_rate",
                "bad_capture",
                "good_capture",
                "lift",
                "score",
            ]
        )
        empty_top_rules = empty_rules.copy()
        empty_summary.to_csv(output_dir / "20_auto_cross_pair_summary.csv", index=False, encoding="utf-8-sig")
        empty_rules.to_csv(output_dir / "21_auto_cross_rule_candidates.csv", index=False, encoding="utf-8-sig")
        empty_top_rules.to_csv(output_dir / "23_auto_cross_top_rules.csv", index=False, encoding="utf-8-sig")
        return metadata, empty_summary, empty_rules

    summary_rows = []
    candidate_frames = []

    for left_idx in range(len(feature_names) - 1):
        for right_idx in range(left_idx + 1, len(feature_names)):
            feature_1 = feature_names[left_idx]
            feature_2 = feature_names[right_idx]
            eligible, pair_summary = evaluate_pair_segments(feature_frame, df[target_col], feature_1, feature_2)
            summary_rows.append(pair_summary)
            if not eligible.empty:
                candidate_frames.append(eligible.head(AUTO_SEARCH_TOP_CELLS_PER_PAIR))

    pair_summary_df = (
        pd.concat(summary_rows, ignore_index=True)
        if summary_rows
        else pd.DataFrame()
    )
    if not pair_summary_df.empty:
        pair_summary_df = pair_summary_df.sort_values(
            ["best_score", "best_lift", "best_bad_cnt"], ascending=[False, False, False]
        ).head(AUTO_SEARCH_TOP_PAIR_COUNT)

    candidate_rules_df = (
        pd.concat(candidate_frames, ignore_index=True)
        if candidate_frames
        else pd.DataFrame()
    )
    if not candidate_rules_df.empty:
        candidate_rules_df = candidate_rules_df.sort_values(
            ["score", "lift", "bad_cnt"], ascending=[False, False, False]
        ).reset_index(drop=True)
    top_rules_df = candidate_rules_df.head(AUTO_SEARCH_TOP_N_RULES).copy() if not candidate_rules_df.empty else candidate_rules_df.copy()

    pair_summary_df.to_csv(output_dir / "20_auto_cross_pair_summary.csv", index=False, encoding="utf-8-sig")
    candidate_rules_df.to_csv(output_dir / "21_auto_cross_rule_candidates.csv", index=False, encoding="utf-8-sig")
    top_rules_df.to_csv(output_dir / "23_auto_cross_top_rules.csv", index=False, encoding="utf-8-sig")

    if not pair_summary_df.empty:
        generate_auto_search_heatmaps(feature_frame, df[target_col], pair_summary_df, output_dir)

    return metadata, pair_summary_df, candidate_rules_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rule crosstab analysis")
    parser.add_argument("--input", type=str, default=str(INPUT_FILE), help="Input CSV path")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help="Output directory")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> RuntimeConfig:
    return RuntimeConfig(
        input_file=Path(args.input),
        output_dir=Path(args.output),
    )


def run(runtime_config: RuntimeConfig) -> None:
    ensure_output_dir(runtime_config.output_dir)
    setup_plot_style()

    print(f"[1/8] Loading data: {runtime_config.input_file}")
    df_raw = load_data(runtime_config.input_file)
    save_basic_eda(df_raw, runtime_config.output_dir)

    print("[2/8] Preparing target")
    df = prepare_target(df_raw, TARGET_COL, TARGET_MAPPING)

    print("[3/8] Splitting feature types")
    num_cols, obj_cols = split_features(df, TARGET_COL, EXCLUDE_COLS)
    pd.DataFrame({"numeric_features": pd.Series(num_cols)}).to_csv(
        runtime_config.output_dir / "17_numeric_features.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame({"categorical_features": pd.Series(obj_cols)}).to_csv(
        runtime_config.output_dir / "18_categorical_features.csv", index=False, encoding="utf-8-sig"
    )

    print("[4/8] Exporting distributions and bad-rate charts")
    plot_target_distribution(df, TARGET_COL, runtime_config.output_dir)
    plot_categorical_badrate(
        df,
        obj_cols,
        TARGET_COL,
        runtime_config.output_dir,
        MAX_CATEGORY_UNIQUE_FOR_PLOT,
    )

    print("[5/8] Calculating numeric IV")
    iv_table, _ = calculate_numeric_iv(
        df, num_cols, TARGET_COL, runtime_config.output_dir, IV_BIN_COUNT
    )
    save_iv_selected(iv_table, IV_THRESHOLD, runtime_config.output_dir)

    print("[6/8] Building fixed cross tables")
    build_cross_tables(df, TARGET_COL, runtime_config.output_dir)

    print("[7/8] Evaluating configured rules")
    evaluate_rules(df, TARGET_COL, runtime_config.output_dir)

    print("[8/8] Searching best two-variable cross rules")
    search_best_cross_rules(
        df,
        TARGET_COL,
        num_cols,
        obj_cols,
        iv_table,
        runtime_config.output_dir,
    )

    print(f"Completed. Outputs written to: {runtime_config.output_dir.resolve()}")


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
    try:
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
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot write {excel_path}. Close summary_report.xlsx and rerun python run.py."
        ) from exc

    for csv_path in csv_files:
        csv_path.unlink()

    for extra_excel in output_dir.rglob("*.xlsx"):
        if extra_excel != excel_path:
            extra_excel.unlink()

    return excel_path
