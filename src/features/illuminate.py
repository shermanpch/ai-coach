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
    """count / total as a float in [0, 1]."""
    return count / total if total else 0.0


def _ols_slope(y: Sequence[float]) -> float:
    """
    Ordinary‐least‐squares slope of y against its index (0,1,…,n-1).
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
# (catches both “Mathematics” and “Georgia’s K-12 Mathematics Standards”)
MATH_KEYWORDS = ("mathematics", "math")

# (catches “English Language Arts” and any variant with “ela”/“english”/“language arts”)
ELA_KEYWORDS = ("english language arts", "ela", "english", "language arts")


def _mask_by_subject(
    subject_list: Sequence[str], keywords: tuple[str, ...]
) -> List[int]:
    """
    Return a list of indices for items whose `Standard_Subject`
    contains any keyword (case‐insensitive).
    """
    kw_lc = tuple(k.lower() for k in keywords)
    return [
        i
        for i, subj in enumerate(subject_list)
        if any(kw in str(subj).lower() for kw in kw_lc)
    ]


def _values_by_mask(values: Sequence[Any], mask: List[int]) -> List[Any]:
    """
    Grab elements from `values` at the positions specified in `mask`,
    preserving order.
    """
    return [values[i] for i in mask]


def _subject_scores(row, keywords: tuple[str, ...]) -> List[float]:
    """
    Return the Standard_percent_correct values whose Standard_Subject
    matches any keyword (case‐insensitive).
    """
    return _values_by_mask(
        row.illuminate.Standard_percent_correct,
        _mask_by_subject(row.illuminate.Standard_Subject, keywords),
    )


# --------------------------------------------------------------------------- #
# Row‐level (per‐student) features                                             #
# --------------------------------------------------------------------------- #


@single("total_points_possible", float)
def get_total_points_possible(row) -> float:
    """Sum of all available points across the student’s Spring 2025 assessments."""
    return sum(row.illuminate.Response_points_possible)


@single("total_points_earned", float)
def get_total_points_earned(row) -> float:
    """Sum of points the student actually earned."""
    return sum(row.illuminate.Response_points)


@single("weighted_overall_percent_correct", float)
def get_weighted_overall_percent_correct(row) -> float:
    """Overall accuracy weighted by points possible (Σ earned / Σ possible)."""
    possible_total = sum(row.illuminate.Response_points_possible)
    earned_total = sum(row.illuminate.Response_points)
    return earned_total / possible_total if possible_total else 0.0


@single("mean_item_percent_correct", float)
def get_mean_item_percent_correct(row) -> float:
    """Unweighted mean of item‐level % correct (all subjects combined)."""
    return _mean(row.illuminate.Response_percent_correct)


@single("std_item_percent_correct", float)
def get_std_item_percent_correct(row) -> float:
    """Variation in item‐level performance (all subjects combined)."""
    vals = row.illuminate.Response_percent_correct
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


@single("num_items", int)
def get_num_items(row) -> int:
    """Count of scored items attempted (all subjects combined)."""
    return len(row.illuminate.Response_points)


# ---------- Metacognitive tags from Illuminate’s mastery conditions ---------- #
@single("percent_extension", float)
def get_percent_extension(row) -> float:
    """Fraction of all items marked ‘Extension’ (student already excels)."""
    tags = row.illuminate.condition
    return _pct(tags.count("Extension"), len(tags))


@single("percent_reteach", float)
def get_percent_reteach(row) -> float:
    """Fraction of all items marked ‘Reteach’ (student needs remediation)."""
    tags = row.illuminate.condition
    return _pct(tags.count("Reteach"), len(tags))


@single("percent_review_practice", float)
def get_percent_review_practice(row) -> float:
    """Fraction of all items marked ‘Review & Practice’."""
    tags = row.illuminate.condition
    return _pct(tags.count("Review & Practice"), len(tags))


# -------------------- Standard‐level mastery aggregates --------------------- #
@single("mean_standard_percent_correct", float)
def get_mean_standard_percent_correct(row) -> float:
    """Average mastery across every linked standard (all subjects combined)."""
    return _mean(row.illuminate.Standard_percent_correct)


@single("mastery_rate_above_80", float)
def get_mastery_rate_above_80(row) -> float:
    """Share of all standards ≥ 80% correct (robust mastery)."""
    scores = row.illuminate.Standard_percent_correct
    return _pct(sum(s >= 80 for s in scores), len(scores))


@single("low_mastery_rate_below_50", float)
def get_low_mastery_rate_below_50(row) -> float:
    """Share of all standards ≤ 50% correct (major gaps)."""
    scores = row.illuminate.Standard_percent_correct
    return _pct(sum(s <= 50 for s in scores), len(scores))


# ------------------------- Subject‐specific readiness ----------------------- #
@single("mean_std_pct_math", float)
def get_mean_std_pct_math(row) -> float:
    """Mean standard‐level % correct for Mathematics standards."""
    return _mean(_subject_scores(row, MATH_KEYWORDS))


@single("mean_std_pct_ela", float)
def get_mean_std_pct_ela(row) -> float:
    """Mean standard‐level % correct for English Language Arts standards."""
    return _mean(_subject_scores(row, ELA_KEYWORDS))


@single("math_total_points_possible", float)
def get_math_total_points_possible(row) -> float:
    """Sum of points‐possible for Math‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    possibles = _values_by_mask(row.illuminate.Response_points_possible, idx)
    return sum(possibles)


