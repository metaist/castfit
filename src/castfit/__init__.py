"""castfit: basic type casting

.. include:: ../../README.md
   :start-line: 2
"""

# std
from __future__ import annotations
from collections.abc import Callable as CallableABC
from collections.abc import Mapping as MappingABC
from collections.abc import Sequence as SequenceABC
from dataclasses import dataclass
from dataclasses import field
from dataclasses import is_dataclass
from dataclasses import replace
from datetime import datetime
from datetime import timezone
from inspect import Parameter
from inspect import signature
from types import BuiltinFunctionType
from types import FunctionType
from types import NoneType
from types import UnionType
from typing import Any
from typing import Callable
from typing import cast
from typing import get_args
from typing import get_origin
from typing import get_type_hints
from typing import Iterable
from typing import Iterator
from typing import Literal
from typing import Mapping
from typing import NoReturn
from typing import Optional
from typing import overload
from typing import Sequence
from typing import Sized
from typing import TypeVar
from typing import Union
import logging
import sys


# TODO 2026-10-31 @ py3.10 EOL: move imports above
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Never
else:  # pragma: no cover
    Never = NoReturn  # semantically same; syntactically different

# TODO 2027-10-31 @ py3.11 EOL: move imports above
if sys.version_info >= (3, 12):  # pragma: no cover
    from types import get_original_bases
else:  # pragma: no cover
    # https://github.com/python/cpython/blob/3.13/Lib/types.py#L148
    def get_original_bases(cls: type, /) -> tuple[type, ...]:
        try:
            return cls.__dict__.get("__orig_bases__", cls.__bases__)
        except AttributeError:
            raise TypeError(
                f"Expected an instance of type, not {type(cls).__name__!r}"
            ) from None


__all__ = [
    "__version__",
    "__pubdate__",
    #
    # types
    "TypeForm",
    "CastFn",
    #
    # utilities
    "iterate",
    "setkeys",
    "setattrs",
    "TypeInfo",
    "type_info",
    "type_hints",
    "is_subtype",
    #
    # top-level API
    "is_type",
    "to_type",
    "casts",
    "castfit",
    #
    # Internals
    "Never",
]

__version__ = "0.1.3"
__pubdate__ = "2025-11-27T03:12:11Z"

log = logging.getLogger(__name__)
"""Global logger."""

DEFAULT_ENCODING = "utf-8"
"""Default file encoding."""

F = TypeVar("F", bound=Callable[..., Any])
"""Type variable for functions."""

K = TypeVar("K")
"""Type variable for keys."""

T = TypeVar("T")
"""Type variable for values."""

Ignored = Optional[Any]
"""A function argument that is ignored."""

SPECIAL_FORMS = (Any, Never, NoReturn, NoneType, Literal, Union, UnionType)
"""Special forms."""

# TypeForm = Union[type[T], type(Any)]
TypeForm = Union[type[T], Any]
"""`Type` and special forms like `Any`, `Union`, etc."""
# NOTE: We want `type[T] | _SpecialForm` but type checkers can't handle it.

CastFnShort = Callable[[Any], Any]
"""Function signature for a simple caster."""

CastFnLong = Callable[[Any, TypeForm[T], Optional["Casts"]], T]
"""Function signature for a full caster."""

CastFn = Union[CastFnShort, CastFnLong[T]]
"""Function signature that maps a value to a type."""

Casts = dict[tuple[TypeForm[Any], TypeForm[Any]], CastFn[Any]]
"""Type of internal mapping of types to cast functions."""

TYPE_CASTS: Casts = {}
"""Mapping of types to cast functions."""

### Utilities ###


def iterate(*items: T | Iterable[T]) -> Iterator[T]:
    """Return an iterator over individual or collections of items.

    NOTE: Although `str` is `Iterable`, we treat it as an individual item.

    Args:
        *items (T | Iterable[T]): one or more items to be iterated

    Yields:
        T: an individual item

    Examples:

    Strings are treated like individual items.
    >>> list(iterate("hello")) == ["hello"]
    True

    Iterate over lists or individual items:
    >>> list(iterate([1, 2], 3)) == [1, 2, 3]
    True

    You can iterate over multiple lists:
    >>> list(iterate([3, 4], [5, 6])) == [3, 4, 5, 6]
    True
    """
    for item in items:
        if isinstance(item, str):
            yield cast(T, item)
        elif isinstance(item, Iterable):
            yield from item
        else:
            yield item


