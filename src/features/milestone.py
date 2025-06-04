import statistics
from typing import Any, List, Sequence

from ..feasy.decorator import single


# --------------------------------------------------------------------------- #
# Small numeric utilities                                                      #
# --------------------------------------------------------------------------- #
def _mean(nums: Sequence[float]) -> float:
    """Graceful mean that returns 0.0 on an empty sequence."""
    return statistics.mean(nums) if nums else 0.0


def _pct(count: int, total: int) -> float:
    """Return count/total as a float in [0,1]. 0.0 if total==0."""
    return count / total if total else 0.0


def _ols_slope(y: Sequence[float]) -> float:
    """
    Ordinary‐least‐squares slope of y vs. its index (0,1,…,n−1).
    Returns 0.0 if fewer than 2 points.
    """
    n = len(y)
    if n < 2:
        return 0.0
    idx_sum = n * (n - 1) / 2  # Σ i
    idx_sqsum = (n - 1) * n * (2 * n - 1) / 6  # Σ i²
    y_sum = sum(y)
    iy_sum = sum(i * v for i, v in enumerate(y))
    denom = n * idx_sqsum - idx_sum**2
    return (n * iy_sum - idx_sum * y_sum) / denom if denom else 0.0


# --------------------------------------------------------------------------- #
# Subject‐keyword definitions                                                   #
# --------------------------------------------------------------------------- #
# Index Math‐related subjects in Milestone:
# (catches 'Algebra I', 'Algebra: Concepts and Connections', 'Coordinate Algebra')
MATH_KEYWORDS = (
    "algebra",  # catches 'Algebra I', 'Algebra: Concepts and Connections', 'Coordinate Algebra'
    "mathematics",  # catches 'Mathematics'
)

# Index ELA‐related subjects in Milestone:
# (catches 'English Language Arts', 'American Literature & Composition')
ELA_KEYWORDS = (
    "english language arts",  # exact match for 'English Language Arts'
    "american literature",  # catches 'American Literature & Composition'
    "composition",  # catches any leftover '& Composition'
)


def _mask_by_subject(
    subject_list: Sequence[str], keywords: tuple[str, ...]
) -> List[int]:
    """
    Return a list of indices i for which subject_list[i] contains ANY of the
    keywords (case‐insensitive). If subject_list is None or [], returns [].
    """
    if not subject_list:
        return []
    kw_lc = tuple(k.lower() for k in keywords)
    return [
        i
        for i, subj in enumerate(subject_list)
        if any(kw in str(subj).lower() for kw in kw_lc)
    ]


def _values_by_mask(values: Sequence[Any], mask: List[int]) -> List[Any]:
    """
    Return [ values[i] for i in mask ], preserving order. If values is None or [],
    returns [].
    """
    if not values:
        return []
    return [values[i] for i in mask if i < len(values)]


def _subject_metric(
    row, subject_keywords: tuple[str, ...], metric_list: Sequence[Any]
) -> List[Any]:
    """
    Return only those elements of metric_list whose SubjectDesc matches
    any keyword in subject_keywords.
    """
    idx = _mask_by_subject(row.milestone.SubjectDesc or [], subject_keywords)
    return _values_by_mask(metric_list or [], idx)


# --------------------------------------------------------------------------- #
# Basic snapshot‐level features                                                #
# --------------------------------------------------------------------------- #


@single("num_subjects_tested", int)
def get_num_subjects_tested(row) -> int:
    """Number of different subjects taken in this snapshot."""
    return len(row.milestone.SubjectDesc or [])


@single("mean_scale_score_all", float)
def get_mean_scale_score_all(row) -> float:
    """Mean of all ScaleScore values across all subjects (ignores None)."""
    vals = [s for s in (row.milestone.ScaleScore or []) if isinstance(s, (int, float))]
    return _mean(vals)


@single("std_scale_score_all", float)
def get_std_scale_score_all(row) -> float:
    """Standard deviation of ScaleScore across all subjects (ignores None)."""
    vals = [s for s in (row.milestone.ScaleScore or []) if isinstance(s, (int, float))]
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


@single("mean_achievement_level_all", float)
def get_mean_achievement_level_all(row) -> float:
    """Mean of AchievementLevel across all subjects (ignores None)."""
    vals = [
        lvl
        for lvl in (row.milestone.AchievementLevel or [])
        if isinstance(lvl, (int, float))
    ]
    return _mean(vals)


@single("pct_proficient_all", float)
def get_pct_proficient_all(row) -> float:
    """
    Fraction of subjects where AchievementLevel ≥ 3 (assuming 3+ is 'proficient').
    Returns 0.0 if no subjects.
    """
    levels = [
        lvl
        for lvl in (row.milestone.AchievementLevel or [])
        if isinstance(lvl, (int, float))
    ]
    total = len(levels)
    if total == 0:
        return 0.0
    return _pct(sum(1 for lvl in levels if lvl >= 3), total)


