"""castfit: basic type casting

.. include:: ../../README.md
   :start-line: 2
"""

# std
from __future__ import annotations
from collections.abc import Callable as Callable2
from dataclasses import is_dataclass
from datetime import datetime
from inspect import signature
from types import FunctionType
from types import LambdaType
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
    "is_subtype",
    #
    # extensions
    "checks_type",
    "converts",
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

F = TypeVar("F")
"""Type variable for functions."""

K = TypeVar("K")
"""Type variable for keys."""

T = TypeVar("T")
"""Type variable for values."""

Ignored = Optional[Any]
"""A function argument that is ignored."""

GenericLiteral = type(Literal[Any])
"""Type of a generic `Literal`."""

GenericUnion = (type(Union[str, int]), UnionType)
"""Type of a generic `Union`."""

GenericFunction = (FunctionType, LambdaType)
"""Type of function."""

SPECIAL_FORMS = (Any, Never, NoReturn, NoneType, Literal, Union, UnionType)
"""Special forms."""

# TypeForm = Union[type[T], type, type(Any), type(Union), UnionType, _SpecialForm]
TypeForm = Union[type[T], Any]
"""`Type` and special forms like `Any`, `Union`, etc."""
# NOTE: We want `type[T] | _SpecialForm` but type checkers can't handle it.

CheckFn = Callable[[Any, TypeForm[T], "Checks | None"], bool]
"""Function signature that checks if a value is of a type."""

Checks = dict[TypeForm[Any], CheckFn[Any]]
"""Type of internal mapping of types to check functions."""

TYPE_CHECKS: Checks = {}
"""Mapping of types to check functions."""

CastFnShort = Callable[[Any], Any]
"""Function signature for a simple caster."""

CastFnLong = Callable[[Any, TypeForm[T], "Checks | None", "Casts | None"], T]
"""Function signature for a full caster."""

CastFn = Union[CastFnShort, CastFnLong[T]]
"""Function signature that maps a value to a type."""

Casts = dict[tuple[TypeForm[Any], TypeForm[Any]], CastFn[Any]]
"""Type of internal mapping of types to cast functions."""

TYPE_CASTS: Casts = {}
"""Mapping of types to cast functions."""

### Utilities ###


def setattrs(obj: T, **values: dict[str, Any]) -> T:
    """Like `setattr()` but for multiple values and returns the object."""
    for name, val in values.items():
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


def get_types(item: type[T] | FunctionType | LambdaType) -> dict[str, Any]:
    """Returns names and inferred types for `item`.

    See: [typing.get_type_hints](https://docs.python.org/3/library/typing.html#typing.get_type_hints)
    """
    hints = get_type_hints(item)
    if isinstance(item, GenericFunction):
        result = {}
        for param in signature(item).parameters.values():
            result[param.name] = hints.get(param.name, Any)
        result["return"] = hints.get("return", None)
        return result

    # type
    for parent in reversed(item.__mro__):
        for name, value in getattr(parent, "__dict__", {}).items():
            if name in hints or name.startswith("__"):
                continue
            if value is not None:
                hints[name] = type(value)
            else:
                hints[name] = Any
    return hints


### Type Check ###