def setkeys(d: dict[Any, Any], *values: dict[Any, Any], **extra: Any) -> dict[Any, Any]:
    """Return `dict` that has been updated by `values` and `extra`."""
    for value in values + (extra,):
        d.update(value)
    return d


def setattrs(obj: T, *values: dict[str, Any], **extra: Any) -> T:
    """Like `setattr()` but for multiple values and returns the object."""
    for name, val in setkeys({}, *values, extra).items():
        setattr(obj, name, val)
    return obj


@dataclass(frozen=True)
class TypeInfo:
    """Type information."""

    name: str = ""
    """Name of the field or parameter."""

    hint: TypeForm[Any] = Any
    """Type hint or inferred type."""

    default: Any = Parameter.empty
    """Default value, if any."""

    origin: Any = Any
    """Type origin.

    See: [`typing.get_origin`](https://docs.python.org/3/library/typing.html#typing.get_origin)
    """

    args: tuple[Any, ...] = field(default_factory=tuple)
    """Type arguments.

    See: [`typing.get_args`](https://docs.python.org/3/library/typing.html#typing.get_args)
    """


TYPE_CACHE: dict[Any, TypeInfo] = {}
"""Type information cache used by `type_info()`."""


def type_info(item: Any, use_cache: bool = True) -> TypeInfo:
    """Return type information about `item`.

    This function is similar to `builtins.type` except that it returns an
    object that which includes additional metadata.

    When `item` has an origin, we return:

    - `origin` (from `typing.get_origin`)
    - `args` (from `typing.get_args`)

    For special forms (`Any`, `Literal`, `Union`, etc.) and classes we set
    `origin` to be the item.

    Args:
        item (Any): the value to get info about

        use_cache (bool, default=True): whether or not to lookup/store results
            in a local cache. Even when `use_cache=True` if `item` is an
            instance, `Literal`, `Union`, or `UnionType`, it will not be
            stored in the local cache.

    Returns:
        TypeInfo: `item` type information
    """
    if use_cache:
        try:
            log.debug("try to fetch from cache: %s", item)
            return TYPE_CACHE[item]
        except (KeyError, TypeError):
            pass  # missing key or `item` is unhashable

    name: str = getattr(item, "__name__", getattr(item, "_name", ""))
    args: tuple[Any, ...] = tuple()
    if origin := get_origin(item):
        log.debug("has an origin %s", origin)
        args = get_args(item)
        hint = item
        if not name:
            name = getattr(origin, "__name__", getattr(origin, "_name", ""))
    elif isinstance(item, type):
        log.debug("%s is a class", item)
        hint = item
        if bases := getattr(item, "__orig_bases__", None):
            # NOTE: We assume the first base is the relevant one.
            origin = get_origin(bases[0])
            args = get_args(bases[0])
            log.debug("%s has original base: %s with args %s", item, origin, args)
        else:
            origin = item
    elif item in SPECIAL_FORMS:
        log.debug("%s is a special form", item)
        hint = origin = item
    else:  # instance
        log.debug("%s is an instance", item)
        use_cache = False  # do not save instance information
        hint = origin = type(item)

    result = TypeInfo(name=name, hint=hint, origin=origin, args=args)
    if use_cache and origin not in (Union, UnionType, Literal):
        TYPE_CACHE[item] = result
        log.debug("saved to cache: %s", result)
    return result


