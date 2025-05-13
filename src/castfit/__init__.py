"""castfit: basic type casting

.. include:: ../../README.md
   :start-line: 2
"""

# std
from __future__ import annotations
from dataclasses import is_dataclass
from datetime import datetime
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


# TODO 2025-10-31 @ py3.9 EOL: move imports above
if sys.version_info >= (3, 10):  # pragma: no cover
    from types import NoneType
    from types import UnionType
else:  # pragma: no cover
    NoneType = type(None)  # same as `types.NoneType`
    UnionType = Union  # workaround

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
    #
    # types
    "Ignored",
    "TypeForm",
    "CheckFn",
    "Checks",
    "CastFn",
    "Casts",
    #
    # top-level API
    "castfit",
    "is_type",
    "to_type",
    #
    # extensions
    "checks_type",
    "casts_to",
    #
    # lower-level API
    "get_origin_type",
    "setattrs",
    "is_any",
    "to_any",
    "is_never",
    "to_never",
    "is_none",
    "to_none",
    "is_literal",
    "to_literal",
    "is_union",
    "to_union",
    "to_bytes",
    "to_str",
    "is_list",
    "to_list",
    "is_set",
    "to_set",
    "is_dict",
    "to_dict",
    "is_tuple",
    "to_tuple",
    "to_datetime",
]

__version__ = "0.1.1"
__pubdate__ = "2025-04-28T14:32:37Z"

DEFAULT_ENCODING = "utf-8"
"""Default file encoding."""

K = TypeVar("K")
"""Type variable for keys."""

T = TypeVar("T")
"""Type variable for values."""

Ignored = Optional[Any]
"""A function argument that is ignored."""

TypeForm = Union[type[T], Any]
"""`Type` and special forms like `Any`, `Union`, etc."""
# NOTE: We have a union with `Any` instead of `_SpecialForm` because
# neither pyright nor mypy can handle `_SpecialForm`.

CheckFn = Callable[[Any, TypeForm[T], "Checks | None"], bool]
"""Function signature that checks if a value is of a type."""

Checks = dict[TypeForm[Any], CheckFn[Any]]
"""Type of internal mapping of types to check functions."""

TYPE_CHECKS: Checks = {}
"""Mapping of types to check functions."""

CastFn = Callable[[Any, TypeForm[T], "Checks | None", "Casts | None"], T]
"""Function signature that maps a value to a type."""

Casts = dict[TypeForm[Any], CastFn[Any]]
"""Type of internal mapping of types to cast functions."""

TYPE_CASTS: Casts = {}
"""Mapping of types to cast functions."""

### Type Check ###


