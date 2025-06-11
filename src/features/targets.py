import pandas as pd

from ..feasy.decorator import single


@single("sat_math_score", float)
def get_sat_math_score(row) -> float:
    """SAT Math score."""
    sat_data = getattr(row, "sat", None)
    if sat_data is None or pd.isna(sat_data):
        return None
    return sat_data.MathScore[-1]


@single("sat_verbal_score", float)
def get_sat_verbal_score(row) -> int:
    """SAT Verbal score."""
    sat_data = getattr(row, "sat", None)
    if sat_data is None or pd.isna(sat_data):
        return None
    return sat_data.VerbalScore[-1]
