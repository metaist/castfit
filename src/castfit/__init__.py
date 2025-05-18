"""castfit: basic type casting

.. include:: ../../README.md
   :start-line: 2
"""

# std
from __future__ import annotations
from dataclasses import is_dataclass
from datetime import datetime
from inspect import signature
from types import BuiltinFunctionType
from typing import Any
from typing import Callable
from typing import cast
from typing import get_args
from typing import get_origin
from typing import get_type_hints
from typing import Literal
from typing import NoReturn
from typing import Optional
from typing import TypeVar
from typing import Union
import sys

# from typing import _SpecialForm

# TODO 2025-10-31 @ py3.9 EOL: move imports above
if sys.version_info >= (3, 10):  # pragma: no cover
    from types import NoneType
    from types import UnionType
else:  # pragma: no cover
    NoneType = type(None)  # same as `types.NoneType`
    UnionType = type(Union[int, str])  # workaround

# TODO 2026-10-31 @ py3.10 EOL: move imports above
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Never
else:  # pragma: no cover
    Never = NoReturn  # semantically same; syntactically different

__all__ = [
    "__version__",
    "__pubdate__",
    #
    # imported
    "Never",
    "NoneType",
    "UnionType",
    #
    # types
    "TypeForm",
    "CastFn",
    "Casts",
    #
    # top-level API
    "castfit",
    "is_type",
    "to_type",
    "DEFAULT_ENCODING",
    #
    # extensions
    "converts",
    #
    # lower-level API
    "get_origin_type",
    "setattrs",
    "to_any",
    "to_never",
    "to_none",
    "to_literal",
    "to_union",
    "to_bytes",
    "to_str",
    "to_list",
    "to_set",
    "to_dict",
    "to_tuple",
    "to_datetime",
]

__version__ = "0.1.1"
__pubdate__ = "2025-04-28T14:32:37Z"

DEFAULT_ENCODING = "utf-8"
"""Default file encoding."""

F = TypeVar("F")
"""Type variable for functions."""

K = TypeVar("K")
"""Type variable for keys."""

T = TypeVar("T")
"""Type variable for values."""

Ignored = Optional[Any]
"""A function argument that is ignored."""

SPECIAL_FORMS = (Any, Never, NoReturn, NoneType, Literal, Union, UnionType)
"""Special forms."""

# TypeForm = Union[type[T], type(Any), type(Union), UnionType, _SpecialForm]
TypeForm = Union[type[T], Any]
"""`Type` and special forms like `Any`, `Union`, etc."""
# NOTE: We want `type[T] | _SpecialForm` but type checkers can't handle it.

CastFnShort = Callable[[Any], Any]
"""Function signature for a simple caster."""

CastFnLong = Callable[[Any, TypeForm[T], "Casts | None"], T]
"""Function signature for a full caster."""

CastFn = Union[CastFnShort, CastFnLong[T]]
"""Function signature that maps a value to a type."""

Casts = dict[tuple[TypeForm[Any], TypeForm[Any]], CastFn[Any]]
"""Type of internal mapping of types to cast functions."""

TYPE_CASTS: Casts = {}
"""Mapping of types to cast functions."""

### Utilities ###


def setattrs(obj: T, values: Union[dict[str, Any], None] = None, **extra: Any) -> T:
    """Like `setattr()` but for multiple values and returns the object."""
    items = {**values, **extra} if values else extra
    for name, val in items.items():
        setattr(obj, name, val)
    return obj


def get_origin_type(item: TypeForm[T] | T) -> type[T]:
    """Returns the `item` origin, the `item` itself, or `type(item)`.

    See: [typing.get_origin](https://docs.python.org/3/library/typing.html#typing.get_origin)
    """
    origin = get_origin(item) or item
    if isinstance(origin, type) or origin in SPECIAL_FORMS:
        return cast(type[T], origin)  # cast due to mypy
    return cast(type[T], type(item))  # cast due to mypy


def get_types(item: type[T] | Callable[..., Any]) -> dict[str, Any]:
    """Returns names and inferred types for `item`.

    See: [typing.get_type_hints](https://docs.python.org/3/library/typing.html#typing.get_type_hints)
    """
    hints = get_type_hints(item)
    if isinstance(item, type):
        for parent in reversed(item.__mro__):
            for name, value in getattr(parent, "__dict__", {}).items():
                if name in hints or name.startswith("__"):
                    continue
                if value is not None:
                    hints[name] = type(value)
                else:
                    hints[name] = Any
    else:
        result = {}
        for param in signature(item).parameters.values():
            result[param.name] = hints.get(param.name, Any)
        result["return"] = hints.get("return", None)
        return result
    return hints


