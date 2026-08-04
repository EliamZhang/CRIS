"""
D类规则调优项目入口脚本。

运行方式：
    python run.py

输入：
    input/data_v3.xlsx

输出：
    output/ 下的指标表、分箱表、命中明细和图片。
"""
from __future__ import annotations

import argparse
import importlib
import math
import re
import sys
import warnings
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

warnings.filterwarnings("ignore")


@dataclass
class ProjectConfig:
    base_dir: Path = Path(__file__).resolve().parents[1]
    data_file: Path = Path(__file__).resolve().parents[1] / "input" / "data_v3.xlsx"
    output_dir: Path = Path(__file__).resolve().parents[1] / "output"
    sheet_name: int = 0
    target_col: str = "is_dlq_30d"
    id_col: str = "sample_id"
    month_col: str = "sample_month"
    score_col: str = "risk_score"
    binning_method: str = "scorecardpy"
    rule_set: list[dict] = field(
        default_factory=lambda: [
            {"name": "ovd_order_cnt_6m_grade", "threshold": 2, "operator": "gt", "comment": "recent overdue count is high"},
            {"name": "last_6m_avg_asset_total_grade", "threshold": 1, "operator": "lt", "comment": "recent asset grade is weak"},
            {"name": "adr_stability_grade", "threshold": 2, "operator": "lt", "comment": "address stability is weak"},
            {"name": "positive_biz_cnt_1y_grade", "threshold": 1, "operator": "lt", "comment": "positive business count is low"},
            {"name": "repayment_ability_rank", "threshold": 4, "operator": "gt", "comment": "repayment ability rank is poor"},
        ]
    )
    top_n_plot: int = 20
    csv_encoding: str = "utf-8-sig"
    grid_top_n: int = 30
    grid_min_hit_rate: float = 0.01
    grid_max_hit_rate: float = 0.50
    grid_min_lift: float = 1.05
    grid_min_bad_capture: float = 0.01

    @property
    def input_dir(self) -> Path:
        return self.data_file.parent

    @property
    def figure_dir(self) -> Path:
        return self.output_dir / "figures"

    @property
    def bin_dir(self) -> Path:
        return self.output_dir / "bins"

    @property
    def exclude_cols(self) -> list[str]:
        return [self.id_col, self.month_col, self.score_col]


DEFAULT_CONFIG = ProjectConfig()


def ensure_dirs(cfg: ProjectConfig) -> None:
    """创建输出目录。"""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.figure_dir.mkdir(parents=True, exist_ok=True)
    cfg.bin_dir.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    """将字段名转换为安全文件名。"""
    return re.sub(r"[^0-9a-zA-Z_\-\u4e00-\u9fa5]+", "_", str(name)).strip("_")


def load_data(cfg: ProjectConfig) -> pd.DataFrame:
    """读取输入 Excel。"""
    if not cfg.data_file.exists():
        raise FileNotFoundError(f"输入文件不存在：{cfg.data_file}")
    df = pd.read_excel(cfg.data_file, sheet_name=cfg.sheet_name)
    if cfg.target_col not in df.columns:
        raise ValueError(f"数据中找不到目标字段：{cfg.target_col}")
    return df


def get_feature_cols(df: pd.DataFrame, cfg: ProjectConfig) -> List[str]:
    """获取参与分箱和规则观察的变量列。"""
    exclude = set(cfg.exclude_cols + [cfg.target_col])
    return [c for c in df.columns if c not in exclude]


def calc_overall_bad_rate(df: pd.DataFrame, cfg: ProjectConfig) -> Tuple[pd.DataFrame, float]:
    """筛选有表现标签的通过样本，并计算整体坏账率。"""
    df_tg = df.loc[df[cfg.target_col].notna()].reset_index(drop=True).copy()
    if df_tg.empty:
        raise ValueError(f"{cfg.target_col} 全为空，无法计算坏账率。")
    df_tg[cfg.target_col] = df_tg[cfg.target_col].astype(int)
    overall_bad_rate = float(df_tg[cfg.target_col].mean())
    if overall_bad_rate <= 0:
        raise ValueError("整体坏账率为 0，无法计算 lift。")
    return df_tg, overall_bad_rate


