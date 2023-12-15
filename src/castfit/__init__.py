"""Basic type casting.

.. include:: ../../README.md
   :start-line: 4
"""

# std
from __future__ import annotations
from dataclasses import is_dataclass
from datetime import datetime
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import get_args
from typing import get_origin
from typing import get_type_hints
from typing import List
from typing import Literal
from typing import NoReturn
from typing import Optional
from typing import overload
from typing import Set
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union
import sys

if sys.version_info >= (3, 11):  # pragma: no cover
    from types import NoneType
    from typing import Never
else:
    NoneType = type(None)
    Never = NoReturn


__version__ = "0.1.0"
__pubdate__ = "2023-12-15T00:43:07Z"

K = TypeVar("K")
"""Type variable for keys."""

T = TypeVar("T")
"""Type variable for values."""

Ignored = Optional[Any]
"""A function argument that is ignored."""

TypeForm = Union[Type[T], Any]
"""`Type` and special forms like `All`, `Union`, etc."""
# NOTE: We want just `Type[T]`, but `mypy` treats special forms as `object`.

CheckFn = Callable[[Any, TypeForm[Any]], bool]
Checks = Dict[TypeForm[Any], CheckFn]
TYPE_CHECKS: Checks = {}

CastFn = Callable[[Any, TypeForm[T]], T]
Casts = Dict[TypeForm[Any], CastFn[Any]]
TYPE_CASTS: Casts = {}


@overload
def castfit(spec: Type[T], data: Dict[str, Any]) -> T:
    ...


@overload
def castfit(spec: T, data: Dict[str, Any]) -> T:
    ...


def castfit(spec, data):  # type: ignore[no-untyped-def]
    """Construct a `spec` using `data` that has been cast appropriately."""
    type_hints = get_type_hints(spec)
    typed_data: Dict[str, Any] = {
        name: to_type(value, type_hints.get(name, Any)) for name, value in data.items()
    }
    if is_dataclass(spec) and isinstance(spec, type):
        return spec(**typed_data)

    result = spec
    if isinstance(spec, type):
        result = spec()
    return setattrs(result, **typed_data)


def is_type(value: Any, kind: TypeForm[Any], checks: Optional[Checks] = None) -> bool:
    """Return `True` if `value` is of a type compatible with `kind`."""
    # TODO [2024-10-14]: @ py3.8 EOL, make return type `TypeGuard[T]`
    checks = checks or TYPE_CHECKS
    origin = get_origin(kind) or kind
    checker = checks.get(origin)
    if checker:
        return checker(value, kind)
    return isinstance(value, kind)


def to_type(
    value: Any,
    kind: TypeForm[T],
    checks: Optional[Checks] = None,
    casts: Optional[Casts] = None,
) -> T:
    """Try to cast `value` to the type of `kind`."""
    checks = checks or TYPE_CHECKS
    if is_type(value, kind, checks):  # already done
        return cast(T, value)

    casts = casts or TYPE_CASTS
    origin = get_origin(kind) or kind
    caster = casts.get(origin)
    if caster:
        return cast(T, caster(value, kind))

    try:
        return cast(T, origin(value))  # type: ignore[call-arg]
    except Exception:
        raise TypeError(f"Cannot cast {value!r} to {kind}")


def get_origin_type(given: TypeForm[T]) -> Type[T]:
    """Returns the `given` type, its origin, or `type(obj)`.

    See: [typing.get_origin](https://docs.python.org/3/library/typing.html#typing.get_origin)
    """
    origin = get_origin(given) or given
    if isinstance(origin, type):
        return cast(Type[T], origin)  # cast due to mypy
    return cast(Type[T], type(given))  # cast due to mypy


def setattrs(obj: object, **values: Dict[str, Any]) -> object:
    """Like `setattr()` but for multiple values and returns the object."""
    for name, val in values.items():
        setattr(obj, name, val)
    return obj


def checks_type(*types: Any) -> Callable[[CheckFn], CheckFn]:
    """Define a type-checker for one or more types."""

    def _factory(func: CheckFn) -> CheckFn:
        for t in types:
            TYPE_CHECKS[t] = func
        return func

    return _factory


def casts_to(*types: Any) -> Callable[[T], T]:
    """Define a type-caster for one or more types."""

    def _factory(func: T) -> T:
        for t in types:
            TYPE_CASTS[t] = cast(CastFn[Any], func)
        return func

    return _factory


@checks_type(Any)
def is_any(_value: Ignored = None, _kind: Ignored = Any) -> bool:
    """Always return `True`."""
    return True


@casts_to(Any)
def to_any(value: T, _kind: Ignored = Any) -> T:
    """Always return `value`."""
    return value


@checks_type(Never, NoReturn)
def is_never(_value: Ignored = None, _kind: Ignored = Never) -> bool:
    """Always return `False`."""
    return False


@casts_to(Never, NoReturn)
def to_never(value: Any, _kind: Ignored = Never) -> NoReturn:
    """Always raise a `TypeError`."""
    raise TypeError(f"Cannot cast {value!r} to Never (nothing can)")


