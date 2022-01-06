""" Decorator for query parameters. """

from inspect import signature
from functools import wraps


def _process_requests_args(*, reqarg_name, reqargs):
    def decorator(func):
        @wraps(func)
        def wrapped(*fargs, **fkwargs):
            processed = {}
            for reqarg in reqargs:
                arg_sig = signature(reqarg.__init__)
                init_args = {
                    p: fkwargs.pop(p) for p in arg_sig.parameters if p in fkwargs
                }
                if init_args:
                    reqarg_inst = reqarg(**init_args)
                    processed.update(reqarg_inst.to_dict())
            result = func(*fargs, **fkwargs, **{reqarg_name: processed})
            return result

        return wrapped

    return decorator


def file_args(*args):
    """ Process arguments for `files` parameter of requests """
    return _process_requests_args(reqarg_name="files", reqargs=args)


def params_args(*args):
    """ Process arguments for `params` parameter of requests """
    return _process_requests_args(reqarg_name="params", reqargs=args)
