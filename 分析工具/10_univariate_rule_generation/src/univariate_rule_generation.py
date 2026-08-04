"""风控规则生成：变量初筛、IV/WOE 分箱、阈值规则挖掘与评估。"""
from __future__ import annotations

import argparse
import math
import re
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_COLS = 16_384

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class RuleGenerationConfig:
    input_path: Path = PROJECT_ROOT / "input" / "data_rule.csv"
    output_dir: Path = PROJECT_ROOT / "output"
    target_col: str = "target"
    exclude_cols: Optional[List[str]] = None    
    feature_cols: Optional[List[str]] = None
    missing_values: Sequence[float] = field(default_factory=lambda: [-999])
    discrete_unique_threshold: int = 20
    max_bins: int = 5
    min_bin_pct: float = 0.05
    binning_method: str = "tree"
    smoothing: float = 0.5
    quantile_list: Sequence[float] = field(default_factory=lambda: [0.005, 0.01, 0.02, 0.05, 0.95, 0.98, 0.99, 0.995])
    lift_cutoff: float = 1.5
    hit_rate_down_cutoff: float = 0.01
    hit_rate_up_cutoff: float = 0.06
    bad_capture_down_cutoff: float = 0.0
    save_figures: bool = True
    figure_dpi: int = 160


def ensure_dirs(output_dir: Path) -> Dict[str, Path]:
    """创建输出目录。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    return {"output": output_dir, "figures": figure_dir}


def clean_filename(name: str) -> str:
    """将变量名转成安全文件名。"""
    safe = re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fa5-]+", "_", str(name))
    return safe[:120]


def build_sheet_name(name: str) -> str:
    safe = re.sub(r"[:\\/?*\[\]]+", "_", str(name)).strip()
    return (safe or "sheet")[:31]


def write_summary_report(output_dir: Path, sheets: Dict[str, pd.DataFrame]) -> Path:
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


def load_data(config: RuleGenerationConfig) -> pd.DataFrame:
    """读取输入数据，并校验 target 字段。"""
    df = pd.read_csv(config.input_path)
    if config.target_col not in df.columns:
        raise ValueError(f"找不到目标字段 {config.target_col!r}，请检查 config.target_col。")

    unique_y = sorted(df[config.target_col].dropna().unique().tolist())
    if set(unique_y) - {0, 1}:
        raise ValueError(f"目标字段必须是 0/1 二分类，目前取值为：{unique_y}")
    return df


def get_feature_cols(df: pd.DataFrame, config: RuleGenerationConfig) -> List[str]:
    """获取待分析变量列表，支持排除基础字段。"""
    exclude_cols = set(config.exclude_cols or [])
    exclude_cols.add(config.target_col)

    if config.feature_cols:
        missing = [c for c in config.feature_cols if c not in df.columns]
        if missing:
            raise ValueError(f"feature_cols 中这些字段不存在：{missing}")

        return [c for c in config.feature_cols if c not in exclude_cols]

    return [c for c in df.columns if c not in exclude_cols]


def normalize_missing(df: pd.DataFrame, feature_cols: Sequence[str], missing_values: Sequence[float]) -> pd.DataFrame:
    """将配置中的特殊缺失值替换为 NaN，仅处理特征字段。"""
    out = df.copy()
    if missing_values:
        out.loc[:, feature_cols] = out.loc[:, feature_cols].replace(list(missing_values), np.nan)
    return out


def variable_statistics(raw_df: pd.DataFrame, feature_cols: Sequence[str], config: RuleGenerationConfig) -> pd.DataFrame:
    """变量初筛统计：唯一值、空值率、特殊缺失率、众数占比、字段类型。"""
    rows = []
    n = len(raw_df)
    for col in feature_cols:
        s = raw_df[col]
        mode_share = s.value_counts(normalize=True, dropna=False).iloc[0] if n else np.nan
        special_missing_rate = s.isin(list(config.missing_values)).mean() if config.missing_values else 0.0
        rows.append(
            {
                "feature": col,
                "unique_values": s.nunique(dropna=True),
                "null_rate": s.isna().mean(),
                "special_missing_rate": special_missing_rate,
                "mode_share": mode_share,
                "dtype": str(s.dtype),
            }
        )
    res = pd.DataFrame(rows).sort_values(["unique_values", "feature"], ascending=[False, True])
    return res


def infer_feature_type(s: pd.Series, discrete_unique_threshold: int) -> str:
    """识别变量类型：continuous / discrete。"""
    non_missing = s.dropna()
    if not pd.api.types.is_numeric_dtype(non_missing):
        return "discrete"
    if non_missing.nunique() <= discrete_unique_threshold:
        return "discrete"
    return "continuous"


def tree_thresholds(x: pd.Series, y: pd.Series, max_bins: int, min_bin_pct: float) -> Optional[List[float]]:
    """使用决策树获取连续变量分箱切点；失败时返回 None。"""
    try:
        from sklearn.tree import DecisionTreeClassifier
    except Exception:
        return None

    valid = x.notna() & y.notna()
    x_valid = x[valid].astype(float)
    y_valid = y[valid].astype(int)
    if x_valid.nunique() <= 1 or y_valid.nunique() <= 1:
        return None

    min_leaf = max(int(math.ceil(len(x_valid) * min_bin_pct)), 1)
    clf = DecisionTreeClassifier(
        criterion="entropy",
        max_leaf_nodes=max_bins,
        min_samples_leaf=min_leaf,
        random_state=42,
    )
    clf.fit(x_valid.to_numpy().reshape(-1, 1), y_valid)
    thresholds = clf.tree_.threshold
    thresholds = sorted(float(t) for t in thresholds if t != -2)
    if not thresholds:
        return None
    return thresholds


def quantile_thresholds(x: pd.Series, max_bins: int) -> List[float]:
    """使用分位数获取连续变量分箱切点。"""
    x_valid = x.dropna().astype(float)
    if x_valid.nunique() <= 1:
        return []
    probs = np.linspace(0, 1, max_bins + 1)[1:-1]
    thresholds = sorted(set(float(x_valid.quantile(p)) for p in probs))
    return thresholds


def make_binned_series(
    df: pd.DataFrame,
    feature: str,
    target: str,
    config: RuleGenerationConfig,
) -> Tuple[pd.Series, str, List[float]]:
    """对单变量做分箱。"""
    s = df[feature]
    ftype = infer_feature_type(s, config.discrete_unique_threshold)

    if ftype == "continuous":
        thresholds = None
        if config.binning_method == "tree":
            thresholds = tree_thresholds(s, df[target], config.max_bins, config.min_bin_pct)
        if not thresholds:
            thresholds = quantile_thresholds(s, config.max_bins)

        if thresholds:
            edges = [-np.inf] + thresholds + [np.inf]
            labels = []
            for left, right in zip(edges[:-1], edges[1:]):
                left_s = "-inf" if left == -np.inf else f"{left:.6g}"
                right_s = "inf" if right == np.inf else f"{right:.6g}"
                labels.append(f"[{left_s}, {right_s})")
            binned = pd.cut(s.astype(float), bins=edges, labels=labels, include_lowest=True, right=False)
            return binned.astype("object").where(s.notna(), "MISSING"), ftype, thresholds

    # 离散变量或连续变量无法分箱时：按原值分组
    binned = s.astype("object").where(s.notna(), "MISSING").astype(str)
    return binned, ftype, []


def calc_woe_iv_from_bins(
    df: pd.DataFrame,
    feature: str,
    target: str,
    bin_col: pd.Series,
    ftype: str,
    thresholds: Sequence[float],
    smoothing: float,
) -> pd.DataFrame:
    """计算单变量分箱明细、WOE、IV。"""
    temp = pd.DataFrame({"bin": bin_col.astype(str), target: df[target].astype(int)})
    grouped = temp.groupby("bin", dropna=False)[target].agg(["count", "sum"]).reset_index()
    grouped.rename(columns={"sum": "bad"}, inplace=True)
    grouped["good"] = grouped["count"] - grouped["bad"]

    total = grouped["count"].sum()
    total_bad = grouped["bad"].sum()
    total_good = grouped["good"].sum()
    k = grouped.shape[0]

    grouped["count_distr"] = grouped["count"] / total
    grouped["badprob"] = grouped["bad"] / grouped["count"]
    grouped["bad_distr"] = (grouped["bad"] + smoothing) / (total_bad + smoothing * k)
    grouped["good_distr"] = (grouped["good"] + smoothing) / (total_good + smoothing * k)
    grouped["woe"] = np.log(grouped["bad_distr"] / grouped["good_distr"])
    grouped["bin_iv"] = (grouped["bad_distr"] - grouped["good_distr"]) * grouped["woe"]
    grouped["variable"] = feature
    grouped["feature_type"] = ftype
    grouped["thresholds"] = ",".join(f"{x:.8g}" for x in thresholds)

    cols = [
        "variable", "feature_type", "thresholds", "bin", "count", "good", "bad",
        "count_distr", "good_distr", "bad_distr", "badprob", "woe", "bin_iv",
    ]
    return grouped[cols]


def plot_bin_result(bin_df: pd.DataFrame, feature: str, figure_dir: Path, dpi: int) -> None:
    """保存单变量分箱坏率图。"""
    if bin_df.empty:
        return
    plot_df = bin_df.copy()
    plot_df["bin"] = plot_df["bin"].astype(str)
    plt.figure(figsize=(max(7, min(14, len(plot_df) * 1.2)), 4.5))
    plt.bar(plot_df["bin"], plot_df["badprob"])
    plt.title(f"{feature} - bin bad rate")
    plt.xlabel("bin")
    plt.ylabel("bad rate")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(figure_dir / f"{clean_filename(feature)}_bad_rate.png", dpi=dpi)
    plt.close()


def run_iv_analysis(df: pd.DataFrame, feature_cols: Sequence[str], config: RuleGenerationConfig, figure_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """执行所有变量的 IV/WOE 分析。"""
    all_bins = []
    for feature in feature_cols:
        binned, ftype, thresholds = make_binned_series(df, feature, config.target_col, config)
        bin_df = calc_woe_iv_from_bins(df, feature, config.target_col, binned, ftype, thresholds, config.smoothing)
        all_bins.append(bin_df)
        if config.save_figures:
            plot_bin_result(bin_df, feature, figure_dir, config.figure_dpi)

    bins_detail = pd.concat(all_bins, axis=0, ignore_index=True) if all_bins else pd.DataFrame()
    iv_summary = (
        bins_detail.groupby(["variable", "feature_type", "thresholds"], dropna=False)["bin_iv"]
        .sum()
        .reset_index()
        .rename(columns={"bin_iv": "iv"})
        .sort_values("iv", ascending=False)
    )
    return iv_summary, bins_detail


def rule_evaluate(selected: pd.DataFrame, total: pd.DataFrame, target: str) -> Dict[str, float]:
    """规则命中样本效果评估。"""
    total_size = len(total)
    total_bad = float(total[target].sum())
    total_good = float(total_size - total_bad)
    total_bad_rate = total_bad / total_size if total_size else np.nan

    hit_size = len(selected)
    hit_bad = float(selected[target].sum())
    hit_good = float(hit_size - hit_bad)
    hit_bad_rate = hit_bad / hit_size if hit_size else np.nan
    hit_rate = hit_size / total_size if total_size else np.nan
    bad_capture = hit_bad / total_bad if total_bad else np.nan
    good_capture = hit_good / total_good if total_good else np.nan
    lift = hit_bad_rate / total_bad_rate if total_bad_rate else np.nan

    precision = hit_bad_rate
    recall = bad_capture
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else np.nan

    return {
        "total_size": total_size,
        "total_bad": total_bad,
        "total_bad_rate": total_bad_rate,
        "hit_rate": hit_rate,
        "hit_size": hit_size,
        "hit_bad": hit_bad,
        "hit_bad_rate": hit_bad_rate,
        "bad_capture": bad_capture,
        "good_capture": good_capture,
        "lift": lift,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def discover_rules_for_feature(df: pd.DataFrame, feature: str, target: str, config: RuleGenerationConfig) -> pd.DataFrame:
    """对单变量生成候选规则。"""
    s = df[feature]
    rows = []

    miss_mask = s.isna()
    if miss_mask.any():
        metrics = rule_evaluate(df[miss_mask], df, target)
        rows.append({"variable": feature, "rule": "is missing", "threshold": np.nan, "direction": "missing", **metrics})

    valid = df[s.notna()].copy()
    if valid.empty:
        return pd.DataFrame(rows)

    if pd.api.types.is_numeric_dtype(valid[feature]):
        x = valid[feature].astype(float)
        for q in config.quantile_list:
            threshold = float(x.quantile(q))
            if q < 0.5:
                mask = s.notna() & (s.astype(float) <= threshold)
                rule = f"{feature} <= {threshold:.8g}"
                direction = "lower_tail"
            else:
                mask = s.notna() & (s.astype(float) >= threshold)
                rule = f"{feature} >= {threshold:.8g}"
                direction = "upper_tail"
            metrics = rule_evaluate(df[mask], df, target)
            rows.append({"variable": feature, "rule": rule, "threshold": threshold, "quantile": q, "direction": direction, **metrics})

    # 离散变量补充单值命中规则，避免变量是类别编码时只看分位点不直观
    if s.nunique(dropna=True) <= config.discrete_unique_threshold:
        for value in sorted(s.dropna().unique().tolist()):
            mask = s == value
            rule = f"{feature} == {value}"
            metrics = rule_evaluate(df[mask], df, target)
            rows.append({"variable": feature, "rule": rule, "threshold": value, "direction": "single_value", **metrics})

    return pd.DataFrame(rows)


def run_rule_discovery(df: pd.DataFrame, feature_cols: Sequence[str], config: RuleGenerationConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """执行规则挖掘和规则筛选。"""
    candidates = []
    for feature in feature_cols:
        candidates.append(discover_rules_for_feature(df, feature, config.target_col, config))
    all_rules = pd.concat(candidates, axis=0, ignore_index=True) if candidates else pd.DataFrame()

    selected = all_rules[
        (all_rules["lift"] >= config.lift_cutoff)
        & (all_rules["hit_rate"] >= config.hit_rate_down_cutoff)
        & (all_rules["hit_rate"] <= config.hit_rate_up_cutoff)
        & (all_rules["bad_capture"] >= config.bad_capture_down_cutoff)
    ].copy()
    selected = selected.sort_values(["lift", "hit_bad_rate", "bad_capture"], ascending=False)
    return all_rules, selected


def save_report(
    output_dir: Path,
    config: RuleGenerationConfig,
    df: pd.DataFrame,
    stats_df: pd.DataFrame,
    iv_summary: pd.DataFrame,
    selected_rules: pd.DataFrame,
) -> None:
    """保存 Markdown 运行报告。"""
    top_iv = iv_summary.head(10)[["variable", "iv", "feature_type"]].to_markdown(index=False) if not iv_summary.empty else "无"
    top_rules = (
        selected_rules.head(10)[["variable", "rule", "hit_rate", "hit_bad_rate", "bad_capture", "lift", "f1"]].to_markdown(index=False)
        if not selected_rules.empty
        else "无符合筛选条件的规则"
    )

    text = f"""# 规则生成运行报告

