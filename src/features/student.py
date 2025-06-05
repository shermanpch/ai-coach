from ..feasy.decorator import single


@single("GradeLevel", str)
def get_student_grade_level(row) -> str:
    """Student grade level."""
    return row.GradeLevel


@single("is_gifted", str)
def is_gifted(row) -> str:
    """Student gifted status as binary: Y=gifted, D=not gifted, N=no info."""
    value = getattr(row, "ActiveGiftedStudentResultRecordFlag", None)
    if value not in ("Y", "D"):
        return "N"
    return value


@single("RetainedFlag", str)
def get_retained_flag(row) -> str:
    """Retained flag."""
    return row.RetainedFlag