@single("mean_lexile_score_all", float)
def get_mean_lexile_score_all(row) -> float:
    """Mean LexileScore across all subjects (ignores None/nan)."""
    vals = [
        lx for lx in (row.milestone.LexileScore or []) if isinstance(lx, (int, float))
    ]
    return _mean(vals)


@single("num_unique_test_dates", int)
def get_num_unique_test_dates(row) -> int:
    """
    Number of distinct TestingDateId values in this snapshot (how many test‐days).
    """
    return len(set(row.milestone.TestingDateId or []))


# --------------------------------------------------------------------------- #
# Math‐specific performance metrics                                            #
# --------------------------------------------------------------------------- #


@single("scale_score_mean_math", float)
def get_scale_score_mean_math(row) -> float:
    """Mean ScaleScore for Math‐tagged subjects in this snapshot."""
    vals = [
        v
        for v in _subject_metric(row, MATH_KEYWORDS, row.milestone.ScaleScore)
        if isinstance(v, (int, float))
    ]
    return _mean(vals)


@single("scale_score_std_math", float)
def get_scale_score_std_math(row) -> float:
    """Standard deviation of ScaleScore for Math‐tagged subjects."""
    vals = [
        v
        for v in _subject_metric(row, MATH_KEYWORDS, row.milestone.ScaleScore)
        if isinstance(v, (int, float))
    ]
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


@single("achievement_level_mean_math", float)
def get_achievement_level_mean_math(row) -> float:
    """Mean AchievementLevel for Math‐tagged subjects."""
    vals = [
        v
        for v in _subject_metric(row, MATH_KEYWORDS, row.milestone.AchievementLevel)
        if isinstance(v, (int, float))
    ]
    return _mean(vals)


@single("pct_proficient_math", float)
def get_pct_proficient_math(row) -> float:
    """
    Fraction of Math‐tagged subjects with AchievementLevel ≥ 3.
    """
    vals = [
        v
        for v in _subject_metric(row, MATH_KEYWORDS, row.milestone.AchievementLevel)
        if isinstance(v, (int, float))
    ]
    total = len(vals)
    if total == 0:
        return 0.0
    return _pct(sum(1 for lvl in vals if lvl >= 3), total)


@single("lexile_mean_math", float)
def get_lexile_mean_math(row) -> float:
    """Mean LexileScore for Math‐tagged subjects (often NaN)."""
    vals = [
        v
        for v in _subject_metric(row, MATH_KEYWORDS, row.milestone.LexileScore)
        if isinstance(v, (int, float))
    ]
    return _mean(vals)


# --------------------------------------------------------------------------- #
# ELA‐specific performance metrics                                             #
# --------------------------------------------------------------------------- #


@single("scale_score_mean_ela", float)
def get_scale_score_mean_ela(row) -> float:
    """Mean ScaleScore for ELA‐tagged subjects in this snapshot."""
    vals = [
        v
        for v in _subject_metric(row, ELA_KEYWORDS, row.milestone.ScaleScore)
        if isinstance(v, (int, float))
    ]
    return _mean(vals)


@single("scale_score_std_ela", float)
def get_scale_score_std_ela(row) -> float:
    """Standard deviation of ScaleScore for ELA‐tagged subjects."""
    vals = [
        v
        for v in _subject_metric(row, ELA_KEYWORDS, row.milestone.ScaleScore)
        if isinstance(v, (int, float))
    ]
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


@single("achievement_level_mean_ela", float)
def get_achievement_level_mean_ela(row) -> float:
    """Mean AchievementLevel for ELA‐tagged subjects."""
    vals = [
        v
        for v in _subject_metric(row, ELA_KEYWORDS, row.milestone.AchievementLevel)
        if isinstance(v, (int, float))
    ]
    return _mean(vals)


@single("pct_proficient_ela", float)
def get_pct_proficient_ela(row) -> float:
    """
    Fraction of ELA‐tagged subjects with AchievementLevel ≥ 3.
    """
    vals = [
        v
        for v in _subject_metric(row, ELA_KEYWORDS, row.milestone.AchievementLevel)
        if isinstance(v, (int, float))
    ]
    total = len(vals)
    if total == 0:
        return 0.0
    return _pct(sum(1 for lvl in vals if lvl >= 3), total)


@single("lexile_mean_ela", float)
def get_lexile_mean_ela(row) -> float:
    """Mean LexileScore for ELA‐tagged subjects."""
    vals = [
        v
        for v in _subject_metric(row, ELA_KEYWORDS, row.milestone.LexileScore)
        if isinstance(v, (int, float))
    ]
    return _mean(vals)