def type_hints(item: type[T] | Callable[..., Any]) -> dict[str, TypeInfo]:
    """Returns names and inferred types for `item`.

    This function merges some of the behavior of `typing.get_type_hints` for
    classes and `inspect.signature` for other callables.

    Args:
        item (type[T] | Callable[..., Any]): a class, lambda, or function

    Returns:
        (dict[str, TypeInfo]): mapping of field/parameter names to hint information

    See:

    - [`typing.get_type_hints`](https://docs.python.org/3/library/typing.html#typing.get_type_hints)
    - [`inspect.signature`](https://docs.python.org/3/library/inspect.html#inspect.signature)
    """
    result = {}
    hints = get_type_hints(item)
    if isinstance(item, type):
        for parent in reversed(item.__mro__):
            for name, value in getattr(parent, "__dict__", {}).items():
                if (
                    name in result
                    or name.startswith("__")
                    or isinstance(value, (BuiltinFunctionType, FunctionType))
                ):
                    continue

                if isinstance(value, property):
                    if value.fset:
                        info = list(type_hints(value.fset).values())[1]
                    elif value.fget:
                        info = type_hints(value.fget)["return"]
                    else:  # pragma: no cover
                        continue

                    # `property` has no default
                    result[name] = replace(info, name=name, default=Parameter.empty)
                else:  # normal field
                    hint = hints.get(name, Any if value is None else type(value))
                    info = type_info(hint)
                    result[name] = replace(info, name=name, default=value)

        # get all the typed-without-default values
        for name, hint in hints.items():
            if name not in result:
                result[name] = replace(type_info(hint), name=name)

    else:  # non-class callable
        for name, param in signature(item).parameters.items():
            info = type_info(hints.get(name, Any))
            result[name] = replace(info, name=name, default=param.default)
        info = type_info(hints.get("return", Any))
        result["return"] = replace(info, name="return")
    return result


### Type Check ###

NUMERIC_TOWER = (bool, int, float, complex)
"""Numeric tower defined by PEP 3141."""


