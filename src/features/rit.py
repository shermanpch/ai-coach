import statistics
from typing import Sequence

from ..feasy.decorator import single


# --------------------------------------------------------------------------- #
# Small numeric utilities                                                     #
# --------------------------------------------------------------------------- #
def _mean(nums: Sequence[float]) -> float:
    """Return the mean of nums, or 0.0 if empty."""
    return statistics.mean(nums) if nums else 0.0


# --------------------------------------------------------------------------- #
# 1. Count of records per snapshot                                            #
# --------------------------------------------------------------------------- #
@single("num_tests", int)
def get_num_tests(row) -> int:
    """
    Number of MAP test entries in this snapshot.
    Uses length of TestRITScore (assumes all score-related lists are same length).
    """
    vals = getattr(row.rit, "TestRITScore", None) or []
    return len(vals)


# --------------------------------------------------------------------------- #
# 2. TestDurationMinutes features                                             #
# --------------------------------------------------------------------------- #
@single("mean_test_duration", float)
def get_mean_test_duration(row) -> float:
    """
    Mean of TestDurationMinutes across all tests in this snapshot.
    Ignores non-numeric entries.
    """
    vals = getattr(row.rit, "TestDurationMinutes", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return _mean(numeric_vals)


@single("std_test_duration", float)
def get_std_test_duration(row) -> float:
    """
    Standard deviation of TestDurationMinutes.
    Returns 0.0 if fewer than 2 numeric entries.
    """
    vals = getattr(row.rit, "TestDurationMinutes", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return statistics.pstdev(numeric_vals) if len(numeric_vals) > 1 else 0.0


# --------------------------------------------------------------------------- #
# 3. TestRITScore features                                                    #
# --------------------------------------------------------------------------- #
@single("mean_rit_score", float)
def get_mean_rit_score(row) -> float:
    """
    Mean of all TestRITScore values across tests in this snapshot.
    Ignores non-numeric entries.
    """
    vals = getattr(row.rit, "TestRITScore", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return _mean(numeric_vals)


@single("std_rit_score", float)
def get_std_rit_score(row) -> float:
    """
    Standard deviation of TestRITScore.
    Returns 0.0 if fewer than 2 numeric entries.
    """
    vals = getattr(row.rit, "TestRITScore", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return statistics.pstdev(numeric_vals) if len(numeric_vals) > 1 else 0.0


@single("max_rit_score", float)
def get_max_rit_score(row) -> float:
    """
    Maximum RIT score in this snapshot (0.0 if no numeric entries).
    """
    vals = getattr(row.rit, "TestRITScore", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return max(numeric_vals) if numeric_vals else 0.0


@single("min_rit_score", float)
def get_min_rit_score(row) -> float:
    """
    Minimum RIT score in this snapshot (0.0 if no numeric entries).
    """
    vals = getattr(row.rit, "TestRITScore", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return min(numeric_vals) if numeric_vals else 0.0


# --------------------------------------------------------------------------- #
# 4. TestPercentile features                                                  #
# --------------------------------------------------------------------------- #
@single("mean_percentile", float)
def get_mean_percentile(row) -> float:
    """
    Mean of TestPercentile values across tests in this snapshot.
    Ignores non-numeric entries.
    """
    vals = getattr(row.rit, "TestPercentile", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return _mean(numeric_vals)


@single("std_percentile", float)
def get_std_percentile(row) -> float:
    """
    Standard deviation of TestPercentile.
    Returns 0.0 if fewer than 2 numeric entries.
    """
    vals = getattr(row.rit, "TestPercentile", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return statistics.pstdev(numeric_vals) if len(numeric_vals) > 1 else 0.0


# --------------------------------------------------------------------------- #
# 5. AchievementQuintile features                                             #
# --------------------------------------------------------------------------- #
@single("count_quintile_high", int)
def get_count_quintile_high(row) -> int:
    """
    Count of tests where AchievementQuintile == 'High' (case-insensitive).
    """
    raw = getattr(row.rit, "AchievementQuintile", None) or []
    return sum(
        1 for x in raw if isinstance(x, str) and x.lower().strip("'\"") == "high"
    )


@single("count_quintile_hiavg", int)
def get_count_quintile_hiavg(row) -> int:
    """
    Count of tests where AchievementQuintile is 'HiAvg' or 'HighAvg'.
    """
    raw = getattr(row.rit, "AchievementQuintile", None) or []
    return sum(
        1
        for x in raw
        if isinstance(x, str) and x.lower().strip("'\"") in ("hiavg", "highavg")
    )


@single("count_quintile_avg", int)
def get_count_quintile_avg(row) -> int:
    """
    Count of tests where AchievementQuintile == 'Avg'.
    """
    raw = getattr(row.rit, "AchievementQuintile", None) or []
    return sum(1 for x in raw if isinstance(x, str) and x.lower().strip("'\"") == "avg")


@single("count_quintile_lowavg", int)
def get_count_quintile_lowavg(row) -> int:
    """
    Count of tests where AchievementQuintile == 'LoAvg' or 'LowAvg'.
    """
    raw = getattr(row.rit, "AchievementQuintile", None) or []
    return sum(
        1
        for x in raw
        if isinstance(x, str) and x.lower().strip("'\"") in ("loavg", "lowavg")
    )


@single("count_quintile_low", int)
def get_count_quintile_low(row) -> int:
    """
    Count of tests where AchievementQuintile == 'Low'.
    """
    raw = getattr(row.rit, "AchievementQuintile", None) or []
    return sum(1 for x in raw if isinstance(x, str) and x.lower().strip("'\"") == "low")


@single("pct_quintile_high", float)
def get_pct_quintile_high(row) -> float:
    """
    Fraction of tests in the 'High' quintile (0.0 if no entries).
    """
    raw = getattr(row.rit, "AchievementQuintile", None) or []
    total = len(raw)
    if total == 0:
        return 0.0
    high_count = sum(
        1 for x in raw if isinstance(x, str) and x.lower().strip("'\"") == "high"
    )
    return high_count / total


# --------------------------------------------------------------------------- #
# 6. PercentCorrect features                                                  #
# --------------------------------------------------------------------------- #
@single("mean_percent_correct", float)
def get_mean_percent_correct(row) -> float:
    """
    Mean of PercentCorrect values across tests (ignores non-numeric).
    """
    vals = getattr(row.rit, "PercentCorrect", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return _mean(numeric_vals)


@single("std_percent_correct", float)
def get_std_percent_correct(row) -> float:
    """
    Standard deviation of PercentCorrect.
    Returns 0.0 if fewer than 2 numeric entries.
    """
    vals = getattr(row.rit, "PercentCorrect", None) or []
    numeric_vals = [v for v in vals if isinstance(v, (int, float))]
    return statistics.pstdev(numeric_vals) if len(numeric_vals) > 1 else 0.0