def _grade_binning_one(df_tg: pd.DataFrame, feature: str, target_col: str, overall_bad_rate: float) -> pd.DataFrame:
    """兜底分箱：按字段取值/等级直接聚合，适合本项目中的 grade/rank 类规则变量。"""
    tmp = df_tg[[feature, target_col]].copy()
    tmp["bin"] = tmp[feature].where(tmp[feature].notna(), "Missing")

    grouped = (
        tmp.groupby("bin", dropna=False)[target_col]
        .agg(total="count", bad="sum")
        .reset_index()
    )
    grouped["good"] = grouped["total"] - grouped["bad"]
    grouped["count_distr"] = grouped["total"] / grouped["total"].sum()
    grouped["badprob"] = grouped["bad"] / grouped["total"]
    grouped["lift"] = grouped["badprob"] / overall_bad_rate
    grouped.insert(0, "variable", feature)

    # 尽量按数值顺序展示；非数值 bin 放最后。
    def _sort_key(v):
        try:
            return (0, float(v))
        except Exception:
            return (1, str(v))

    grouped = grouped.sort_values("bin", key=lambda s: s.map(_sort_key)).reset_index(drop=True)
    return grouped[["variable", "bin", "total", "good", "bad", "count_distr", "badprob", "lift"]]


def _scorecardpy_binning(
    df_tg: pd.DataFrame,
    features: Iterable[str],
    target_col: str,
    overall_bad_rate: float,
) -> Dict[str, pd.DataFrame]:
    """优先使用 notebook 原始的 scorecardpy.woebin 逻辑。"""
    sc = importlib.import_module("scorecardpy")
    model_cols = list(features) + [target_col]
    bins_info = sc.woebin(
        df_tg[model_cols],
        y=target_col,
        breaks_list={},
        method="tree",
        stop_limit=0,
    )

    result = {}
    for feature, bin_df in bins_info.items():
        out = bin_df.copy()
        if "badprob" in out.columns:
            out["lift"] = out["badprob"] / overall_bad_rate
        result[feature] = out
    return result


def calculate_binning_lift(
    df_tg: pd.DataFrame,
    overall_bad_rate: float,
    cfg: ProjectConfig,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], str]:
    """计算每个变量的分箱 badrate 和 lift。"""
    features = get_feature_cols(df_tg, cfg)
    method_used = "grade"

    if cfg.binning_method == "scorecardpy":
        try:
            bins_info = _scorecardpy_binning(df_tg, features, cfg.target_col, overall_bad_rate)
            method_used = "scorecardpy"
        except Exception as exc:
            print(f"[WARN] scorecardpy 分箱不可用，自动降级为 grade 等值分箱。原因：{exc}")
            bins_info = {
                feature: _grade_binning_one(df_tg, feature, cfg.target_col, overall_bad_rate)
                for feature in features
            }
    else:
        bins_info = {
            feature: _grade_binning_one(df_tg, feature, cfg.target_col, overall_bad_rate)
            for feature in features
        }

    lift_rows = []
    for feature, bin_df in bins_info.items():
        if feature == cfg.target_col or "lift" not in bin_df.columns:
            continue
        lift_rows.append({
            "variable": feature,
            "max_lift": float(bin_df["lift"].max()),
            "max_badprob": float(bin_df.loc[bin_df["lift"].idxmax(), "badprob"]) if "badprob" in bin_df.columns else np.nan,
            "max_lift_bin": str(bin_df.loc[bin_df["lift"].idxmax(), "bin"]) if "bin" in bin_df.columns else "",
        })

    rule_lift = pd.DataFrame(lift_rows).sort_values("max_lift", ascending=False).reset_index(drop=True)
    return rule_lift, bins_info, method_used