def is_subtype(
    left: TypeForm[T],
    right: TypeForm[K],
    *,
    covariant: bool = False,
    contravariant: bool = False,
    implicit: bool = True,
) -> bool:
    """Return `True` if `left` is a subtype of `right`.

    In many ways this function is an extension of `issubclass` to
    certain special forms:

    - `Any`
    - `Never`, `NoReturn`
    - `NoneType`
    - `Literal`
    - `Union`, `UnionType`
    - `Callable`
    - `Sequence`, `Mapping`, `list`, `dict`, `set`, `tuple`
    - `Generic` (using `TypeVar` to set `covariant` and `contravariant`)

    **NOTE**: This is not an exhaustive type checker.

    This function also supports variance comparisons:
        - implicit (default enabled): `left` is a numeric subtype of `right` as defined by PEP 3141
        - invariant (default enabled): `left` and `right` must match exactly (unless implicit matched first)
        - covariant (default disabled): `left` is a subclass of `right`
        - contravariant (default disabled): `left` is a superclass of `right`

    Args:
        left (TypeForm[T]): a supported type form.
        right (TypeForm[K]): a supported type form.
        covariant (bool, default=False): if `True`, `left` may be a subclass of `right`.
        contravariant (bool, default=False): if `True`, `left` may be a superclass of `right`.
        implicit (bool, default=True): if `True`, support the PEP 3141 numeric tower implicit
            conversions, even when otherwise invariant comparisons are being made.

    Returns:
        bool: `True` if `left` is a subtype of `right`, `False` otherwise.

    See:
        - [`issubclass`](https://docs.python.org/3/library/functions.html#issubclass)
        - [PEP 3141 - A Type Hierarchy for Numbers](https://peps.python.org/pep-3141/)
    """

    if covariant and contravariant:  # bivariant
        return is_subtype(left, right, covariant=True, implicit=implicit) or is_subtype(
            left, right, contravariant=True, implicit=implicit
        )
    if contravariant:
        return is_subtype(right, left, covariant=True, implicit=implicit)
    # either: invariant or covariant

    kwargs = dict(covariant=covariant, contravariant=contravariant, implicit=implicit)

    if right is Any:
        log.debug("every type is a subtype of `Any`")
        return True
    if left is Any:
        log.debug("`Any` is only a subtype of `Any`")
        return right is Any

    if right in (Never, NoReturn):  # Never is not in Never
        log.debug("no type is a subtype of `Never`")
        return False
    if left in (Never, NoReturn):  # Never is in everything else
        log.debug("`Never` is a subtype of every type")
        return True

    if right in (None, NoneType):
        log.debug("only `None|NoneType` is a subtype of `None|NoneType`")
        return left in (None, NoneType)

    if left == right:  # same type
        log.debug("same type: %s", left)
        return True

    # Implicit Numeric Tower
    if implicit and left in NUMERIC_TOWER and right in NUMERIC_TOWER:
        log.debug("numeric types: %s and %s", left, right)
        return NUMERIC_TOWER.index(right) >= NUMERIC_TOWER.index(left)

    o1 = get_origin(left) or getattr(left, "__orig_class__", None)
    o2 = get_origin(right) or getattr(right, "__orig_class__", None)
    a1, a2 = get_args(left), get_args(right)

    # Literal
    if o2 is Literal:
        log.debug("every left `Literal` arg is in right `Literal`")
        return o1 is Literal and set(a1).issubset(a2)
    if o1 is Literal:
        log.debug(
            "left %s in right args %s or every left arg type is subtype of right",
            left,
            a2,
        )
        return left in a2 or all(is_subtype(type(arg), right, **kwargs) for arg in a1)

    # Union
    if o1 in (Union, UnionType):  # every left must in right
        log.debug("every left arg must be subtype of right")
        return all(is_subtype(arg, right, **kwargs) for arg in a1)
    if o2 in (Union, UnionType):  # left must be any right
        log.debug("left is subtype of any right arg")
        return any(is_subtype(left, arg, **kwargs) for arg in a2)

    # Generics
    if o1 and o2 and o1 == o2:
        log.debug("same container: %s", o1)

        if o1 in (Callable, CallableABC):
            if not is_subtype(a1[1], a2[1], covariant=True):
                log.debug(
                    "%s return type must be covariant subtype of %s", a1[1], a2[1]
                )
                return False
            if a1[0] is Ellipsis:
                log.debug("left matches any right args")
                return True
            if a2[0] is Ellipsis:
                log.debug("left needs ellipsis to match")
                return False
            if len(a1[0]) != len(a2[0]):
                log.debug("different arg lengths")
                return False
            log.debug("left args must be contravariant subtype of right args")
            return all(
                is_subtype(x, y, contravariant=True, implicit=implicit)
                for x, y in zip(a1[0], a2[0])
            )

        if o1 is tuple and a1 == tuple(()):  # empty tuple means no args
            log.debug("left empty tuple clears out the args")
            a1 = tuple()
        if o2 is tuple and len(a2) == 2 and a2[1] is Ellipsis:
            log.debug("right Ellipsis changes the length of args")
            a2 = tuple(a2[0] for _ in range(len(a1)))  # even if a1 has nothing

        if len(a1) != len(a2):
            log.debug("different number of args")
            return False

        if o1 in (Sequence, SequenceABC):
            log.debug("Sequence is covariant in its items")
            kwargs.update(covariant=True)
            return is_subtype(a1[0], a2[0], covariant=True, implicit=implicit)
        if o1 in (Mapping, MappingABC):
            log.debug("Mapping is invariant in its keys and covariant in its items")
            return is_subtype(a1[0], a2[0], implicit=implicit) and is_subtype(
                a1[1], a2[1], covariant=True, implicit=implicit
            )

        bases = getattr(o1, "__orig_bases__", None)
        if bases:
            log.debug("left args must be subtypes of right args")
            # NOTE: We assume a single Generic[T] at the top.
            for tv, x, y in zip(get_args(bases[0]), a1, a2):
                if not is_subtype(
                    x,
                    y,
                    covariant=tv.__covariant__,
                    contravariant=tv.__contravariant__,
                    implicit=implicit,
                ):
                    log.debug("%s is not subtype of %s per %s", x, y, tv)
                    return False
            return True

        log.debug("left args must be subtypes of right args")
        return all(is_subtype(x, y, **kwargs) for x, y in zip(a1, a2))

    # Proper Types
    if isinstance(left, type) and isinstance(right, type) and covariant:
        log.debug("left type must be subclass of right type")
        return issubclass(left, right)

    log.debug("%s is not a subtype of %s", left, right)
    return False