### Type Check ###


def is_type(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is of a type compatible with `kind`."""
    if kind is Any:
        return True
    if kind in (Never, NoReturn):
        return False
    if kind in (None, NoneType):
        return value is None

    origin = get_origin(kind) or kind
    args = get_args(kind)
    if origin is Literal:
        return value in args
    if origin in (Union, UnionType):
        return any(is_type(value, vt) for vt in args)
    # all special forms handled

    if origin is not Any and not isinstance(value, origin):  # different containers
        return False

    if origin in (list, set, dict) and len(value) == 0:
        return True  # empty mutable containers match

    if origin in (list, set):
        vt = args[0] if args else Any
        return all(is_type(v, vt) for v in value)

    if origin is dict:
        kt, vt = args if args else (Any, Any)
        return all(is_type(k, kt) and is_type(v, vt) for k, v in value.items())

    if origin is tuple:
        if len(args) == 0 or args == ((),):  # special empty-tuple format
            return value is tuple()
        if len(args) > 1 and args[1] == ...:
            args = args[:1] * len(value)
        return len(value) == len(args) and all(
            is_type(v, vt) for v, vt in zip(value, args)
        )

    return isinstance(value, cast(type, kind))


### Casting ###


def to_type(value: Any, kind: TypeForm[T], casts: Casts | None = None) -> T:
    """Try to cast `value` to the type of `kind`."""
    if is_type(value, kind):  # already done
        return cast(T, value)

    casts = casts or TYPE_CASTS
    src: type[T] = get_origin_type(value)
    caster: Union[Callable[[Any], T], None] = get_converters(src, kind, casts)
    try:
        if caster:
            return caster(value)
        return to_class(value, cast(type[T], kind), casts)
    except Exception as e:
        raise TypeError(f"Cannot cast {value!r} to {kind}") from e


def get_converters(
    src: TypeForm[T], dest: TypeForm[K], casts: Casts | None = None
) -> Callable[[Any], T] | None:
    casts = casts or TYPE_CASTS

    def _wrap(
        f: CastFn[Any], t: TypeForm[F], casts: Casts | None
    ) -> Callable[[Any], F]:
        if isinstance(f, BuiltinFunctionType):
            arity = 1
        else:
            arity = len(signature(f).parameters)

        def _result(v: Any) -> F:
            if arity == 1:  # f is short-form
                f1 = cast(CastFnShort, f)
                return cast(F, f1(v))
            f2 = cast(CastFnLong[F], f)
            return f2(v, t, casts)

        return _result

    dest_origin: type[K] = get_origin_type(dest)
    for left, right in [
        (src, dest),
        (src, dest_origin),
        (Any, dest),
        (Any, dest_origin),
    ]:
        if caster := casts.get((left, right)):
            return _wrap(caster, dest, casts)

    return None


def set_converter(src: TypeForm[T], to: TypeForm[K], func: CastFn[Any]) -> CastFn[Any]:
    """Set the type-caster from `src` to `dest`"""
    TYPE_CASTS[(src, to)] = func
    return func


def converts(src: TypeForm[T], to: TypeForm[K]) -> Callable[[F], F]:
    """Define a type-caster from a `src` type to a `dest` type."""

    def _factory(func: F) -> F:
        set_converter(src, to, cast(CastFn[Any], func))
        return func

    return _factory


@converts(Any, Any)
def to_any(value: T) -> T:
    """Always return `value`."""
    return value


@converts(Any, Never)
@converts(Any, NoReturn)
def to_never(value: Any) -> NoReturn:
    """Always raise a `TypeError`."""
    raise TypeError(f"Cannot cast {value!r} to Never (nothing can)")


@converts(Any, NoneType)
def to_none(value: Ignored = None) -> None:
    """Always return `None`."""
    return None


@converts(Any, Literal)
def to_literal(
    value: T,
    kind: TypeForm[T],
    casts: Casts | None = None,
) -> T:
    """Return `value` if it is one of the `Literal` values."""
    if is_type(value, kind):
        return value
    raise TypeError(f"Cannot cast {value!r} to {kind}")


@converts(Any, Union)
@converts(Any, UnionType)
def to_union(
    value: Any,
    kind: TypeForm[T],
    casts: Casts | None = None,
) -> T:
    for arg in get_args(kind):
        try:
            return cast(T, to_type(value, arg, casts))
        except (TypeError, ValueError):
            pass
    raise TypeError(f"Cannot cast {value!r} to {kind}")


@converts(str, int)
def str_to_int(value: str) -> int:
    """Cast `value` into an `int`."""
    try:
        return int(value)
    except ValueError:
        return int(float(value))


@converts(Any, bytes)
def to_bytes(
    value: Any,
    kind: type[bytes] = bytes,
    casts: Casts | None = None,
) -> bytes:
    """Cast `value` into `bytes`, encoding `str` with a default encoding if needed."""
    if isinstance(value, str):
        return value.encode(DEFAULT_ENCODING)
    cls: type[bytes] = get_origin_type(kind)
    return cls(value)


@converts(Any, str)
def to_str(
    value: Any,
    kind: type[str] = str,
    casts: Casts | None = None,
) -> str:
    """Cast `value` into `str`, decoding `bytes` with a default encoding if needed."""
    if isinstance(value, bytes):
        return value.decode(DEFAULT_ENCODING)
    cls: type[str] = get_origin_type(kind)
    return cls(value)


@converts(Any, list)
def to_list(
    value: Any,
    kind: type[list[T]] = list,
    casts: Casts | None = None,
) -> list[T]:
    """Cast `value` into `list`."""
    cls: type[list[T]] = get_origin_type(kind)
    args = get_args(kind)
    val_type = args[0] if args else Any
    return cls(to_type(val, val_type, casts) for val in value)


@converts(Any, set)
def to_set(
    value: Any,
    kind: type[set[T]] = set,
    casts: Casts | None = None,
) -> set[T]:
    """Cast `value` into `set`."""
    cls: type[set[T]] = get_origin_type(kind)
    args = get_args(kind)
    val_type = args[0] if args else Any
    return cls(to_type(val, val_type, casts) for val in value)


@converts(Any, dict)
def to_dict(
    value: Any,
    kind: type[dict[K, T]] = dict,
    casts: Casts | None = None,
) -> dict[K, T]:
    """Cast `value` into a `dict`."""
    cls: type[dict[K, T]] = get_origin_type(kind)
    if len(value) == 0:
        return cls()
    args = get_args(kind)
    key_type, val_type = args if args else (Any, Any)
    return cls(
        {
            to_type(k, key_type, casts): to_type(v, val_type, casts)
            for k, v in value.items()
        }
    )


@converts(Any, tuple)
def to_tuple(
    value: Any,
    kind: type[tuple[Any, ...]] = tuple,
    casts: Casts | None = None,
) -> tuple[Any, ...]:
    """Cast `value` into a `tuple`."""
    cls: type[tuple[Any, ...]] = get_origin_type(kind)
    args = get_args(kind)
    if (not value or len(value) == 0) and len(args) == 0 or args == ((),):
        return cls()
    if len(args) > 1 and args[1] == ...:  # by definition
        args = args[:1] * len(value)
    if len(value) != len(args):
        raise ValueError(f"Different lengths when casting {value!r} to {kind}")
    return cls(to_type(val, val_type, casts) for val, val_type in zip(value, args))


set_converter(float, datetime, datetime.fromtimestamp)
set_converter(int, datetime, datetime.fromtimestamp)
set_converter(str, datetime, datetime.fromisoformat)


@converts(Any, datetime)
def to_datetime(value: Any) -> datetime:
    """Cast `value` into a `datetime`."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, (list, tuple)):  # try to unpack values
        return datetime(*value)  # type: ignore
    if isinstance(value, dict):
        return datetime(**value)  # type: ignore
    raise ValueError(f"Cannot cast {value!r} into datetime")


def to_class(
    value: Any,
    kind: type[T],
    casts: Casts | None = None,
) -> T:
    """Cast `value` to an instance of `kind`."""
    cls: type[T] = get_origin_type(kind)
    if isinstance(value, dict):
        hints = get_types(cls)
        data: dict[str, Any] = {
            name: to_type(value.get(name, hint), hint, casts)
            for name, hint in hints.items()
        }
        if is_dataclass(cls):
            return cast(T, cls(**data))
        else:
            return setattrs(cls(), **data)

    # try passing it to the constructor
    return cls(value)  # type: ignore[call-arg]


def castfit(
    spec: type[T],
    data: dict[str, Any],
    *,
    casts: Casts | None = None,
) -> T:
    """Construct a `spec` using `data` that has been cast appropriately."""
    return to_class(data, spec, casts)
