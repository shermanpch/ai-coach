from collections import Counter

import numpy as np
import pandas as pd

from .feasy.decorator import multiple, single


@single("mask_studentpersonkey", str)
def get_student_id(row) -> str:
    """Gets the customer ID."""
    return row.mask_studentpersonkey


@single("test", float)
def test(row):
    return row.illuminate.Response_points[0]