def is_type(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is of a type compatible with `kind`."""
    checks = checks or TYPE_CHECKS
    origin = get_origin(kind) or kind
    checker = checks.get(origin)
    if checker:
        return checker(value, kind, checks)
    return isinstance(value, kind)


def checks_type(*types: Any) -> Callable[[CheckFn[Any]], CheckFn[Any]]:
    """Define a type-checker for one or more types."""

    def _factory(func: CheckFn[Any]) -> CheckFn[Any]:
        for t in types:
            TYPE_CHECKS[t] = func
        return func

    return _factory


@checks_type(Any)
def is_any(value: Any, kind: TypeForm[T] = Any, checks: Checks | None = None) -> bool:
    """Always return `True`."""
    return True


@checks_type(Never, NoReturn)
def is_never(
    value: Any, kind: TypeForm[T] = Never, checks: Checks | None = None
) -> bool:
    """Always return `False`."""
    return False


@checks_type(NoneType)
def is_none(
    value: Any, kind: TypeForm[T] = NoneType, checks: Checks | None = None
) -> bool:
    """Return `True` if `value` is `None`."""
    return value is None


@checks_type(Literal)
def is_literal(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is a valid `Literal`."""
    return value in get_args(kind)


@checks_type(Union, UnionType)
def is_union(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is a valid `Union`."""
    return any(is_type(value, val_type, checks=checks) for val_type in get_args(kind))


@checks_type(list)
def is_list(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is a valid `list`."""
    if not isinstance(value, list):
        return False
    if len(value) == 0:  # list() matches list[Any]
        return True
    args = get_args(kind)
    val_type = args[0] if args else Any
    return all(is_type(val, val_type, checks=checks) for val in value)


@checks_type(set)
def is_set(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is a valid `set`."""
    if not isinstance(value, set):
        return False
    if len(value) == 0:  # set() matches set[Any]
        return True
    args = get_args(kind)
    val_type = args[0] if args else Any
    return all(is_type(val, val_type, checks=checks) for val in value)


@checks_type(dict)
def is_dict(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is a valid `dict`."""
    if not isinstance(value, dict):
        return False
    if len(value) == 0:  # dict() matches dict[Any, Any]
        return True
    args = get_args(kind)
    key_type, val_type = args if args else (Any, Any)
    return all(
        is_type(k, key_type, checks=checks) and is_type(v, val_type, checks=checks)
        for k, v in value.items()
    )


@checks_type(tuple)
def is_tuple(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is a valid `tuple`."""
    args = get_args(kind)
    if not isinstance(value, tuple):
        return False
    if len(args) == 0 or args == ((),):  # special empty-tuple format
        return value == ()
    if len(args) > 1 and args[1] == ...:
        args = args[:1] * len(value)
    return len(value) == len(args) and all(
        is_type(v, vt, checks=checks) for v, vt in zip(value, args)
    )


### Casting ###


def to_type(
    value: Any,
    kind: TypeForm[T],
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> T:
    """Try to cast `value` to the type of `kind`."""
    checks = checks or TYPE_CHECKS
    if is_type(value, kind, checks):  # already done
        return cast(T, value)

    casts = casts or TYPE_CASTS
    origin: type[T] = get_origin(kind) or kind
    caster = casts.get(origin)
    try:
        if caster:
            print(caster)
            return cast(T, caster(value, kind, checks, casts))
        return cast(T, to_class(value, kind, checks, casts))
    except Exception as e:
        raise TypeError(f"Cannot cast {value!r} to {kind}") from e


def set_caster(src: TypeForm[T], dest: TypeForm[K], fn: CastFn[Any]) -> CastFn[Any]:
    """Define a type-caster for converting from `src` to `dest`."""
    TYPE_CASTS[dest] = fn
    return fn


def casts_to(*types: Any) -> Callable[[T], T]:
    """Define a type-caster for one or more types."""

    def _factory(func: T) -> T:
        for t in types:
            set_caster(Any, t, cast(CastFn[T], func))
        return func

    return _factory


def casting(src: Any, dest: Any) -> Callable[[T], T]:
    def _factory(func: T) -> T:
        set_caster(src, dest, cast(CastFn[T], func))
        return func

    return _factory


def get_origin_type(given: TypeForm[T] | T) -> type[T]:
    """Returns the `given` type, its origin, or `type(obj)`.

    See: [typing.get_origin](https://docs.python.org/3/library/typing.html#typing.get_origin)
    """
    origin = get_origin(given) or given
    if isinstance(origin, type):
        return cast(type[T], origin)  # cast due to mypy
    return cast(type[T], type(given))  # cast due to mypy


def get_types(cls: type[T]) -> dict[str, Any]:
    """Returns field names and inferred types for `given`.

    See: [typing.get_type_hints](https://docs.python.org/3/library/typing.html#typing.get_type_hints)
    """
    hints = get_type_hints(cls)
    for parent in reversed(cls.__mro__):
        for name, value in getattr(cls, "__dict__", {}).items():
            if name in hints or name.startswith("__"):
                continue
            if value is not None:
                hints[name] = type(value)
            else:
                hints[name] = Any
    return hints


# @casts_to(Any)
@casting(Any, Any)
def to_any(
    value: T,
    kind: Ignored = Any,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> T:
    """Always return `value`."""
    return value


@casts_to(Never, NoReturn)
def to_never(
    value: Any,
    kind: Ignored = Never,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> NoReturn:
    """Always raise a `TypeError`."""
    raise TypeError(f"Cannot cast {value!r} to Never (nothing can)")


@casts_to(NoneType)
def to_none(
    value: Ignored = None,
    kind: Ignored = None,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> None:
    """Always return `None`."""
    return None


@casts_to(Literal)
def to_literal(
    value: T,
    kind: TypeForm[T],
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> T:
    """Return `value` if it is one of the `Literal` values."""
    if is_literal(value, kind, checks):
        return value
    raise TypeError(f"Cannot cast {value!r} to {kind}")


@casts_to(Union, UnionType)
def to_union(
    value: Any,
    kind: TypeForm[T],
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> T:
    for arg in get_args(kind):
        try:
            return cast(T, to_type(value, arg, checks=checks, casts=casts))
        except (TypeError, ValueError):
            pass
    raise TypeError(f"Cannot cast {value!r} to {kind}")


@casts_to(bytes)
def to_bytes(
    value: Any,
    kind: type[bytes] = bytes,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> bytes:
    """Cast `value` into `bytes`, encoding `str` with a default encoding if needed."""
    if isinstance(value, str):
        return value.encode(DEFAULT_ENCODING)
    cls: type[bytes] = get_origin_type(kind)
    return cls(value)


@casts_to(str)
def to_str(
    value: Any,
    kind: type[str] = str,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> str:
    """Cast `value` into `str`, decoding `bytes` with a default encoding if needed."""
    if isinstance(value, bytes):
        return value.decode(DEFAULT_ENCODING)
    cls: type[str] = get_origin_type(kind)
    return cls(value)


@casts_to(list)
def to_list(
    value: Any,
    kind: type[list[T]] = list,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> list[T]:
    """Cast `value` into `list`."""
    cls: type[list[T]] = get_origin_type(kind)
    args = get_args(kind)
    val_type = args[0] if args else Any
    return cls(to_type(val, val_type, checks=checks, casts=casts) for val in value)


@casts_to(set)
def to_set(
    value: Any,
    kind: type[set[T]] = set,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> set[T]:
    """Cast `value` into `set`."""
    cls: type[set[T]] = get_origin_type(kind)
    args = get_args(kind)
    val_type = args[0] if args else Any
    return cls(to_type(val, val_type, checks=checks, casts=casts) for val in value)


@casts_to(dict)
def to_dict(
    value: Any,
    kind: type[dict[K, T]] = dict,
    checks: Checks | None = None,
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
            to_type(k, key_type, checks=checks, casts=casts): to_type(
                v, val_type, checks=checks, casts=casts
            )
            for k, v in value.items()
        }
    )


@casts_to(tuple)
def to_tuple(
    value: Any,
    kind: type[tuple[Any, ...]] = tuple,
    checks: Checks | None = None,
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
    return cls(
        to_type(val, val_type, checks=checks, casts=casts)
        for val, val_type in zip(value, args)
    )


@casts_to(datetime)
def to_datetime(
    value: Any,
    kind: type[datetime] = datetime,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> datetime:
    """Cast `value` into a `datetime`."""
    cls: type[datetime] = get_origin_type(kind)
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return cls.fromtimestamp(value)
    if isinstance(value, str):
        return cls.fromisoformat(value)
    if isinstance(value, (list, tuple)):  # try to unpack values
        return cls(*value)
    if isinstance(value, dict):
        return cls(**value)
    raise ValueError(f"Cannot parse {value!r} into {kind}")


def setattrs(obj: T, **values: dict[str, Any]) -> T:
    """Like `setattr()` but for multiple values and returns the object."""
    for name, val in values.items():
        setattr(obj, name, val)
    return obj


def to_class(
    value: Any,
    kind: type[T],
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> T:
    """Cast `value` to an instance of `kind`."""
    cls: type[T] = get_origin_type(kind)
    if isinstance(value, dict):
        hints = get_types(cls)
        data: dict[str, Any] = {
            name: to_type(value.get(name, hint), hint, checks=checks, casts=casts)
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
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> T:
    """Construct a `spec` using `data` that has been cast appropriately."""
    return to_class(data, spec, checks=checks, casts=casts)