def is_type(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` is of a type compatible with `kind`."""
    checks = checks or TYPE_CHECKS
    origin = get_origin(kind) or kind
    if checker := checks.get(origin):
        return checker(value, kind, checks)
    return isinstance(value, cast(type, kind))


def is_subtype(t1: TypeForm[T], t2: TypeForm[K]) -> bool:
    """Return `True` if `t1` is a subtype of `t1`, `False` otherwise.

    Extends `issubclass` to `Any`, `Never`, `NoneType`, `Literal`, `Union`.
    """
    if t2 is Any:
        return True
    if t2 in (Never, NoReturn):
        return False
    if t2 is NoneType:
        return t1 in (None, NoneType)

    type1, type2 = type(t1), type(t2)
    args1, args2 = get_args(t1), get_args(t2)

    if type2 is GenericLiteral:
        return type1 is GenericLiteral and set(args1).issubset(args2)
    if type1 is GenericLiteral:
        return all(is_type(arg, t2) for arg in args1)

    if type2 in GenericUnion:
        return t1 in args2 or type1 in GenericUnion and set(args1).issubset(args2)

    if args1 or args2:  # generics
        origin1, origin2 = get_origin(t1), get_origin(t2)
        return (
            len(args1) == len(args2)
            and is_subtype(origin1, origin2)
            and all(is_subtype(x, y) for x, y in zip(args1, args2))
        )

    return t1 is t2 or issubclass(t1, t2)


def checks_type(*types: Any) -> Callable[[F], F]:
    """Define a type-checker for one or more types."""

    def _factory(func: F) -> F:
        for t in types:
            TYPE_CHECKS[t] = cast(CheckFn[Any], func)
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


@checks_type(Callable, Callable2)
def is_callable(value: Any, kind: TypeForm[T], checks: Checks | None = None) -> bool:
    """Return `True` if `value` matches the type signature of `kind`."""
    if not callable(value):
        return False
    args = get_args(kind)
    hints = get_types(cast(FunctionType, value))
    return_type = hints.pop("return")
    if not is_subtype(return_type, args[1]):
        return False
    if args[0] is Ellipsis:  # don't check args
        return True
    if len(args[0]) != len(hints):
        return False
    for (name, have), want in zip(hints.items(), args[0]):
        if not is_subtype(have, want):
            return False
    return True


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
    src: type[T] = get_origin_type(value)
    caster: Union[Callable[[Any], T], None] = get_converters(src, kind, checks, casts)
    try:
        if caster:
            return caster(value)
        return to_class(value, cast(type[T], kind), checks, casts)
    except Exception as e:
        raise TypeError(f"Cannot cast {value!r} to {kind}") from e


def converts(src: TypeForm[T], dest: TypeForm[K]) -> Callable[[F], F]:
    """Define a type-caster from a `src` type to a `dest` type."""

    def _factory(func: F) -> F:
        TYPE_CASTS[(src, dest)] = cast(CastFn[Any], func)
        return func

    return _factory


def get_converters(
    src: TypeForm[T],
    dest: TypeForm[K],
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> Callable[[Any], T] | None:
    casts = casts or TYPE_CASTS

    def _wrap(
        f: CastFn[Any], t: TypeForm[F], checks: Checks | None, casts: Casts | None
    ) -> Callable[[Any], F]:
        arity = len(signature(f).parameters)

        def _result(v: Any) -> F:
            if arity == 1:
                f1 = cast(CastFnShort, f)
                return cast(F, f1(v))
            f2 = cast(CastFnLong[F], f)
            return f2(v, t, checks, casts)

        return _result

    dest_origin: type[K] = get_origin_type(dest)
    for left, right in [
        (src, dest),
        (src, dest_origin),
        (Any, dest),
        (Any, dest_origin),
    ]:
        if caster := casts.get((left, right)):
            return _wrap(caster, dest, checks, casts)

    return None


@converts(Any, Any)
def to_any(
    value: T,
    kind: Ignored = Any,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> T:
    """Always return `value`."""
    return value


@converts(Any, Never)
@converts(Any, NoReturn)
def to_never(
    value: Any,
    kind: Ignored = Never,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> NoReturn:
    """Always raise a `TypeError`."""
    raise TypeError(f"Cannot cast {value!r} to Never (nothing can)")


@converts(Any, NoneType)
def to_none(
    value: Ignored = None,
    kind: Ignored = None,
    checks: Checks | None = None,
    casts: Casts | None = None,
) -> None:
    """Always return `None`."""
    return None


@converts(Any, Literal)
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


@converts(Any, Union)
@converts(Any, UnionType)
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


@converts(Any, bytes)
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


@converts(Any, str)
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


@converts(Any, list)
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


@converts(Any, set)
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


@converts(Any, dict)
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


@converts(Any, tuple)
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


@converts(Any, datetime)
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