## 一、样本概况

- 输入文件：`{config.input_path}`
- 样本量：{df.shape[0]:,}
- 字段数：{df.shape[1]:,}
- 目标字段：`{config.target_col}`
- 整体坏账率：{df[config.target_col].mean():.6%}

## 二、配置摘要

```text
{asdict(config)}
```

## 三、Top IV 变量

{top_iv}

## 四、Top 规则候选

{top_rules}

## 五、输出文件

- `01_variable_statistics.csv`：变量初筛统计
- `02_iv_summary.csv`：变量 IV 汇总
- `03_bins_detail.csv`：变量分箱明细、WOE、bin IV
- `04_rule_candidates_all.csv`：所有候选规则
- `05_rule_candidates_selected.csv`：按配置阈值筛选后的规则
- `figures/`：每个变量的分箱坏账率图片
"""
    (output_dir / "run_report.md").write_text(text, encoding="utf-8")


def run(config: RuleGenerationConfig) -> None:
    """主流程。"""
    dirs = ensure_dirs(config.output_dir)
    raw_df = load_data(config)
    feature_cols = get_feature_cols(raw_df, config)
    df = normalize_missing(raw_df, feature_cols, config.missing_values)
    stats_df = variable_statistics(raw_df, feature_cols, config)
    stats_df.to_csv(dirs["output"] / "01_variable_statistics.csv", index=False, encoding="utf-8-sig")

    iv_summary, bins_detail = run_iv_analysis(df, feature_cols, config, dirs["figures"])
    iv_summary.to_csv(dirs["output"] / "02_iv_summary.csv", index=False, encoding="utf-8-sig")
    bins_detail.to_csv(dirs["output"] / "03_bins_detail.csv", index=False, encoding="utf-8-sig")

    all_rules, selected_rules = run_rule_discovery(df, feature_cols, config)
    all_rules.to_csv(dirs["output"] / "04_rule_candidates_all.csv", index=False, encoding="utf-8-sig")
    selected_rules.to_csv(dirs["output"] / "05_rule_candidates_selected.csv", index=False, encoding="utf-8-sig")

    save_report(dirs["output"], config, df, stats_df, iv_summary, selected_rules)

    print("运行完成，输出目录：", dirs["output"])
    print("Top IV:")
    print(iv_summary.head(10).to_string(index=False))
    print("\nTop selected rules:")
    if selected_rules.empty:
        print("无符合筛选条件的规则。")
    else:
        print(selected_rules.head(10).to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="风控单变量规则生成项目")
    parser.add_argument("--input", type=str, default=None, help="输入 CSV 路径，默认 input/data_rule.csv")
    parser.add_argument("--output", type=str, default=None, help="输出目录，默认 output/")
    parser.add_argument("--target", type=str, default=None, help="目标字段，默认 target")
    parser.add_argument("--lift", type=float, default=None, help="规则筛选 lift 阈值")
    parser.add_argument("--hit-rate-min", type=float, default=None, help="规则最小命中率")
    parser.add_argument("--hit-rate-max", type=float, default=None, help="规则最大命中率")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> RuleGenerationConfig:
    cfg = RuleGenerationConfig(
    exclude_cols=[
        "target",
    ]
)
    if args.input:
        cfg.input_path = Path(args.input)
    if args.output:
        cfg.output_dir = Path(args.output)
    if args.target:
        cfg.target_col = args.target
    if args.lift is not None:
        cfg.lift_cutoff = args.lift
    if args.hit_rate_min is not None:
        cfg.hit_rate_down_cutoff = args.hit_rate_min
    if args.hit_rate_max is not None:
        cfg.hit_rate_up_cutoff = args.hit_rate_max
    return cfg


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
