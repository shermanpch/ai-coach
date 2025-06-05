"""
Feature extraction engine for processing decorated feature functions.

This module provides the Sparkle class, which processes feature extraction functions
decorated with @single or @multiple decorators to extract features from datasets
in batch. It converts the extracted features into pandas DataFrames with proper
column names and data types.

Examples:
    ```python
    from feasy.decorator import single, multiple
    from feasy.sparkle import Sparkle

    @single("user_id", str)
    def get_user_id(user):
        return user.id

    @single("score", float)
    def get_score(user):
        return user.rating * 100

    @multiple([("age", int), ("income", float)])
    def get_demographics(user):
        return [user.age, user.annual_income]

    # Single group - extract all features into one DataFrame
    sparkle = Sparkle([get_user_id, get_score, get_demographics])
    features_df = sparkle.source(user_data).to_pandas()

    # Multiple groups - extract into separate DataFrames
    identity_funcs = [get_user_id]
    metric_funcs = [get_score, get_demographics]
    sparkle = Sparkle(identity_funcs, metric_funcs)
    identity_df, metrics_df = sparkle.source(user_data).to_pandas()
    ```
"""

from itertools import chain, starmap
from operator import attrgetter
from typing import Any, Callable, Iterable, List, Tuple, Union

import pandas as pd


def _extract(proto: Any, funcs: List[Callable]) -> List[Any]:
    """
    Apply feature functions to a single data row and flatten results.

    Args:
        proto: A single data record/row
        funcs: List of decorated feature extraction functions

    Returns:
        List[Any]: Flattened list of all feature values
    """
    result = []
    for feature_function in funcs:
        function_output = feature_function(proto)
        result.extend(function_output)
    return result


def _extractor(funcs_list: List[List[Callable]]) -> Callable:
    """
    Create function for processing multiple feature function groups.

    Args:
        funcs_list: List of function groups

    Returns:
        Callable: Function that processes a data row through all groups
    """

    def _grouped_extractor(proto: Any) -> Tuple[List[Any], ...]:
        return tuple(_extract(proto, function_group) for function_group in funcs_list)

    return _grouped_extractor


class Sparkle:
    """
    Feature extraction engine for processing decorated feature functions.

    Sparkle takes groups of decorated feature extraction functions and applies them
    to datasets, converting the results into properly typed pandas DataFrames.

    Examples:
        ```python
        # Define feature functions
        @single("user_id", str)
        def get_user_id(user):
            return user.id

        @multiple([("age", int), ("income", float)])
        def get_demographics(user):
            return [user.age, user.annual_income]

        # Single group
        sparkle = Sparkle([get_user_id, get_demographics])
        df = sparkle.source(user_data).to_pandas()
        # Returns: DataFrame with columns user_id, age, income

        # Multiple groups
        group1 = [get_user_id]
        group2 = [get_demographics]
        sparkle = Sparkle(group1, group2)
        df1, df2 = sparkle.source(user_data).to_pandas()
        # Returns: tuple of DataFrames
        ```
    """

    def __init__(self, *funcs: List[Callable]):
        """
        Initialize Sparkle with groups of feature extraction functions.

        Args:
            *funcs: Variable number of function lists. Each list contains
                   decorated feature extraction functions that will be
                   processed together into a single DataFrame.

        Examples:
            ```python
            # Single group of functions
            sparkle = Sparkle([func1, func2, func3])

            # Multiple groups of functions
            sparkle = Sparkle([func1, func2], [func3, func4])
            ```
        """
        self.funcs = funcs
        self.data = None

    def source(
        self,
        data: Union[Iterable[Any], pd.DataFrame],
        from_dataframe: bool = False,
    ) -> "Sparkle":
        """
        Set the data source for feature extraction.

        Args:
            data: Iterable dataset or pandas DataFrame
            from_dataframe: If True, converts DataFrame to named tuples

        Returns:
            Sparkle: Self for method chaining

        Examples:
            ```python
            # With iterable data
            sparkle = Sparkle([get_features]).source(user_records)

            # With pandas DataFrame
            sparkle = Sparkle([get_features]).source(user_df, from_dataframe=True)

            # Method chaining
            df = Sparkle([get_features]).source(data).to_pandas()
            ```
        """
        if from_dataframe:
            self.data = list(data.itertuples(index=False))
        else:
            self.data = data
        return self

    def to_matrix(self) -> Tuple[Tuple[List[Any], ...], ...]:
        """
        Apply all feature function groups to data and return matrix structure.

        Returns:
            Tuple: Matrix of results grouped by function lists

        Example:
            For funcs = [[func1], [func2]] and data = [row1, row2]:
            Returns: (
                ([func1(row1), func1(row2)],),        # Group 1
                ([func2(row1), func2(row2)],)         # Group 2
            )
        """
        extractor_function = _extractor(self.funcs)
        mapped_results = map(extractor_function, self.data)
        return tuple(zip(*mapped_results))

    def _matrix_to_df(
        self,
        matrix: Tuple[List[Any], ...],
        funcs: List[Callable],
    ) -> pd.DataFrame:
        """
        Convert feature matrix into pandas DataFrame with proper types.

        Args:
            matrix: Matrix of feature values for one function group
            funcs: List of decorated feature functions with schema info

        Returns:
            pd.DataFrame: DataFrame with named columns and proper data types
        """
        if len(funcs) == 0:
            return pd.DataFrame(matrix)

        all_schemas = chain(*map(attrgetter("schema"), funcs))
        column_names, column_types = zip(*all_schemas)
        df = pd.DataFrame(matrix, columns=column_names)
        type_mapping = dict(zip(column_names, column_types))
        return df.astype(type_mapping)

    def to_pandas(self) -> Union[pd.DataFrame, Tuple[pd.DataFrame, ...]]:
        """
        Extract features from dataset and return pandas DataFrames.

        Returns:
            Union[pd.DataFrame, Tuple[pd.DataFrame, ...]]:
                Single DataFrame if one function group, tuple if multiple groups

        Examples:
            ```python
            # Single function group
            @single("user_id", str)
            def get_id(user):
                return user.id

            sparkle = Sparkle([get_id])
            df = sparkle.source(users).to_pandas()
            # Returns: DataFrame directly

            # Multiple function groups
            sparkle = Sparkle([get_id], [get_age])
            df1, df2 = sparkle.source(users).to_pandas()
            # Returns: tuple of DataFrames
            ```
        """
        feature_matrix = self.to_matrix()
        result_dataframes = tuple(
            starmap(self._matrix_to_df, zip(feature_matrix, self.funcs))
        )

        if len(result_dataframes) == 1:
            return result_dataframes[0]
        return result_dataframes
