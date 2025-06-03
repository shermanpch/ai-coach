from itertools import chain, starmap
from operator import attrgetter

import pandas as pd


def _extract(proto, funcs):
    """
    Apply a list of functions to 1 row/record of data
    and return the outputs in a list

    Args:
        proto => 1 row/record of data.
        funcs -> [func1, func2]
    Returns:
        list -> [func1(proto), func2(proto)]
    """
    res = []
    for f in funcs:
        res.extend(f(proto))
    return res


def _extractor(funcs_list):
    """
    Maps each list of functions to proto and return a tuple

    Args:
        funcs_list -> [[func1, func2], [func3, func4]]
    Returns:
        tuple -> ((func1(proto), func2(proto)), (func3(proto), func4(proto)))
    """

    def _f(proto):
        return tuple(_extract(proto, funcs) for funcs in funcs_list)

    return _f


class Sparkle:
    def __init__(self, *funcs):
        self.funcs = funcs
        self.data = None

    def source(self, data):
        self.data = data
        return self

    def to_matrix(self):
        """
        Map each list of functions to all rows of data and return a tuple
        grouped accordingly to the list of functions

        Args:
            self.funcs -> [[func1, func2], [func3, func4]]
            self.data -> [proto1, proto2]
        Returns:
            tuple -> (
            (([func1(proto1), func1(proto2)], [func2(proto1), func2(proto2)]), [func1, func2]),
            (([func3(proto1), func3(proto2)], [func4(proto1), func4(proto2)]), [func3, func4]),
            )
        """
        matrix = map(_extractor(self.funcs), self.data)
        return tuple(zip(*matrix))

    def _matrix_to_df(self, matrix, funcs):
        """
        Each element of to_matrix output is a list of functions applied to all rows of data
        One dataframe will be created from each element of to_matrix output

        Returns:
            dataframe -> [col1, col2]
        """
        # If empty list of functions, just return matrix in the form of dataframe
        if len(self.funcs) == 0:
            return pd.DataFrame(matrix)
        # Unpack schema into a list of feature names and a list of types
        names, types = zip(*chain(*map(attrgetter("schema"), funcs)))
        return pd.DataFrame(matrix, columns=names).astype(dict(zip(names, types)))

    def to_pandas(self):
        """
        Map _matrix_to_df across every list of functions in self.funcs
        Each list of functions will generate a dataframe

        Returns:
            tuple -> (df1, df2, df3)
        """
        return tuple(starmap(self._matrix_to_df, zip(self.to_matrix(), self.funcs)))
