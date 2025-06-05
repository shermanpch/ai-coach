"""
Utility functions for data manipulation and nested data structures.

This module provides functionality for creating nested data structures
from pandas DataFrames with dot notation access.
"""

import inspect
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class NestedData:
    """
    A class that provides dot notation access to nested data structures.

    This class allows you to access nested data using dot notation (e.g., obj.key)
    instead of dictionary-style access (e.g., obj['key']).

    Attributes:
        All attributes are dynamically set based on the input data dictionary.

    Example:
        >>> data = {'name': 'John', 'age': 30, 'city': 'New York'}
        >>> nested = NestedData(data)
        >>> nested.name
        'John'
        >>> nested.age
        30
    """

    def __init__(self, data_dict: Dict[str, Any]):
        """
        Initialize NestedData with a dictionary.

        Args:
            data_dict: Dictionary containing the data to be nested.

        Raises:
            TypeError: If data_dict is not a dictionary.
            ValueError: If data_dict is empty.
        """
        if not isinstance(data_dict, dict):
            raise TypeError("data_dict must be a dictionary")

        if not data_dict:
            raise ValueError("data_dict cannot be empty")

        for key, value in data_dict.items():
            # Handle nested dictionaries recursively
            if isinstance(value, dict):
                setattr(self, key, NestedData(value))
            else:
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Return a string representation of the NestedData object."""
        attrs = []
        for k, v in self.__dict__.items():
            if isinstance(v, NestedData):
                attrs.append(f"{k}=NestedData(...)")
            else:
                attrs.append(f"{k}={repr(v)}")
        return f"NestedData({', '.join(attrs)})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another NestedData object."""
        if not isinstance(other, NestedData):
            return False
        return self.__dict__ == other.__dict__

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the NestedData object back to a dictionary.

        Returns:
            Dictionary representation of the nested data.
        """
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, NestedData):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an attribute value with a default fallback.

        Args:
            key: The attribute name to retrieve.
            default: Default value if the attribute doesn't exist.

        Returns:
            The attribute value or the default value.
        """
        return getattr(self, key, default)

    def keys(self) -> List[str]:
        """
        Get all attribute names.

        Returns:
            List of attribute names.
        """
        return list(self.__dict__.keys())


