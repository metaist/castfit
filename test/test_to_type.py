# std
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Literal
from typing import Optional
from typing import Union
import sys

# lib
from pytest import raises

# pkg
from castfit import Never
from castfit import NoneType
import castfit


def test_get_origin_type() -> None:
    """Get the appropriate constructor."""
    assert castfit.get_origin_type(list[int]) is list
    assert castfit.get_origin_type(list) is list
    assert castfit.get_origin_type([]) is list

    class MyList(list[int]):
        pass

    assert castfit.get_origin_type(MyList) == MyList
    assert castfit.get_origin_type(MyList([1, 2, 3])) == MyList


def test_any() -> None:
    """Keep whatever type you have."""
    values: list[Any] = [None, True, 3, 6.28, "test", b"test"]
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


def test_custom() -> None:
    """Custom conversions."""
    assert castfit.to_type("123", int, casts={int: lambda v, t, ch, ca: 999}) == 999


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


# TODO 2025-10-31 @ py3.9 EOL: remove conditional
if sys.version_info >= (3, 10):

    def test_union_type() -> None:
        """Any of a `UnionType` args can match."""
        assert castfit.to_type(42, str | None) == "42"


def test_empty() -> None:
    """Make empty containers."""
    assert castfit.to_type(list(), dict[str, int]) == dict()
    assert castfit.to_type(set(), list[int]) == list()
    assert castfit.to_type(list(), set[int]) == set()
    assert castfit.to_type("", tuple[()]) == tuple()


def test_containers() -> None:
    """Cast values in a container."""
    assert castfit.to_type([1, "2", 3.0], list[float]) == [1.0, 2.0, 3.0]
    assert castfit.to_type([1, "2", 3.0], set[float]) == {1.0, 2.0, 3.0}
    assert castfit.to_type([1, "2", 3.0], tuple[float, int, str]) == (1.0, 2, "3.0")
    assert castfit.to_type([1, "2", 3.0], tuple[float, ...]) == (1.0, 2.0, 3.0)
    assert castfit.to_type({"x": 1, 2: "3"}, dict[str, float]) == {
        "x": 1.0,
        "2": 3.0,
    }
    assert castfit.to_type({"x": 1, 2: "3"}, list) == ["x", 2]
    assert castfit.to_type({"x": 1, 2: "3"}, set) == {"x", 2}

    with raises(TypeError):  # input too short
        castfit.to_type([1], tuple[float, int])
    with raises(TypeError):  # input too long
        castfit.to_type([1, 2], tuple[float])


def test_datetime() -> None:
    """Cast to `datetime`."""
    dt = datetime(2023, 12, 12, 12)
    assert castfit.to_datetime(dt, datetime) == dt  # direct to avoid check
    assert castfit.to_type([2023, 12, 12, 12], datetime) == dt
    assert castfit.to_type((2023, 12, 12, 12), datetime) == dt
    assert castfit.to_type("2023-12-12T12:00:00", datetime) == dt
    assert castfit.to_type(dict(year=2023, month=12, day=12, hour=12), datetime) == dt
    assert castfit.to_type(1745865691.2135372, datetime) == datetime(
        2025, 4, 28, 14, 41, 31, 213537
    )

    with raises(TypeError):
        castfit.to_type(None, datetime)
    with raises(TypeError):
        castfit.to_type("12/12/2023 12:00:00", datetime)  # bad format


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


def test_nested_class() -> None:
    """Cast data into nested classes."""

    @dataclass
    class Dog:
        name: str
        age: int

    @dataclass
    class Owner:
        dogs: list[Dog]

    dogs = [{"name": "Fido", "age": "3"}, {"name": "Spot", "age": "5"}]
    have: Owner = castfit.castfit(Owner, {"dogs": dogs})
    assert len(have.dogs) == 2
    assert have.dogs[0].name == "Fido"
    assert have.dogs[1].age == 5