def apply_rules(df: pd.DataFrame, rules: List[dict]) -> Tuple[float, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """执行规则命中计算，输出综合命中率、命中数量分布、单一/自然命中率。"""
    data = df.copy()
    hit_cols = []

    for rule in rules:
        name = rule["name"]
        threshold = rule["threshold"]
        operator = rule["operator"]
        if name not in data.columns:
            raise ValueError(f"规则字段不存在：{name}")

        hit_col = f"{name}_hit"
        hit_cols.append(hit_col)
        if operator == "lt":
            data[hit_col] = (data[name] < threshold).astype(int)
        elif operator == "gt":
            data[hit_col] = (data[name] > threshold).astype(int)
        else:
            raise ValueError(f"不支持的 operator：{operator}，仅支持 gt / lt")

    data["hit_any"] = data[hit_cols].any(axis=1)
    data["hit_sum"] = data[hit_cols].sum(axis=1)
    overall_hit_rate = float(data["hit_any"].mean())

    hit_dist = (
        data["hit_sum"]
        .value_counts(dropna=False)
        .rename_axis("hit_sum")
        .reset_index(name="sample_cnt")
        .sort_values("hit_sum")
    )
    hit_dist["sample_pct"] = hit_dist["sample_cnt"] / len(data)

    pure_rows = []
    for col in hit_cols:
        hit_cnt = int((data[col] == 1).sum())
        pure_hit_cnt = int(((data[col] == 1) & (data["hit_sum"] == 1)).sum())
        hit_rate = hit_cnt / len(data) if len(data) else 0
        pure_hit_rate = pure_hit_cnt / len(data) if len(data) else 0
        pure_hit_pct = pure_hit_cnt / hit_cnt if hit_cnt else 0
        pure_rows.append({
            "rule": col.replace("_hit", ""),
            "pure_hit_cnt": pure_hit_cnt,
            "hit_cnt": hit_cnt,
            "pure_hit_rate": pure_hit_rate,
            "hit_rate": hit_rate,
            "pure_hit_pct_in_rule_hits": pure_hit_pct,
        })

    pure_hit_df = pd.DataFrame(pure_rows).sort_values(
        ["pure_hit_rate", "pure_hit_pct_in_rule_hits"], ascending=[False, False]
    ).reset_index(drop=True)

    return overall_hit_rate, data, hit_dist, pure_hit_df


def evaluate_tuning(
    df: pd.DataFrame,
    df_tg: pd.DataFrame,
    ruled_df: pd.DataFrame,
    before_bad_rate: float,
    cfg: ProjectConfig,
) -> pd.DataFrame:
    """评估调整前后坏账率和通过率变化。"""
    after_pass_df = ruled_df.loc[ruled_df["hit_sum"] == 0].copy()
    after_bad_rate = float(after_pass_df[cfg.target_col].mean())

    passing_rate_before = len(df_tg) / len(df)
    passing_rate_after = len(after_pass_df) / len(df)

    result = pd.DataFrame([
        {"metric": "bad_rate_before", "value": before_bad_rate, "value_pct": before_bad_rate * 100},
        {"metric": "bad_rate_after", "value": after_bad_rate, "value_pct": after_bad_rate * 100},
        {"metric": "bad_rate_drop_pct", "value": (before_bad_rate - after_bad_rate) / before_bad_rate, "value_pct": (before_bad_rate - after_bad_rate) * 100 / before_bad_rate},
        {"metric": "passing_rate_before", "value": passing_rate_before, "value_pct": passing_rate_before * 100},
        {"metric": "passing_rate_after", "value": passing_rate_after, "value_pct": passing_rate_after * 100},
        {"metric": "passing_rate_drop_pct", "value": (passing_rate_before - passing_rate_after) / passing_rate_before, "value_pct": (passing_rate_before - passing_rate_after) * 100 / passing_rate_before},
    ])
    return result


def build_threshold_candidates(series: pd.Series) -> List[float]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return []
    unique_values = sorted(float(v) for v in numeric.unique().tolist())
    if len(unique_values) <= 12:
        return unique_values
    quantiles = sorted(
        {
            float(v)
            for v in numeric.quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]).tolist()
            if not pd.isna(v)
        }
    )
    return quantiles or unique_values[:12]


def evaluate_grid_rule(
    df_tg: pd.DataFrame,
    feature: str,
    operator: str,
    threshold: float,
    target_col: str,
    overall_bad_rate: float,
) -> Dict[str, object]:
    if operator == "lt":
        mask = df_tg[feature] < threshold
        rule_name = f"{feature} < {threshold}"
    else:
        mask = df_tg[feature] > threshold
        rule_name = f"{feature} > {threshold}"

    hit_df = df_tg.loc[mask].copy()
    total_bad = float(df_tg[target_col].sum())
    hit_cnt = int(mask.sum())
    bad_cnt = int(hit_df[target_col].sum()) if hit_cnt else 0
    bad_rate = float(hit_df[target_col].mean()) if hit_cnt else np.nan
    hit_rate = hit_cnt / len(df_tg) if len(df_tg) else np.nan
    bad_capture = bad_cnt / total_bad if total_bad else np.nan
    lift = bad_rate / overall_bad_rate if overall_bad_rate > 0 and not np.isnan(bad_rate) else np.nan
    score = (
        (0 if np.isnan(lift) else max(lift - 1.0, 0.0))
        * math.sqrt(max(hit_rate, 0.0))
        * max(bad_capture, 0.0)
    )
    return {
        "feature": feature,
        "operator": operator,
        "threshold": threshold,
        "rule_name": rule_name,
        "hit_cnt": hit_cnt,
        "bad_cnt": bad_cnt,
        "hit_rate": hit_rate,
        "bad_rate": bad_rate,
        "lift": lift,
        "bad_capture": bad_capture,
        "grid_score": score,
    }


