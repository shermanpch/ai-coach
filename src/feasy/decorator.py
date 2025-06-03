from functools import wraps


def multiple(params):
    for p in params:
        if len(p) != 2:
            raise Exception("Feature specification should be (name, dtype) pair.")
        if not isinstance(p[0], str):
            raise Exception("Feature name should be str.")
        if not isinstance(p[1], (type, str)):
            raise Exception("Feature dtype should be an instance of type or string.")

    def decorator(f):
        f.name = f.__name__
        f.schema = params
        return f

    return decorator


def single(name, dtype):
    def decorator(f):
        @wraps(f)
        @multiple([(name, dtype)])
        def _f(row):
            return [f(row)]

        _f.name = f.__name__
        return _f

    return decorator