def nest(
    df: pd.DataFrame,
    nested_column_name: str,
    columns_to_nest: Union[List[str], str],
    drop_original: bool = True,
    handle_missing: str = "skip",
) -> pd.DataFrame:
    """
    Create a nested column with dot notation access from specified columns.

    This function takes specified columns from a DataFrame and creates a new
    column containing NestedData objects that allow dot notation access to
    the original column values.

    Args:
        df: The input DataFrame.
        nested_column_name: Name for the new nested column.
        columns_to_nest: Column name(s) to include in the nested structure.
                        Can be a single string or list of strings.
        drop_original: Whether to drop the original columns after nesting.
                      Defaults to True.
        handle_missing: How to handle missing columns. Options:
                       - 'skip': Skip missing columns silently
                       - 'error': Raise an error for missing columns
                       - 'fill': Fill missing columns with None

    Returns:
        DataFrame with the new nested column.

    Raises:
        ValueError: If df is empty, nested_column_name already exists,
                   or columns_to_nest is empty.
        KeyError: If handle_missing='error' and columns are missing.
        TypeError: If df is not a DataFrame.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'id': [1, 2, 3],
        ...     'name': ['Alice', 'Bob', 'Charlie'],
        ...     'age': [25, 30, 35],
        ...     'city': ['NY', 'LA', 'Chicago']
        ... })
        >>> result = nest(df, 'person_info', ['name', 'age'])
        >>> result.person_info[0].name
        'Alice'
        >>> result.person_info[0].age
        25
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    elif df.empty:
        raise ValueError("DataFrame cannot be empty")

    if not nested_column_name or not isinstance(nested_column_name, str):
        raise ValueError("nested_column_name must be a non-empty string")

    if nested_column_name in df.columns:
        raise ValueError(f"Column '{nested_column_name}' already exists in DataFrame")

    # Handle single column input
    if isinstance(columns_to_nest, str):
        columns_to_nest = [columns_to_nest]

    if not columns_to_nest:
        raise ValueError("columns_to_nest cannot be empty")

    # Validate columns exist based on handle_missing strategy
    missing_columns = [col for col in columns_to_nest if col not in df.columns]

    if missing_columns:
        if handle_missing == "error":
            raise KeyError(f"Columns not found in DataFrame: {missing_columns}")
        elif handle_missing == "skip":
            columns_to_nest = [col for col in columns_to_nest if col in df.columns]
            if not columns_to_nest:
                raise ValueError(
                    "No valid columns found after filtering missing columns"
                )
        elif handle_missing == "fill":
            # Add missing columns with None values
            for col in missing_columns:
                df[col] = None
        else:
            raise ValueError("handle_missing must be 'skip', 'error', or 'fill'")

    def create_nested_object(row: pd.Series) -> NestedData:
        """Create a NestedData object from a DataFrame row."""
        data_dict = {}
        for col in columns_to_nest:
            if col in row.index:
                data_dict[col] = row[col]
        return NestedData(data_dict)

    # Create a copy to avoid modifying the original DataFrame
    result_df = df.copy()

    # Create the nested column
    result_df[nested_column_name] = result_df.apply(create_nested_object, axis=1)

    # Remove the original columns if requested
    if drop_original:
        columns_to_drop = [col for col in columns_to_nest if col in result_df.columns]
        result_df = result_df.drop(columns=columns_to_drop)

    return result_df


def unnest(
    df: pd.DataFrame,
    nested_column_name: str,
    prefix: Optional[str] = None,
    drop_nested: bool = True,
) -> pd.DataFrame:
    """
    Expand a nested column back into separate columns.

    This function takes a column containing NestedData objects and expands
    it back into separate columns.

    Args:
        df: The input DataFrame containing the nested column.
        nested_column_name: Name of the column containing NestedData objects.
        prefix: Optional prefix for the expanded column names.
        drop_nested: Whether to drop the nested column after expansion.

    Returns:
        DataFrame with expanded columns.

    Raises:
        ValueError: If nested_column_name doesn't exist in DataFrame.
        TypeError: If the nested column doesn't contain NestedData objects.

    Example:
        >>> # Assuming 'nested_df' has a 'person_info' column with NestedData objects
        >>> expanded = unnest(nested_df, 'person_info', prefix='person_')
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if nested_column_name not in df.columns:
        raise ValueError(f"Column '{nested_column_name}' not found in DataFrame")

    # Create a copy to avoid modifying the original DataFrame
    result_df = df.copy()

    # Extract data from the first non-null nested object to get column names
    sample_nested = None
    for nested_obj in result_df[nested_column_name]:
        if nested_obj is not None and isinstance(nested_obj, NestedData):
            sample_nested = nested_obj
            break

    if sample_nested is None:
        raise ValueError(
            f"No valid NestedData objects found in column '{nested_column_name}'"
        )

    # Get all possible keys from nested objects
    all_keys = set()
    for nested_obj in result_df[nested_column_name]:
        if isinstance(nested_obj, NestedData):
            all_keys.update(nested_obj.keys())

    # Create new columns
    for key in all_keys:
        column_name = f"{prefix}{key}" if prefix else key
        result_df[column_name] = result_df[nested_column_name].apply(
            lambda x, k=key: x.get(k) if isinstance(x, NestedData) else None
        )

    # Drop the nested column if requested
    if drop_nested:
        result_df = result_df.drop(columns=[nested_column_name])

    return result_df


def get_feature_functions_from_module(module: Any) -> List[Any]:
    """
    Extract all feature functions from a given module.

    A feature function is defined as a function that:
    1. Is actually a function (not a class or other object)
    2. Belongs to the specified module (not imported from elsewhere)
    3. Has a 'schema' attribute (typically added by decorators like @single)

    Args:
        module: The module to extract feature functions from.

    Returns:
        List of feature functions found in the module.

    Example:
        >>> from src.features import illuminate
        >>> feature_funcs = get_feature_functions_from_module(illuminate)
        >>> len(feature_funcs)  # Number of feature functions found
        23
    """
    feature_functions = []

    # Iterate through all members of the module
    for _name, member in inspect.getmembers(module):
        if (
            inspect.isfunction(member)
            and member.__module__ == module.__name__
            and hasattr(member, "schema")
        ):
            feature_functions.append(member)

    return feature_functions


