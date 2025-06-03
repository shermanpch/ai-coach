"""
Utility functions for data manipulation and nested data structures.

This module provides functionality for creating nested data structures
from pandas DataFrames with dot notation access.
"""

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
    # Input validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if df.empty:
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
            lambda x: x.get(key) if isinstance(x, NestedData) else None
        )

    # Drop the nested column if requested
    if drop_nested:
        result_df = result_df.drop(columns=[nested_column_name])

    return result_df
