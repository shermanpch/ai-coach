"""
Feature extraction decorators for defining typed feature functions.

This module provides decorators (@single and @multiple) to define feature extraction
functions with schema information (column names and data types). These decorated
functions work with the Sparkle class for batch feature extraction from datasets.

Examples:
    ```python
    from feasy.decorator import single, multiple

    # Single feature extraction
    @single("user_age", int)
    def extract_age(user_record):
        return 2024 - user_record.birth_year

    # Multiple feature extraction
    @multiple([
        ("transaction_amount", float),
        ("is_premium", bool),
        ("category", str)
    ])
    def extract_transaction_features(transaction):
        return [
            transaction.amount,
            transaction.user.is_premium,
            transaction.category.name
        ]
    ```

Supported Data Types:
    Common pandas-compatible types: str, int, float, bool, datetime64, category,
    or any valid pandas dtype string like "string", "Int64", etc.
"""

from functools import wraps
from typing import Any, Callable, List, Tuple, Type, Union


def multiple(params: List[Tuple[str, Union[Type, str]]]) -> Callable:
    """
    Decorator for functions that extract multiple features from a single data row.

    Args:
        params: List of (name, dtype) tuples where:
            - name (str): Feature/column name
            - dtype (type or str): Data type (e.g., int, float, str, bool, 'category')

    Returns:
        Callable: Decorator function that attaches schema metadata to the target function

    Raises:
        Exception: If feature specifications are invalid

    Examples:
        ```python
        @multiple([
            ("price", float),
            ("quantity", int),
            ("product_name", str)
        ])
        def extract_order_details(order_record):
            return [
                order_record.price,
                order_record.quantity,
                order_record.product.name
            ]

        @multiple([
            ("user_id", "string"),           # pandas string dtype
            ("signup_date", "datetime64[ns]"), # pandas datetime
            ("user_tier", "category"),       # pandas categorical
            ("is_active", bool)
        ])
        def extract_user_features(user):
            return [
                user.id,
                user.signup_date,
                user.tier,
                user.is_active
            ]
        ```

    Notes:
        - Return values must be in the same order as schema parameters
        - The decorated function should return a list with len(params) elements
    """
    # Comprehensive parameter validation
    for i, p in enumerate(params):
        if not isinstance(p, (tuple, list)) or len(p) != 2:
            raise Exception(
                f"Feature specification at index {i} should be a (name, dtype) pair, "
                f"got {type(p).__name__} with length {len(p) if hasattr(p, '__len__') else 'unknown'}"
            )

        name, dtype = p
        if not isinstance(name, str):
            raise Exception(
                f"Feature name at index {i} should be str, got {type(name).__name__}: {repr(name)}"
            )

        if not isinstance(dtype, (type, str)):
            raise Exception(
                f"Feature dtype for '{name}' should be a type instance or string, "
                f"got {type(dtype).__name__}: {repr(dtype)}"
            )

    def decorator(f: Callable) -> Callable:
        """Attach schema metadata to the function."""
        f.name = f.__name__
        f.schema = params
        return f

    return decorator


def single(name: str, dtype: Union[Type, str]) -> Callable:
    """
    Decorator for functions that extract a single feature from a data row.

    This is a convenience decorator for extracting one feature. It automatically
    wraps the function to return a list with a single element for compatibility
    with the multiple feature extraction framework.

    Args:
        name: The feature/column name
        dtype: The data type (e.g., str, int, float, bool, 'category', 'datetime64[ns]')

    Returns:
        Callable: Decorator function that wraps the target function

    Examples:
        ```python
        @single("user_id", str)
        def get_user_id(user_record):
            return user_record.id

        @single("account_balance", float)
        def get_balance(user):
            return float(user.balance_cents) / 100.0

        @single("signup_timestamp", "datetime64[ns]")
        def get_signup_time(user):
            return pd.to_datetime(user.created_at)

        @single("user_category", "category")
        def get_user_category(user):
            return user.membership_tier  # e.g., "bronze", "silver", "gold"
        ```

    Notes:
        - The original function should return a single value (not a list)
        - The decorator automatically converts the return value to a list
    """

    def decorator(f: Callable) -> Callable:
        """Wrap function to return list and apply multiple decorator."""

        @wraps(f)
        @multiple([(name, dtype)])
        def _wrapped_function(row: Any) -> List[Any]:
            """Execute original function and wrap result in list."""
            return [f(row)]

        # Preserve original function metadata
        _wrapped_function.name = f.__name__
        return _wrapped_function

    return decorator
