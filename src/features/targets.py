from ..feasy.decorator import single


@single("sat_math_score", int)
def get_sat_math_score(row) -> int:
    """SAT Math score."""
    return row.sat.MathScore[-1]


@single("sat_verbal_score", int)
def get_sat_verbal_score(row) -> int:
    """SAT Verbal score."""
    return row.sat.VerbalScore[-1]