def run_grid_search(df_tg: pd.DataFrame, overall_bad_rate: float, cfg: ProjectConfig) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for rule in cfg.rule_set:
        feature = rule["name"]
        if feature not in df_tg.columns:
            continue
        operator = rule["operator"]
        for threshold in build_threshold_candidates(df_tg[feature]):
            rows.append(
                evaluate_grid_rule(
                    df_tg=df_tg,
                    feature=feature,
                    operator=operator,
                    threshold=threshold,
                    target_col=cfg.target_col,
                    overall_bad_rate=overall_bad_rate,
                )
            )

    result = pd.DataFrame(rows)
    if result.empty:
        return result

    result = result.sort_values(
        ["grid_score", "lift", "bad_capture"], ascending=[False, False, False]
    ).reset_index(drop=True)
    result.to_csv(cfg.output_dir / "07_grid_search_rule_candidates.csv", index=False, encoding=cfg.csv_encoding)
    filtered = result[
        (result["hit_rate"] >= cfg.grid_min_hit_rate)
        & (result["hit_rate"] <= cfg.grid_max_hit_rate)
        & (result["lift"] >= cfg.grid_min_lift)
        & (result["bad_capture"] >= cfg.grid_min_bad_capture)
    ].copy()
    filtered.head(cfg.grid_top_n).to_csv(
        cfg.output_dir / "08_grid_search_top_rules.csv", index=False, encoding=cfg.csv_encoding
    )
    return filtered


def save_outputs(
    df: pd.DataFrame,
    df_tg: pd.DataFrame,
    rule_lift: pd.DataFrame,
    bins_info: Dict[str, pd.DataFrame],
    ruled_df: pd.DataFrame,
    hit_dist: pd.DataFrame,
    pure_hit_df: pd.DataFrame,
    effect_df: pd.DataFrame,
    overall_bad_rate: float,
    overall_hit_rate: float,
    method_used: str,
    cfg: ProjectConfig,
) -> None:
    """保存所有输出表和图片。"""
    encoding = cfg.csv_encoding

    summary = pd.DataFrame([
        {"metric": "total_sample_cnt", "value": len(df)},
        {"metric": "observed_pass_sample_cnt", "value": len(df_tg)},
        {"metric": "observed_pass_sample_pct", "value": len(df_tg) / len(df)},
        {"metric": "overall_bad_rate", "value": overall_bad_rate},
        {"metric": "overall_rule_hit_rate_after_tuning", "value": overall_hit_rate},
        {"metric": "binning_method_used", "value": method_used},
    ])

    summary.to_csv(cfg.output_dir / "01_overall_summary.csv", index=False, encoding=encoding)
    rule_lift.to_csv(cfg.output_dir / "02_rule_lift_summary.csv", index=False, encoding=encoding)
    hit_dist.to_csv(cfg.output_dir / "03_rule_hit_sum_distribution.csv", index=False, encoding=encoding)
    pure_hit_df.to_csv(cfg.output_dir / "04_rule_pure_hit_summary.csv", index=False, encoding=encoding)
    effect_df.to_csv(cfg.output_dir / "05_tuning_effect_summary.csv", index=False, encoding=encoding)
    ruled_df.to_csv(cfg.output_dir / "06_rule_hit_sample_detail.csv", index=False, encoding=encoding)

    for feature, bin_df in bins_info.items():
        bin_df.to_csv(cfg.bin_dir / f"{safe_filename(feature)}_bins.csv", index=False, encoding=encoding)

    # 图片1：变量最大 lift 排名
    if not rule_lift.empty:
        plot_df = rule_lift.head(cfg.top_n_plot).sort_values("max_lift", ascending=True)
        plt.figure(figsize=(9, max(4, len(plot_df) * 0.45)))
        plt.barh(plot_df["variable"], plot_df["max_lift"])
        plt.xlabel("Max Lift")
        plt.ylabel("Variable")
        plt.title("Top Variables by Max Lift")
        plt.tight_layout()
        plt.savefig(cfg.figure_dir / "top_variable_lift.png", dpi=180)
        plt.close()

    # 图片2：命中数量分布
    plt.figure(figsize=(7, 4))
    plt.bar(hit_dist["hit_sum"].astype(str), hit_dist["sample_pct"])
    plt.xlabel("Rule Hit Count")
    plt.ylabel("Sample Percent")
    plt.title("Rule Hit Count Distribution")
    plt.tight_layout()
    plt.savefig(cfg.figure_dir / "rule_hit_count_distribution.png", dpi=180)
    plt.close()

    # 图片3：调优前后对比
    effect_map = effect_df.set_index("metric")["value_pct"].to_dict()
    compare_df = pd.DataFrame({
        "metric": ["Bad Rate", "Passing Rate"],
        "before": [effect_map.get("bad_rate_before", np.nan), effect_map.get("passing_rate_before", np.nan)],
        "after": [effect_map.get("bad_rate_after", np.nan), effect_map.get("passing_rate_after", np.nan)],
    })
    x = np.arange(len(compare_df))
    width = 0.35
    plt.figure(figsize=(7, 4))
    plt.bar(x - width / 2, compare_df["before"], width, label="Before")
    plt.bar(x + width / 2, compare_df["after"], width, label="After")
    plt.xticks(x, compare_df["metric"])
    plt.ylabel("Percent (%)")
    plt.title("Before vs After Tuning")
    plt.legend()
    plt.tight_layout()
    plt.savefig(cfg.figure_dir / "before_after_tuning_effect.png", dpi=180)
    plt.close()