def is_type(value: Any, kind: TypeForm[T]) -> bool:
    """Return `True` if `value` is of a type compatible with `kind`."""
    if kind is Any:
        return True
    if kind in (Never, NoReturn):
        return False
    if kind in (None, NoneType):
        return value is None

    info = type_info(kind)
    origin = info.origin
    args = info.args
    if origin is Literal:
        return value in args
    if origin in (Union, UnionType):
        return any(is_type(value, vt) for vt in args)
    if origin in (Callable, CallableABC):
        if not callable(value):
            log.debug("%s is not callable", value)
            return False
        if isinstance(value, type):
            log.debug("%s is a class", value)
            return False
        if isinstance(value, BuiltinFunctionType):
            log.debug("%s is a builtin; we cannot get type hints", value)
            return True

        hints = type_hints(value)
        return_type = hints.pop("return").hint
        args = ([h.hint for h in hints.values()], return_type)
        sig = getattr(Callable, "__getitem__")(args)
        log.debug("%s must be a subtype of %s", sig, kind)
        return is_subtype(sig, kind)
    # all special forms handled

    if not isinstance(value, cast(type, origin)):
        return False  # different containers

    if isinstance(value, Sized) and isinstance(value, Iterable):
        if origin in (list, set, dict) and len(value) == 0:
            return True  # empty mutable containers match

        if origin in (list, set):
            vt = args[0] if args else Any
            return all(is_type(v, vt) for v in value)

        if origin is dict and isinstance(value, Mapping):
            kt, vt = args if args else (Any, Any)
            return all(is_type(k, kt) and is_type(v, vt) for k, v in value.items())

        if origin is tuple:
            if len(args) == 0 or args == ((),):  # special empty-tuple format
                return isinstance(value, tuple) and len(value) == 0
            if len(args) > 1 and args[1] == ...:
                args = args[:1] * len(value)
            return len(value) == len(args) and all(
                is_type(v, vt) for v, vt in zip(value, args)
            )

    return isinstance(value, cast(type, kind))


### Casting ###


def to_type(value: Any, kind: TypeForm[T], casts: Optional[Casts] = None) -> T:
    """Try to cast `value` to the type of `kind`.

    Args:
        value (Any): the value to convert

        kind (TypeForm[T]): the type to convert to

        casts (Optional[Casts], default=None): if provided, this mapping
            of `tuple(source type, result type)` to converter functions
            will be used instead of the registered converters.

    Returns:
        Any: the requested type

    Raises:
        TypeError: if there are any problems converting `value` to `kind`
    """
    if is_type(value, kind):  # already done
        return cast(T, value)

    casts = casts or TYPE_CASTS
    src = type_info(value).origin
    fn: Union[Callable[[Any], T], None] = _get_casters(src, kind, casts)
    try:
        if fn:
            return fn(value)
        return _to_class(value, cast(type[T], kind), casts)
    except Exception as e:
        raise TypeError(f"Cannot cast {value!r} to {kind}") from e


def _get_casters(
    src: TypeForm[T], dest: TypeForm[K], casts: Optional[Casts] = None
) -> Callable[[Any], K] | None:
    casts = casts or TYPE_CASTS

    def _wrap(
        f: CastFn[Any], t: TypeForm[K], casts: Optional[Casts]
    ) -> Callable[[Any], K]:
        if isinstance(f, BuiltinFunctionType):
            arity = 1
        else:
            arity = len(signature(f).parameters)

        def _result(v: Any) -> K:
            if arity == 1:  # f is short-form
                f1 = cast(CastFnShort, f)
                return cast(K, f1(v))
            f2 = cast(CastFnLong[K], f)
            return f2(v, t, casts)

        return _result

    dest_origin: Any = type_info(dest).origin
    for left, right in [
        (src, dest),
        (src, dest_origin),
        (Any, dest),
        (Any, dest_origin),
    ]:
        if caster := casts.get((left, right)):
            return _wrap(caster, dest, casts)

    return None


### Extensions ###


@overload  # base case, functional invocation
def casts(
    src: TypeForm[T] | Iterable[TypeForm[T]],
    to: TypeForm[T] | Iterable[TypeForm[T]],
    func: CastFn[Any],
) -> CastFn[Any]: ...


@overload  # zero-arg decorator
def casts(func: F) -> F: ...


@overload  # from `Any` to one or more types
def casts(*, to: TypeForm[T] | Iterable[TypeForm[T]]) -> Callable[[F], F]: ...


@overload  # from one or more types to one or more types
def casts(
    src: TypeForm[T] | Iterable[TypeForm[T]], *, to: TypeForm[T] | Iterable[TypeForm[T]]
) -> Callable[[F], F]: ...


