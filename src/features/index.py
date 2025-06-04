from ..feasy.decorator import single


@single("mask_studentpersonkey", str)
def get_student_id(row) -> str:
    """Student ID."""
    return row.mask_studentpersonkey


@single("SchoolYearFall", str)
def get_school_year_fall(row) -> str:
    """School year fall."""
    return row.SchoolYearNumberFall
