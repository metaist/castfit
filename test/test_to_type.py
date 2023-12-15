# std
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

# lib
from pytest import raises

# pkg
import castfit
from castfit import Never
from castfit import NoneType


def test_get_origin_type() -> None:
    """Get the appropriate constructor."""
    assert castfit.get_origin_type(List[int]) == list
    assert castfit.get_origin_type(list) == list
    assert castfit.get_origin_type([]) == list

    class MyList(List[int]):
        pass

    assert castfit.get_origin_type(MyList) == MyList
    assert castfit.get_origin_type(MyList([1, 2, 3])) == MyList


def test_any() -> None:
    """Keep whatever type you have."""
    values: List[Any] = [None, True, 3, 6.28, "test", b"test"]
    for val in values:
        assert castfit.to_type(val, Any) == val
        assert castfit.to_any(val) == val  # since `to_type` doesn't try the cast


def test_never() -> None:
    """`Never` rejects all types."""
    values = [None, True, 3, 6.28, "test", b"test"]
    for val in values:
        with raises(TypeError):
            castfit.to_type(val, Never)


def test_none() -> None:
    """Convert everything to `None`."""
    values = [None, True, 3, 6.28, "test", b"test"]
    for val in values:
        assert castfit.to_type(val, NoneType) is None


def test_basic() -> None:
    """Basic conversions."""
    assert castfit.to_type(None, bool) is False
    assert castfit.to_type(6.28, int) == 6
    assert castfit.to_type(3, float) == 3.0
    assert castfit.to_type(b"test", str) == "test"
    assert castfit.to_type("test", bytes) == b"test"

    # special cases
    assert castfit.to_type([65], bytes) == b"A"
    assert castfit.to_str("A") == "A"

    with raises(TypeError):
        castfit.to_type("break", int)


def test_literal() -> None:
    """`Literal` requires one of its values."""
    assert castfit.to_literal("r", Literal["r", "rw"]) == "r"
    assert castfit.to_literal(2, Literal[1, 2, 3]) == 2

    with raises(TypeError):
        castfit.to_literal(5, Literal[1, 2, 3])


def test_union() -> None:
    """Any of a `Union` args can match."""
    assert castfit.to_type(42, Union[int, float]) == 42
    assert castfit.to_type("42", Union[float, int]) == 42.0
    assert castfit.to_type(None, Optional[int]) is None
    assert castfit.to_type(None, Optional[Literal[1, 2, 3]]) is None

    with raises(TypeError):
        castfit.to_type(None, Union[int, float])


def test_empty() -> None:
    """Make empty containers."""
    assert castfit.to_type(list(), Dict[str, int]) == dict()
    assert castfit.to_type(set(), List[int]) == list()
    assert castfit.to_type(list(), Set[int]) == set()
    assert castfit.to_type("", Tuple[()]) == tuple()

    with raises(ValueError):
        castfit.to_type([1, 2], Tuple[int, str, float])  # not enough values


def test_containers() -> None:
    """Cast values in a container."""
    assert castfit.to_type([1, "2", 3.0], List[float]) == [1.0, 2.0, 3.0]
    assert castfit.to_type([1, "2", 3.0], Set[float]) == {1.0, 2.0, 3.0}
    assert castfit.to_type([1, "2", 3.0], Tuple[float, int, str]) == (1.0, 2, "3.0")
    assert castfit.to_type([1, "2", 3.0], Tuple[float, ...]) == (1.0, 2.0, 3.0)
    assert castfit.to_type({"x": 1, 2: "3"}, Dict[str, float]) == {
        "x": 1.0,
        "2": 3.0,
    }


def test_datetime() -> None:
    """Cast `str` to `datetime`."""
    assert castfit.to_type("2023-12-12T12:00:00", datetime) == datetime(
        2023, 12, 12, 12
    )


def test_castfit_class() -> None:
    """Cast data using a class."""

    class Spec:
        name: str
        age: int
        loc: Path

    have: Spec = castfit.castfit(Spec, dict(name="Bob", age="21", loc="/"))
    assert have.name == "Bob"
    assert have.age == 21
    assert have.loc == Path("/")


def test_castfit_object() -> None:
    """Cast data using an instance."""

    class Spec:
        name: str
        age: int
        loc: Path

    have: Spec = castfit.castfit(Spec(), dict(name="Bob", age="21", loc="/"))
    assert have.name == "Bob"
    assert have.age == 21
    assert have.loc == Path("/")


def test_spec_dataclass() -> None:
    """Cast data using a dataclass."""

    @dataclass
    class Spec:
        name: str
        age: int
        loc: Path

    have: Spec = castfit.castfit(Spec, dict(name=777, age="21", loc="/"))
    assert have.name == "777"
    assert have.age == 21
    assert have.loc == Path("/")