@checks_type(NoneType)
def is_none(value: Any, _kind: Ignored = None) -> bool:
    """Return `True` if `value` is `None`."""
    return value is None


@casts_to(NoneType)
def to_none(_value: Ignored = None, _kind: Ignored = None) -> None:
    """Always return `None`."""
    return None


@checks_type(Literal)
def is_literal(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is a valid `Literal`."""
    return value in get_args(kind)


@casts_to(Literal)
def to_literal(value: T, kind: TypeForm[T]) -> T:
    """Return `value` if it is one of the `Literal` values."""
    if not is_literal(value, kind):
        raise TypeError(f"Cannot cast {value!r} to {kind}")
    return value


@checks_type(Union)
def is_union(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is a valid `Union`."""
    return any(is_type(value, val_type) for val_type in get_args(kind))


@casts_to(Union)
def to_union(value: Any, kind: TypeForm[T]) -> T:
    for arg in get_args(kind):
        try:
            return cast(T, to_type(value, arg))
        except (TypeError, ValueError):
            pass
    raise TypeError(f"Cannot cast {value!r} to {kind}")


@casts_to(bytes)
def to_bytes(value: Any, kind: Type[bytes] = bytes) -> bytes:
    """Cast `value` into `bytes`, encoding `str` as UTF-8 bytes if needed."""
    if isinstance(value, str):
        return value.encode("utf-8")
    cls: Type[bytes] = get_origin_type(kind)
    return cls(value)


@casts_to(str)
def to_str(value: Any, kind: Type[str] = str) -> str:
    """Cast `value` into `str`, decoding `bytes` as UTF-8 strings if needed."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    cls: Type[str] = get_origin_type(kind)
    return cls(value)


@checks_type(list)
def is_list(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is a valid `list`."""
    if not isinstance(value, list):
        return False
    if len(value) == 0:  # list() matches List[Any]
        return True
    vt = get_args(kind)[0]
    return all(is_type(v, vt) for v in value)


@casts_to(list)
def to_list(value: Any, kind: TypeForm[List[T]] = list) -> List[T]:
    """Cast `value` into `list`."""
    cls: Type[List[T]] = get_origin_type(kind)
    val_type = get_args(kind)[0]
    return cls(to_type(val, val_type) for val in value)


@checks_type(set)
def is_set(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is a valid `set`."""
    if not isinstance(value, set):
        return False
    if len(value) == 0:  # set() matches Set[Any]
        return True
    val_type = get_args(kind)[0]
    return all(is_type(val, val_type) for val in value)


@casts_to(set)
def to_set(value: Any, kind: TypeForm[Set[T]] = set) -> Set[T]:
    """Cast `value` into `set`."""
    cls: Type[Set[T]] = get_origin_type(kind)
    val_type = get_args(kind)[0]
    return cls(to_type(val, val_type) for val in value)


@checks_type(dict)
def is_dict(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is a valid `dict`."""
    if not isinstance(value, dict):
        return False
    if len(value) == 0:  # dict() matches Dict[Any, Any]
        return True
    kt, vt = get_args(kind)
    return all(is_type(k, kt) and is_type(v, vt) for k, v in value.items())


@casts_to(dict)
def to_dict(value: Any, kind: TypeForm[Dict[K, T]] = dict) -> Dict[K, T]:
    """Cast `value` into a `dict`."""
    cls: Type[Dict[K, T]] = get_origin_type(kind)
    if len(value) == 0:
        return cls()
    kt, vt = get_args(kind)
    return cls({to_type(k, kt): to_type(v, vt) for k, v in value.items()})


@checks_type(tuple)
def is_tuple(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is a valid `tuple`."""
    args = get_args(kind)
    if not isinstance(value, tuple):
        return False
    if len(args) == 0 or args == ((),):  # special empty-tuple format
        return value == ()
    if len(args) > 1 and args[1] == ...:
        args = args[:1] * len(value)
    return len(value) == len(args) and all(is_type(v, vt) for v, vt in zip(value, args))


@casts_to(tuple)
def to_tuple(value: Any, kind: TypeForm[Tuple[Any, ...]] = tuple) -> Tuple[Any, ...]:
    """Cast `value` into a `tuple`."""
    cls: Type[Tuple[Any, ...]] = get_origin_type(kind)
    args = get_args(kind)
    if len(value) == 0 and len(args) == 0 or args == ((),):
        return cls()
    if len(args) > 1 and args[1] == ...:
        args = args[:1] * len(value)
    if len(value) < len(args):
        raise ValueError(f"Not enough values in {value!r} to cast to {kind}")
    return cls(to_type(val, val_type) for val, val_type in zip(value, args))


@casts_to(datetime)
def to_datetime(value: Any, kind: Type[datetime] = datetime) -> datetime:
    """Cast `value` into a `datetime`."""
    cls: Type[datetime] = get_origin_type(kind)
    # TODO: Handle other kinds of casts (e.g., int -> datetime)
    return cls.fromisoformat(value)