def print_console_summary(
    effect_df: pd.DataFrame,
    rule_lift: pd.DataFrame,
    overall_hit_rate: float,
    method_used: str,
    cfg: ProjectConfig,
) -> None:
    """打印简要运行结果。"""
    effect = effect_df.set_index("metric")["value_pct"].to_dict()
    print("\n========== 运行完成 ==========")
    print(f"分箱方法: {method_used}")
    print(f"综合命中率: {overall_hit_rate * 100:.4f}%")
    print(f"调整前样本坏浓度: {effect.get('bad_rate_before', math.nan):.4f}%")
    print(f"调整后样本坏浓度: {effect.get('bad_rate_after', math.nan):.4f}%")
    print(f"样本坏浓度下降幅度: {effect.get('bad_rate_drop_pct', math.nan):.4f}%")
    print(f"调整前通过率: {effect.get('passing_rate_before', math.nan):.4f}%")
    print(f"调整后通过率: {effect.get('passing_rate_after', math.nan):.4f}%")
    print(f"通过率下降幅度: {effect.get('passing_rate_drop_pct', math.nan):.4f}%")
    if not rule_lift.empty:
        print("\nTop lift 变量：")
        print(rule_lift.head(10).to_string(index=False))
    print(f"\n输出目录: {cfg.output_dir}")


@dataclass
class RuntimeConfig:
    data_file: Path
    output_dir: Path


def build_project_config(runtime_config: RuntimeConfig) -> ProjectConfig:
    return ProjectConfig(
        base_dir=DEFAULT_CONFIG.base_dir,
        data_file=runtime_config.data_file,
        output_dir=runtime_config.output_dir,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="D ?????")
    parser.add_argument("--input", "--data-file", dest="data_file", type=Path, default=DEFAULT_CONFIG.data_file, help="?? Excel ??")
    parser.add_argument("--output", type=Path, default=DEFAULT_CONFIG.output_dir, help="????")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> RuntimeConfig:
    return RuntimeConfig(data_file=Path(args.data_file), output_dir=Path(args.output))


def run(runtime_config: RuntimeConfig) -> None:
    cfg = build_project_config(runtime_config)

    ensure_dirs(cfg)
    df = load_data(cfg)
    df_tg, overall_bad_rate = calc_overall_bad_rate(df, cfg)
    rule_lift, bins_info, method_used = calculate_binning_lift(df_tg, overall_bad_rate, cfg)
    overall_hit_rate, ruled_df, hit_dist, pure_hit_df = apply_rules(df, cfg.rule_set)
    effect_df = evaluate_tuning(df, df_tg, ruled_df, overall_bad_rate, cfg)
    grid_df = run_grid_search(df_tg, overall_bad_rate, cfg)

    save_outputs(
        df=df,
        df_tg=df_tg,
        rule_lift=rule_lift,
        bins_info=bins_info,
        ruled_df=ruled_df,
        hit_dist=hit_dist,
        pure_hit_df=pure_hit_df,
        effect_df=effect_df,
        overall_bad_rate=overall_bad_rate,
        overall_hit_rate=overall_hit_rate,
        method_used=method_used,
        cfg=cfg,
    )
    print_console_summary(effect_df, rule_lift, overall_hit_rate, method_used, cfg)
    if not grid_df.empty:
        print("\nTop grid-search rule candidates:")
        print(grid_df.head(10).to_string(index=False))


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