def create_student_features(
    df: pd.DataFrame,
    student_col: str,
    year_col: str,
    target_cols: Union[List[str], str],
    numeric_dtypes: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create student-level features from longitudinal data.

    This function transforms student longitudinal data into a single row per student
    with features including:
    - Latest values for each feature (both numeric and categorical)
    - Change (delta) between first and last values (numeric features only)
    - Slopes (trends) across all time points (numeric features only)
    - Number of snapshots per student

    Args:
        df: The input DataFrame with student longitudinal data.
        student_col: Name of the column containing student identifiers.
        year_col: Name of the column containing year/time information.
        target_cols: Column name(s) to exclude from feature creation (typically target variables).
                    Can be a single string or list of strings.
        numeric_dtypes: List of numeric dtypes to include in delta and slope calculations.
                       Defaults to ["float64", "int64"].

    Returns:
        Tuple containing:
        - pd.DataFrame: Student identifiers as a DataFrame with one column
        - pd.DataFrame: Features DataFrame (one row per student) without student column.
        Features include:
        - {feature}_latest: Latest value for each feature (numeric and categorical)
        - {numeric_feature}_delta: Change from first to last value (numeric only)
        - {numeric_feature}_slope: OLS slope across all time points (numeric only)
        - num_snapshots: Number of time points per student

    Raises:
        ValueError: If required columns are missing or DataFrame is empty.
        TypeError: If df is not a DataFrame.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'student_id': [1, 1, 1, 2, 2],
        ...     'year': [2018, 2019, 2020, 2018, 2019],
        ...     'gpa': [3.0, 3.2, 3.5, 2.8, 3.0],
        ...     'sat_score': [1200, 1250, 1300, 1100, 1150],
        ...     'major': ['CS', 'CS', 'Math', 'Bio', 'Bio'],
        ...     'target': [0, 0, 1, 0, 1]
        ... })
        >>> student_df, features = create_student_features(
        ...     df, 'student_id', 'year', 'target'
        ... )
        >>> features.columns
        Index(['gpa_latest', 'sat_score_latest', 'major_latest', 'gpa_delta',
               'sat_score_delta', 'gpa_slope', 'sat_score_slope', 'num_snapshots'],
              dtype='object')
    """
    # Input validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    elif df.empty:
        raise ValueError("DataFrame cannot be empty")

    if student_col not in df.columns:
        raise ValueError(f"Student column '{student_col}' not found in DataFrame")

    if year_col not in df.columns:
        raise ValueError(f"Year column '{year_col}' not found in DataFrame")

    # Handle target_cols as string or list
    if isinstance(target_cols, str):
        target_cols = [target_cols]

    # Set default numeric dtypes
    if numeric_dtypes is None:
        numeric_dtypes = ["float64", "int64"]

    # Drop target columns and sort by student and year
    X_data = df.drop(columns=target_cols, errors="ignore").sort_values(
        [student_col, year_col]
    )

    # Identify numeric feature columns (everything except student_col and year_col)
    numeric_cols = [
        col
        for col, dtype in X_data.dtypes.items()
        if str(dtype) in numeric_dtypes and col not in (student_col, year_col)
    ]

    if not numeric_cols:
        raise ValueError("No numeric columns found for feature creation")

    # Identify all feature columns (for latest snapshot including categorical)
    all_feature_cols = [
        col for col in X_data.columns if col not in (student_col, year_col)
    ]

    # Extract "first snapshot" (earliest year) per student
    first_raw = (
        X_data.groupby(student_col, as_index=False)
        .head(1)
        .set_index(student_col)[numeric_cols]
    )

    # Extract "latest snapshot" (latest year) per student - include ALL features
    last_raw_all = (
        X_data.groupby(student_col, as_index=False)
        .tail(1)
        .set_index(student_col)[all_feature_cols]
    )

    # Extract numeric columns from latest snapshot for delta calculations
    last_raw_numeric = last_raw_all[numeric_cols]

    # Rename all latest features
    last = last_raw_all.rename(columns={c: f"{c}_latest" for c in all_feature_cols})

    # Compute delta = last_raw_numeric − first_raw (only for numeric columns)
    delta_raw = last_raw_numeric.subtract(first_raw)
    delta = delta_raw.rename(columns={c: f"{c}_delta" for c in numeric_cols})

    def slope_and_count(group: pd.DataFrame) -> pd.Series:
        """
        For each numeric column, compute OLS slope of that column across the
        student's snapshots (ordered by year_col). Also return num_snapshots.
        """
        out = {}
        grp = group.sort_values(year_col)
        n = len(grp)
        out["num_snapshots"] = n

        if n < 2:
            for col in numeric_cols:
                out[f"{col}_slope"] = 0.0
        else:
            idx_sum = n * (n - 1) / 2
            idx_sqsum = (n - 1) * n * (2 * n - 1) / 6

            for col in numeric_cols:
                y = grp[col].tolist()
                y_sum = sum(y)
                iy_sum = sum(i * v for i, v in enumerate(y))
                denom = n * idx_sqsum - idx_sum**2
                slope_v = (n * iy_sum - idx_sum * y_sum) / denom if denom else 0.0
                out[f"{col}_slope"] = slope_v

        return pd.Series(out)

    # Compute slopes and snapshot counts
    trends = X_data.groupby(student_col).apply(slope_and_count)

    # Merge all features into one row per student
    student_features = last.join(delta).join(trends)

    # Create student DataFrame with one column
    student_df = pd.DataFrame({student_col: student_features.index})

    # Reset index on features to remove student index
    student_features = student_features.reset_index(drop=True)

    # Return the student DataFrame and features separately
    return student_df, student_features