@single("verbal_total_points_possible", float)
def get_verbal_total_points_possible(row) -> float:
    """Sum of points‐possible for ELA/English‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    possibles = _values_by_mask(row.illuminate.Response_points_possible, idx)
    return sum(possibles)


@single("math_total_points_earned", float)
def get_math_total_points_earned(row) -> float:
    """Sum of points‐earned for Math‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    earned = _values_by_mask(row.illuminate.Response_points, idx)
    return sum(earned)


@single("verbal_total_points_earned", float)
def get_verbal_total_points_earned(row) -> float:
    """Sum of points‐earned for ELA/English‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    earned = _values_by_mask(row.illuminate.Response_points, idx)
    return sum(earned)


@single("math_weighted_percent_correct", float)
def get_math_weighted_percent_correct(row) -> float:
    """Math accuracy weighted by Math points possible."""
    earned = get_math_total_points_earned(row)[-1]
    possible = get_math_total_points_possible(row)[-1]
    return earned / possible if possible else 0.0


@single("verbal_weighted_percent_correct", float)
def get_verbal_weighted_percent_correct(row) -> float:
    """ELA accuracy weighted by ELA points possible."""
    earned = get_verbal_total_points_earned(row)[-1]
    possible = get_verbal_total_points_possible(row)[-1]
    return earned / possible if possible else 0.0


@single("math_mean_item_pct_correct", float)
def get_math_mean_item_pct_correct(row) -> float:
    """Unweighted mean of item‐level % correct for Math‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    vals = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return _mean(vals)


@single("verbal_mean_item_pct_correct", float)
def get_verbal_mean_item_pct_correct(row) -> float:
    """Unweighted mean of item‐level % correct for ELA‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    vals = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return _mean(vals)


@single("math_std_item_pct_correct", float)
def get_math_std_item_pct_correct(row) -> float:
    """Variation in item‐level % correct for Math‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    vals = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


@single("verbal_std_item_pct_correct", float)
def get_verbal_std_item_pct_correct(row) -> float:
    """Variation in item‐level % correct for ELA‐tagged items."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    vals = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


@single("math_mastery_rate_above_80", float)
def get_math_mastery_rate_above_80(row) -> float:
    """Share of Math standards ≥ 80% correct (strong Math mastery)."""
    scores = _subject_scores(row, MATH_KEYWORDS)
    return _pct(sum(s >= 80 for s in scores), len(scores))


@single("verbal_mastery_rate_above_80", float)
def get_verbal_mastery_rate_above_80(row) -> float:
    """Share of ELA standards ≥ 80% correct (strong Verbal mastery)."""
    scores = _subject_scores(row, ELA_KEYWORDS)
    return _pct(sum(s >= 80 for s in scores), len(scores))


@single("math_low_mastery_rate_below_50", float)
def get_math_low_mastery_rate_below_50(row) -> float:
    """Share of Math standards ≤ 50% correct (Math gaps)."""
    scores = _subject_scores(row, MATH_KEYWORDS)
    return _pct(sum(s <= 50 for s in scores), len(scores))


@single("verbal_low_mastery_rate_below_50", float)
def get_verbal_low_mastery_rate_below_50(row) -> float:
    """Share of ELA standards ≤ 50% correct (Verbal gaps)."""
    scores = _subject_scores(row, ELA_KEYWORDS)
    return _pct(sum(s <= 50 for s in scores), len(scores))


@single("math_percent_reteach", float)
def get_math_percent_reteach(row) -> float:
    """Fraction of Math‐tagged items marked ‘Reteach’."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    tags = _values_by_mask(row.illuminate.condition, idx)
    return _pct(tags.count("Reteach"), len(tags))


