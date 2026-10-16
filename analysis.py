from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).parent / "data"
SOURCE_DATE = "September 22, 2026"


@dataclass(frozen=True)
class PercentileEstimate:
    value: float | None
    lower_bound: float
    upper_bound: float


def load_distribution(path: Path) -> pd.DataFrame:
    distribution = pd.read_csv(path)
    required_columns = {"min_rating", "max_rating", "label", "share_pct"}
    if not required_columns.issubset(distribution.columns):
        raise ValueError(f"Distribution data must include {sorted(required_columns)}.")
    if distribution.empty or distribution["share_pct"].isna().any():
        raise ValueError("Distribution data must contain rating bands and share values.")
    if (distribution["share_pct"] < 0).any():
        raise ValueError("Distribution shares must not be negative.")
    if not (2.0 <= distribution.iloc[0]["min_rating"]):
        raise ValueError("Distribution must start at or below the minimum supported rating.")
    if not (distribution["share_pct"].sum() == 100):
        raise ValueError("Published distribution shares must sum to 100%.")
    return distribution


def load_benchmarks(path: Path) -> pd.DataFrame:
    benchmarks = pd.read_csv(path).sort_values("rating").reset_index(drop=True)
    required_columns = {"rating", "percentile"}
    if not required_columns.issubset(benchmarks.columns):
        raise ValueError(f"Percentile data must include {sorted(required_columns)}.")
    if len(benchmarks) < 2 or benchmarks[list(required_columns)].isna().any().any():
        raise ValueError("At least two complete percentile benchmarks are required.")
    if benchmarks["rating"].duplicated().any():
        raise ValueError("Percentile benchmark ratings must be unique.")
    if not benchmarks["rating"].is_monotonic_increasing:
        raise ValueError("Percentile benchmark ratings must be in ascending order.")
    if not benchmarks["percentile"].between(0, 100).all():
        raise ValueError("Percentile benchmarks must be between 0 and 100.")
    if not benchmarks["percentile"].is_monotonic_increasing:
        raise ValueError("Percentile benchmarks must be in ascending order.")
    return benchmarks


def calculate_percentile(rating: float, benchmarks: pd.DataFrame) -> PercentileEstimate:
    """Interpolate published benchmarks without extrapolating beyond them."""
    first = benchmarks.iloc[0]
    last = benchmarks.iloc[-1]
    if rating < first["rating"]:
        return PercentileEstimate(None, 0.0, float(first["percentile"]))
    if rating > last["rating"]:
        return PercentileEstimate(None, float(last["percentile"]), 100.0)

    for index in range(1, len(benchmarks)):
        lower = benchmarks.iloc[index - 1]
        upper = benchmarks.iloc[index]
        if rating <= upper["rating"]:
            position = (rating - lower["rating"]) / (upper["rating"] - lower["rating"])
            value = lower["percentile"] + position * (upper["percentile"] - lower["percentile"])
            return PercentileEstimate(float(value), float(lower["percentile"]), float(upper["percentile"]))

    return PercentileEstimate(float(last["percentile"]), float(last["percentile"]), 100.0)


def get_rating_band(rating: float, distribution: pd.DataFrame) -> pd.Series | None:
    for _, band in distribution.iterrows():
        is_last_band = pd.isna(band["max_rating"])
        if rating >= band["min_rating"] and (is_last_band or rating < band["max_rating"]):
            return band
    return None


def rating_gap_to_next_benchmark(
    rating: float, benchmarks: pd.DataFrame
) -> tuple[float, float] | None:
    next_benchmarks = benchmarks.loc[benchmarks["rating"] > rating, "rating"]
    if next_benchmarks.empty:
        return None
    target = float(next_benchmarks.iloc[0])
    return target, target - rating


def summarize_distribution(distribution: pd.DataFrame) -> dict[str, float]:
    bands_in_the_threes = distribution.loc[
        distribution["min_rating"].ge(3.0) & distribution["max_rating"].le(4.0),
        "share_pct",
    ].sum()
    bands_at_four_or_above = distribution.loc[distribution["min_rating"].ge(4.0), "share_pct"].sum()
    return {
        "share_3s": float(bands_in_the_threes),
        "share_4_plus": float(bands_at_four_or_above),
    }
