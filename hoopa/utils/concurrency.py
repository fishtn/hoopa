import asyncio
import functools
import typing
from asyncio import iscoroutinefunction
from typing import Any, AsyncGenerator, Iterator, Dict

try:
    import contextvars  # Python 3.7+ only.
except ImportError:  # pragma: no cover
    contextvars = None  # type: ignore

T = typing.TypeVar("T")


async def run_in_threadpool(
    func: typing.Callable[..., T], *args: typing.Any, **kwargs: typing.Any
) -> T:
    loop = asyncio.get_event_loop()
    if contextvars is not None:  # pragma: no cover
        # Ensure we run in the same context
        child = functools.partial(func, *args, **kwargs)
        context = contextvars.copy_context()
        func = context.run
        args = (child,)
    elif kwargs:  # pragma: no cover
        # loop.run_in_executor doesn't accept 'kwargs', so bind them in here
        func = functools.partial(func, **kwargs)
    return await loop.run_in_executor(None, func, *args)


async def run_function(callable_fun,  *args, **kwargs) -> Any:
    if iscoroutinefunction(callable_fun):
        return await callable_fun(*args, **kwargs)
    else:
        return await run_in_threadpool(callable_fun, *args, **kwargs)


async def run_function_no_concurrency(func,  *args, **kwargs):
    if iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


class _StopIteration(Exception):
    pass


def _next(iterator: Iterator) -> Any:
    # We can't raise `StopIteration` from within the threadpool iterator
    # and catch it outside that context, so we coerce them into a different
    # exception type.
    try:
        return next(iterator)
    except StopIteration:
        raise _StopIteration


async def iterate_in_threadpool(iterator: Iterator) -> AsyncGenerator:
    while True:
        try:
            yield await run_in_threadpool(_next, iterator)
        except _StopIteration:
            break