@single("verbal_percent_reteach", float)
def get_verbal_percent_reteach(row) -> float:
    """Fraction of ELA‐tagged items marked ‘Reteach’."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    tags = _values_by_mask(row.illuminate.condition, idx)
    return _pct(tags.count("Reteach"), len(tags))


@single("math_percent_extension", float)
def get_math_percent_extension(row) -> float:
    """Fraction of Math‐tagged items marked ‘Extension’."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    tags = _values_by_mask(row.illuminate.condition, idx)
    return _pct(tags.count("Extension"), len(tags))


@single("verbal_percent_extension", float)
def get_verbal_percent_extension(row) -> float:
    """Fraction of ELA‐tagged items marked ‘Extension’."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    tags = _values_by_mask(row.illuminate.condition, idx)
    return _pct(tags.count("Extension"), len(tags))


@single("math_percent_review_practice", float)
def get_math_percent_review_practice(row) -> float:
    """Fraction of Math‐tagged items marked ‘Review & Practice’."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    tags = _values_by_mask(row.illuminate.condition, idx)
    return _pct(tags.count("Review & Practice"), len(tags))


@single("verbal_percent_review_practice", float)
def get_verbal_percent_review_practice(row) -> float:
    """Fraction of ELA‐tagged items marked ‘Review & Practice’."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    tags = _values_by_mask(row.illuminate.condition, idx)
    return _pct(tags.count("Review & Practice"), len(tags))


# -------------------- Time‐aware (growth & recency) signals ----------------- #
@single("last_percent_correct", float)
def get_last_percent_correct(row) -> float:
    """Most recent item‐level % correct (all subjects combined)."""
    vals = row.illuminate.Response_percent_correct
    return vals[-1] if vals else 0.0


@single("improvement_first_to_last", float)
def get_improvement_first_to_last(row) -> float:
    """Change in overall % correct from first to last assessment."""
    vals = row.illuminate.Response_percent_correct
    return vals[-1] - vals[0] if len(vals) >= 2 else 0.0


@single("slope_percent_correct_over_time", float)
def get_slope_percent_correct_over_time(row) -> float:
    """
    OLS slope of % correct vs. assessment index
    (all subjects combined).
    """
    return _ols_slope(row.illuminate.Response_percent_correct)


@single("num_assessments", int)
def get_num_assessments(row) -> int:
    """Count of separate assessments taken in Spring 2025."""
    return len(row.illuminate.responsedatevalue)


@single("math_improvement_first_to_last", float)
def get_math_improvement_first_to_last(row) -> float:
    """Change in % correct for Math‐tagged items from first to last."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    scores = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return (scores[-1] - scores[0]) if len(scores) >= 2 else 0.0


@single("verbal_improvement_first_to_last", float)
def get_verbal_improvement_first_to_last(row) -> float:
    """Change in % correct for ELA‐tagged items from first to last."""
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    scores = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return (scores[-1] - scores[0]) if len(scores) >= 2 else 0.0


@single("math_slope_percent_correct_over_time", float)
def get_math_slope_percent_correct_over_time(row) -> float:
    """
    OLS slope of % correct vs. index for Math‐tagged items
    (>0 ⇒ upward Math trend).
    """
    idx = _mask_by_subject(row.illuminate.Standard_Subject, MATH_KEYWORDS)
    vals = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return _ols_slope(vals)


@single("verbal_slope_percent_correct_over_time", float)
def get_verbal_slope_percent_correct_over_time(row) -> float:
    """
    OLS slope of % correct vs. index for ELA‐tagged items
    (>0 ⇒ upward Verbal trend).
    """
    idx = _mask_by_subject(row.illuminate.Standard_Subject, ELA_KEYWORDS)
    vals = _values_by_mask(row.illuminate.Response_percent_correct, idx)
    return _ols_slope(vals)


# ------------------------- Grade‐level alignment ---------------------------- #
@single("grade_mode_numeric", int)
def get_grade_mode_numeric(row) -> int:
    """
    Most common grade level (as int) across the student’s Spring 2025 tests.
    Useful for spotting acceleration/retention.
    """
    grades = [
        int(g)
        for g in row.illuminate.GradeLevelDuringUnitTest
        if isinstance(g, (int, str)) and str(g).isdigit()
    ]
    return statistics.mode(grades) if grades else 0


@single("is_on_sat_grade_level", int)
def get_is_on_sat_grade_level(row) -> int:
    """1 if the student’s modal grade is 11 (typical SAT year), else 0."""
    return int(get_grade_mode_numeric(row)[-1] == 11)