# --------------------------------------------------------------------------- #
# Time‐aware growth and trajectory features                                    #
# --------------------------------------------------------------------------- #


@single("scale_score_slope_all", float)
def get_scale_score_slope_all(row) -> float:
    """
    OLS slope of all ScaleScore values vs. TestingDateId (across all subjects).
    Sort pairs by date, take the ordered list of scale scores, and compute slope.
    """
    pairs = sorted(
        [
            (d, s)
            for d, s in zip(
                row.milestone.TestingDateId or [], row.milestone.ScaleScore or []
            )
            if isinstance(d, (int, float)) and isinstance(s, (int, float))
        ],
        key=lambda x: x[0],
    )
    if len(pairs) < 2:
        return 0.0
    y = [s for _, s in pairs]
    return _ols_slope(y)


@single("scale_score_improvement_all", float)
def get_scale_score_improvement_all(row) -> float:
    """
    Change in scale score from first to last test date across all subjects:
    (last_score − first_score), ignoring subject labels.
    """
    pairs = sorted(
        [
            (d, s)
            for d, s in zip(
                row.milestone.TestingDateId or [], row.milestone.ScaleScore or []
            )
            if isinstance(d, (int, float)) and isinstance(s, (int, float))
        ],
        key=lambda x: x[0],
    )
    if len(pairs) < 2:
        return 0.0
    return pairs[-1][1] - pairs[0][1]


@single("num_test_days", int)
def get_num_test_days(row) -> int:
    """Number of distinct TestingDateId values in this snapshot."""
    return len(set(row.milestone.TestingDateId or []))


# -------------------- Math‐specific growth trajectories --------------------- #
@single("scale_score_slope_math", float)
def get_scale_score_slope_math(row) -> float:
    """
    OLS slope of Math‐tagged ScaleScore vs. TestingDateId (within this snapshot).
    """
    idx = _mask_by_subject(row.milestone.SubjectDesc or [], MATH_KEYWORDS)
    pairs = sorted(
        [
            (row.milestone.TestingDateId[i], row.milestone.ScaleScore[i])
            for i in idx
            if (
                isinstance(row.milestone.TestingDateId[i], (int, float))
                and isinstance(row.milestone.ScaleScore[i], (int, float))
            )
        ],
        key=lambda x: x[0],
    )
    if len(pairs) < 2:
        return 0.0
    y = [s for _, s in pairs]
    return _ols_slope(y)


@single("scale_score_improvement_math", float)
def get_scale_score_improvement_math(row) -> float:
    """
    Change in Math scale score from first to last test date (within this snapshot).
    """
    idx = _mask_by_subject(row.milestone.SubjectDesc or [], MATH_KEYWORDS)
    pairs = sorted(
        [
            (row.milestone.TestingDateId[i], row.milestone.ScaleScore[i])
            for i in idx
            if (
                isinstance(row.milestone.TestingDateId[i], (int, float))
                and isinstance(row.milestone.ScaleScore[i], (int, float))
            )
        ],
        key=lambda x: x[0],
    )
    if len(pairs) < 2:
        return 0.0
    return pairs[-1][1] - pairs[0][1]


# -------------------- ELA‐specific growth trajectories ---------------------- #
@single("scale_score_slope_ela", float)
def get_scale_score_slope_ela(row) -> float:
    """
    OLS slope of ELA‐tagged ScaleScore vs. TestingDateId (within this snapshot).
    """
    idx = _mask_by_subject(row.milestone.SubjectDesc or [], ELA_KEYWORDS)
    pairs = sorted(
        [
            (row.milestone.TestingDateId[i], row.milestone.ScaleScore[i])
            for i in idx
            if (
                isinstance(row.milestone.TestingDateId[i], (int, float))
                and isinstance(row.milestone.ScaleScore[i], (int, float))
            )
        ],
        key=lambda x: x[0],
    )
    if len(pairs) < 2:
        return 0.0
    y = [s for _, s in pairs]
    return _ols_slope(y)


@single("scale_score_improvement_ela", float)
def get_scale_score_improvement_ela(row) -> float:
    """
    Change in ELA scale score from first to last test date (within this snapshot).
    """
    idx = _mask_by_subject(row.milestone.SubjectDesc or [], ELA_KEYWORDS)
    pairs = sorted(
        [
            (row.milestone.TestingDateId[i], row.milestone.ScaleScore[i])
            for i in idx
            if (
                isinstance(row.milestone.TestingDateId[i], (int, float))
                and isinstance(row.milestone.ScaleScore[i], (int, float))
            )
        ],
        key=lambda x: x[0],
    )
    if len(pairs) < 2:
        return 0.0
    return pairs[-1][1] - pairs[0][1]