def casts(*args: Any, **kwargs: Any) -> Any:
    """Register a function to convert from/to one or more types.

    **Zero Argument Form**<br />
    Converts from first arg type to return type.
    ```python
    @casts
    def f(x: int) -> str: return str(x)
    ```

    **One Argument Form**<br />
    Converts from `Any` to `to` types.
    ```python
    @casts(to=str)
    def f(x): return str(x)
    ```

    **Two Argument Form**<br />
    Converts from `src` types to `to` types.
    ```python
    @casts(int, to=str)
    def f(x): return str(x)
    ```

    **Functional Form**<br />
    Register the function explicitly.
    ```python
    casts(int, str, lambda x: str(x))
    ```

    Args:
        src (TypeForm[T] | Iterable[TypeForm[T]]):
            one ore more types to convert from

        to (TypeForm[T] | Iterable[TypeForm[T]]):
            one ore more types to convert to

        func (CastFn[Any]): converter function

    Returns:
        (CastFn[Any] | Callable[[CastFn[Any]], CastFn[Any]]):
            converter function or a function that returns the converter function
    """

    if (
        len(args) == 1
        and callable(args[0])
        and not isinstance(args[0], type)
        and not kwargs
    ):  # zero-arg decorator
        func = cast(CastFn[Any], args[0])
        hints = type_hints(func)
        assert len(hints) > 0
        src = next(iter(hints.values())).origin
        to = hints["return"].origin
        return casts(src, to, func)

    if len(args) >= 1:
        kwargs["src"] = args[0]
    if len(args) >= 2:
        kwargs["to"] = args[1]
    if len(args) == 3:
        kwargs["func"] = args[2]
    if len(args) > 3:  # pragma: no cover
        # The type checkers won't let us test this.
        raise TypeError("Too many arguments.")

    src = kwargs.get("src", Any)
    if "to" in kwargs:
        to = kwargs["to"]
    else:
        raise TypeError("`cast` missing `to` parameter.")

    def _factory(func: F) -> F:
        for src_type in iterate(src):
            for to_type in iterate(to):
                TYPE_CASTS[(src_type, to_type)] = cast(CastFn[Any], func)
        return func

    f = kwargs.get("func")
    return _factory(f) if f else _factory


@casts(to=Any)
def _to_any(value: T) -> T:
    """Always return `value`."""
    return value


@casts(to=(Never, NoReturn))
def _to_never(value: Any) -> NoReturn:
    """Always raise a `TypeError`."""
    raise TypeError(f"Cannot cast {value!r} to Never (nothing can)")


@casts(to=NoneType)
def _to_none(value: Ignored = None) -> None:
    """Always return `None`."""
    return None


@casts(to=Literal)
def _to_literal(
    value: T,
    kind: TypeForm[T],
    casts: Optional[Casts] = None,
) -> T:
    """Return `value` if it is one of the `Literal` values."""
    if is_type(value, kind):
        return value
    raise TypeError(f"Cannot cast {value!r} to {kind}")


@casts(to=(Union, UnionType))
def _to_union(
    value: Any,
    kind: TypeForm[T],
    casts: Optional[Casts] = None,
) -> T:
    """Return first cast that works."""
    for arg in get_args(kind):
        try:
            return cast(T, to_type(value, arg, casts))
        except (AssertionError, TypeError, ValueError):
            pass
    raise TypeError(f"Cannot cast {value!r} to {kind}")


@casts
def _str_to_int(value: str) -> int:
    """Return `value` as an `int`."""
    try:
        return int(value)
    except ValueError:
        return int(float(value))


@casts
def _to_bytes(
    value: Any,
    kind: type[bytes] = bytes,
    casts: Union[Casts, None] = None,
) -> bytes:
    """Return `value` as `bytes`, encoding `str` with a default encoding if needed."""
    if isinstance(value, str):
        return value.encode(DEFAULT_ENCODING)
    return kind(value)


@casts
def _to_str(
    value: Any,
    kind: type[str] = str,
    casts: Optional[Casts] = None,
) -> str:
    """Return `value` as `str`, decoding `bytes` with a default encoding if needed."""
    if isinstance(value, bytes):
        return value.decode(DEFAULT_ENCODING)
    return kind(value)


