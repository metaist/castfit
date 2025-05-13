# std
from __future__ import annotations
from datetime import datetime
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Literal
from typing import NoReturn
from typing import Optional
from typing import Union
import sys

# pkg
import castfit
from castfit import Never
from castfit import NoneType


def test_any() -> None:
    """`Any` accepts all types."""
    assert castfit.is_type(None, Any)
    assert castfit.is_type(True, Any)
    assert castfit.is_type(3, Any)
    assert castfit.is_type(6.28, Any)
    assert castfit.is_type("test", Any)
    assert castfit.is_type(b"test", Any)
    assert castfit.is_type(Any, Any)


def test_never() -> None:
    """`Never` rejects all types."""
    assert not castfit.is_type(None, NoReturn)
    assert not castfit.is_type(None, Never)
    assert not castfit.is_type(True, Never)
    assert not castfit.is_type(3, Never)
    assert not castfit.is_type(6.28, Never)
    assert not castfit.is_type("test", Never)
    assert not castfit.is_type(b"test", Never)
    assert not castfit.is_type(Never, Never)


def test_basic() -> None:
    """Types should match."""
    assert castfit.is_type(True, bool)
    assert castfit.is_type(False, bool)
    assert castfit.is_type(3, int)
    assert castfit.is_type(6.28, float)
    assert castfit.is_type("test", str)
    assert castfit.is_type(b"test", bytes)

    assert not castfit.is_type(None, bool)
    assert not castfit.is_type(6.28, int)
    assert not castfit.is_type(3, float)
    assert not castfit.is_type(b"test", str)
    assert not castfit.is_type("test", bytes)


def test_literal() -> None:
    """Value must match one of `Literal` args."""
    assert castfit.is_type("r", Literal["r", "rw"])
    assert castfit.is_type(2, Literal[1, 2, 3])
    assert castfit.is_type(None, Optional[Literal[1, 2, 3]])
    assert not castfit.is_type(5, Literal[1, 2, 3])


def test_union() -> None:
    """Any of a `Union` args can match."""
    assert castfit.is_type(42, Union[float, int])
    assert castfit.is_type(None, Optional[int])
    assert castfit.is_type(42, Union[str, Union[float, int]])
    assert not castfit.is_type(42, Union[str, float])


# TODO 2025-10-31 @ py3.9 EOL: remove conditional
if sys.version_info >= (3, 10):

    def test_union_type() -> None:
        """Any of a `UnionType` args can match."""
        assert castfit.is_type(42, int | None)


def test_empty() -> None:
    """Empty containers match."""
    assert castfit.is_type(dict(), dict[str, int])
    assert castfit.is_type(list(), list[int])
    assert castfit.is_type(set(), set[int])


def test_list() -> None:
    """Every item in the list or set must match."""
    assert castfit.is_type([1], list)
    assert castfit.is_type([1], list[int])
    assert castfit.is_type({6, 7}, set)
    assert castfit.is_type({6, 7}, set[int])

    assert castfit.is_type([3, 5, "test", "fun"], list[Union[int, str]])

    assert not castfit.is_type([1], set[int])
    assert not castfit.is_type({1}, list[int])


def test_tuple() -> None:
    """Every item in the tuple must match."""
    assert castfit.is_type((), tuple)
    assert castfit.is_type((), tuple[()])
    assert castfit.is_type((3, "yes", 7.5), tuple[int, str, float])
    assert castfit.is_type((1, 2, 3), tuple[int, ...])

    assert not castfit.is_type([], tuple)


def test_dict() -> None:
    """Keys and values must match."""
    assert castfit.is_type({"field": 2.0}, dict)
    assert castfit.is_type({"field": 2.0}, dict[str, float])
    assert castfit.is_type({"x": 1, "y": "test"}, dict[str, Union[int, str]])

    assert castfit.is_type({("x", 1): ["z"]}, dict[tuple[str, int], list[str]])
    assert not castfit.is_type([], dict[str, str])


def test_datetime() -> None:
    """Check datetime objects."""
    assert castfit.is_type(datetime.now(), datetime)


def test_callable() -> None:
    """Check callable objects."""
    Fn = Callable[..., Any]
    AnyAny = Callable[[Any], Any]
    IntBool = Callable[[int], bool]
    IntInt = Callable[[int], int]
    StrInt = Callable[[str], int]

    def int_bool(x: int) -> bool:
        return bool(x)

    def int_int(x: int) -> int:
        return x

    def str_int(x: str) -> int:
        return int(x)

    assert castfit.is_type(lambda x: x, AnyAny), "Any accepts all types"
    assert castfit.is_type(lambda x, y, z: None, Fn), "... accepts all args"

    assert castfit.is_type(int_bool, IntBool)
    assert castfit.is_type(int_int, IntInt)
    assert castfit.is_type(str_int, StrInt)
    assert castfit.is_type(int_bool, IntInt), "bool is a subtype of int"

    assert not castfit.is_type([], AnyAny), "not callable"
    assert not castfit.is_type(lambda x, y: x + y, AnyAny), "wrong arg count"
    assert not castfit.is_type(int_int, IntBool), "wrong return type"
    assert not castfit.is_type(str_int, IntInt), "wrong arg type"


def test_is_subtype() -> None:
    """Check subtypes."""
    # Any: all members
    assert castfit.is_subtype(str, Any)
    assert castfit.is_subtype(Any, Any)
    assert castfit.is_subtype(Never, Any)

    # Never: no members
    assert not castfit.is_subtype(int, Never)
    assert not castfit.is_subtype(int, NoReturn)
    assert not castfit.is_subtype(Never, Never)

    # None: one member
    assert castfit.is_subtype(None, NoneType)
    assert castfit.is_subtype(NoneType, NoneType)
    assert not castfit.is_subtype(int, NoneType)

    # Literal: requires subset of args
    assert castfit.is_subtype(Literal["r"], Literal["r", "w"])
    assert not castfit.is_subtype(Literal["r", "x"], Literal["r", "w"])

    assert castfit.is_subtype(Literal[3], int)
    assert not castfit.is_subtype(Literal[3], bool), "int is not a subtype of bool"
    assert castfit.is_subtype(Literal[3, "hi"], Union[int, str])

    # Union: requires subset of args
    assert castfit.is_subtype(str, Union[str, int, bool])
    assert castfit.is_subtype(Union[str], Union[str, int, bool])
    assert castfit.is_subtype(Union[str, int], Union[str, int, bool])
    assert not castfit.is_subtype(Union[str, None], Union[str, int, bool])

    if sys.version_info >= (3, 10):
        assert castfit.is_subtype(str, str | int)

    # generics
    assert castfit.is_subtype(list[bool], list[Union[bool, int]])
    assert castfit.is_subtype(list[bool], list[int]), "bool subtypes of int"
    assert castfit.is_subtype(dict[str, bool], dict[str, int]), "bool subtype of int"
    assert castfit.is_subtype(tuple[bool, ...], tuple[int, ...]), "bool subtype of int"
    assert castfit.is_subtype(list[bool], Iterable[int]), "list subtype of Iterable"

    assert not castfit.is_subtype(list[int], list[bool]), "int not subtype of bool"

    # normal subclass
    assert castfit.is_subtype(int, int)  # self-membership
    assert castfit.is_subtype(bool, int)
    assert not castfit.is_subtype(int, str)