@casts
def _to_list(
    value: Any,
    kind: type[list[T]] = list,
    casts: Optional[Casts] = None,
) -> list[T]:
    """Return `value` as a `list`."""
    assert isinstance(value, Iterable)
    args = get_args(kind)
    val_type = args[0] if args else Any
    return kind(to_type(val, val_type, casts) for val in value)


@casts
def _to_set(
    value: Any,
    kind: type[set[T]] = set,
    casts: Optional[Casts] = None,
) -> set[T]:
    """Return `value` as a `set`."""
    assert isinstance(value, Iterable)
    args = get_args(kind)
    val_type = args[0] if args else Any
    return kind(to_type(val, val_type, casts) for val in value)


@casts
def _to_dict(
    value: Any,
    kind: type[dict[K, T]] = dict,
    casts: Optional[Casts] = None,
) -> dict[K, T]:
    """Return `value` as a `dict`."""
    assert isinstance(value, Sized)
    if len(value) == 0:
        return kind()

    assert isinstance(value, Mapping)
    args = get_args(kind)
    key_type, val_type = args if args else (Any, Any)
    return kind(
        {
            to_type(k, key_type, casts): to_type(v, val_type, casts)
            for k, v in value.items()
        }
    )


@casts
def _to_tuple(
    value: Any,
    kind: type[tuple[Any, ...]] = tuple,
    casts: Optional[Casts] = None,
) -> tuple[Any, ...]:
    """Cast `value` into a `tuple`."""
    args = get_args(kind)
    if (not value or len(value) == 0) and len(args) == 0 or args == ((),):
        return kind()
    if len(args) > 1 and args[1] == ...:  # by definition
        args = args[:1] * len(value)
    if len(value) != len(args):
        raise ValueError(f"Different lengths when casting {value!r} to {kind}")
    return kind(to_type(val, val_type, casts) for val, val_type in zip(value, args))


casts(str, datetime, datetime.fromisoformat)


@casts((int, float), to=datetime)
def _float_to_datetime(value: float) -> datetime:
    """Return `value` as a `datetime` in the UTC timezone."""
    return datetime.fromtimestamp(value, timezone.utc)


@casts
def _to_datetime(value: Any) -> datetime:
    """Return `value` as a `datetime`."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, (list, tuple)):  # try to unpack values
        return datetime(*value)  # type: ignore
    if isinstance(value, dict):
        return datetime(**value)  # type: ignore
    raise ValueError(f"Cannot cast {value!r} into datetime")


# NOTE: We do not register this fallback function.
def _to_class(
    value: Any,
    kind: type[T],
    casts: Optional[Casts] = None,
) -> T:
    """Return `value` as an instance of `kind`."""
    if isinstance(value, dict):
        hints = type_hints(kind)
        data: dict[str, Any] = {}
        props: dict[str, Any] = {}
        for name, info in hints.items():
            val = value.get(name, info.default)
            if val is Parameter.empty:  # no value supplied, no default
                if info.origin in (Union, UnionType) and NoneType in info.args:
                    val = None  # safe choice
                else:  # no valid choices for this field
                    continue

            typed: Any = to_type(val, info.hint, casts)
            if isinstance(getattr(kind, name, None), property):
                props[name] = typed
            else:
                data[name] = typed

        if is_dataclass(kind):
            return setattrs(cast(T, kind(**data)), props)
        else:
            return setattrs(kind(), data, props)

    # try passing it to the constructor
    return kind(value)  # type: ignore[call-arg]


def castfit(
    spec: type[T],
    data: dict[str, Any],
    *,
    casts: Optional[Casts] = None,
) -> T:
    """Return an instance of `spec` using `data` to set field values.

    We use type hints to help us figure out how to convert the provided
    data into the field values.

    Args:
        spec (type[T]): plain `class` or `dataclass`; use type hints and
            defaults to define how the data should be converted.

        data (dict[str, Any]): field names mapped to values

        casts (Optional[Casts], default=None): if provided, this mapping
            of `tuple(source type, result type)` to converter functions
            will be used instead of the registered converters.

    Returns:
        Any: an instance of `spec` with fields set

    Raises:
        TypeError: if there is a problem converting any of the fields
    """
    return _to_class(data, spec, casts)
