# std
from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from types import FunctionType
from typing import Any
from typing import Literal
from typing import Union
import sys

# pkg
from castfit import TypeInfo
from castfit import UnionType
import castfit


def test_setattrs() -> None:
    """Set multiple attributes on an object."""

    class Point:
        x: int = 0
        y: bool = False

    obj = Point()
    castfit.setattrs(obj, x=1, y=True)
    assert obj.x == 1
    assert obj.y is True

    obj = Point()
    castfit.setattrs(obj, {"x": 1, "y": True})
    assert obj.x == 1
    assert obj.y is True

    obj = Point()
    castfit.setattrs(obj, {"x": 1}, y=True)
    assert obj.x == 1
    assert obj.y is True

    obj = Point()
    castfit.setattrs(obj, {"x": 1}, {"y": True})
    assert obj.x == 1
    assert obj.y is True


def test_type_info_any() -> None:
    """`Any` type info."""
    assert castfit.type_info(Any) == TypeInfo(name="Any", hint=Any, origin=Any)
    assert castfit.type_info(Any, use_cache=False) == TypeInfo(
        name="Any", hint=Any, origin=Any
    )


def test_type_literal() -> None:
    """`Literal` type info."""

    assert castfit.type_info(Literal) == TypeInfo(
        name="Literal", hint=Literal, origin=Literal
    )
    assert castfit.type_info(Literal["r", "w"]) == TypeInfo(
        name="Literal", hint=Literal["r", "w"], origin=Literal, args=("r", "w")
    )
    assert castfit.type_info(Literal["w", "r"]) == TypeInfo(
        name="Literal", hint=Literal["w", "r"], origin=Literal, args=("w", "r")
    ), "expect preserved arg order"


def test_type_union() -> None:
    """`Union` type info."""
    assert castfit.type_info(Union) == TypeInfo(name="Union", hint=Union, origin=Union)
    if sys.version_info >= (3, 10):
        assert castfit.type_info(UnionType) == TypeInfo(
            name="UnionType", hint=UnionType, origin=UnionType
        )
    else:
        assert castfit.type_info(UnionType) == TypeInfo(
            name="_UnionGenericAlias", hint=UnionType, origin=UnionType
        )
    assert castfit.type_info(Union[str, int]) == TypeInfo(
        name="Union", hint=Union[str, int], origin=Union, args=(str, int)
    )
    assert castfit.type_info(Union[int, str]) == TypeInfo(
        name="Union", hint=Union[int, str], origin=Union, args=(int, str)
    ), "expect preserved arg order"

    assert castfit.type_info(dict[str, Union[int, str]]) == TypeInfo(
        name="dict",
        hint=dict[str, Union[int, str]],
        origin=dict,
        args=(str, Union[int, str]),
    )
    assert castfit.type_info(dict[str, Union[str, int]]) == TypeInfo(
        name="dict",
        hint=dict[str, Union[str, int]],
        origin=dict,
        args=(
            str,
            Union[str, int],
        ),
    ), "expect preserved sub-arg order"


def test_type_generics() -> None:
    """Generic type info."""

    assert castfit.type_info(list) == TypeInfo(name="list", hint=list, origin=list)
    assert castfit.type_info(list[int]) == TypeInfo(
        name="list", hint=list[int], origin=list, args=(int,)
    )


def test_type_instance() -> None:
    """Instance type info."""
    assert castfit.type_info([1, 2, 3]) == TypeInfo(hint=list, origin=list)
    assert castfit.type_info(3) == TypeInfo(hint=int, origin=int)

    class MyList(list[int]): ...

    assert castfit.type_info(MyList) == TypeInfo(
        name="MyList", hint=MyList, origin=list, args=(int,)
    )
    assert castfit.type_info(MyList([1, 2, 3])) == TypeInfo(
        hint=MyList, origin=MyList
    ), "instances don't have __name__"


def test_type_function() -> None:
    """Function type info."""
    assert castfit.type_info(lambda x: x) == TypeInfo(
        "<lambda>", FunctionType, origin=FunctionType
    )


def test_type_hint_lambda() -> None:
    """`lambda` has unknown argument and return types"""
    assert castfit.type_hints(lambda x: x) == {
        "x": TypeInfo("x", Any),
        "return": TypeInfo("return"),
    }


def test_type_hint_function() -> None:
    """Normal type hints."""

    def _x(x: int, y: str = "works") -> bool:
        return bool(x)

    assert castfit.type_hints(_x) == {
        "x": TypeInfo("x", int, origin=int),
        "y": TypeInfo("y", str, "works", origin=str),
        "return": TypeInfo("return", bool, origin=bool),
    }


def test_type_hint_class() -> None:
    """Mixed un/typed & with/without defaults."""

    class X:
        typed: int
        typed_none: Union[int, None] = None
        typed_default: bool = True
        untyped = None
        untyped_default = 5

    assert castfit.type_hints(X) == {
        "typed": TypeInfo("typed", int, origin=int),
        "typed_none": TypeInfo(
            "typed_none", Union[int, None], None, origin=Union, args=(int, type(None))
        ),
        "typed_default": TypeInfo("typed_default", bool, True, origin=bool),
        "untyped": TypeInfo("untyped", Any, None),
        "untyped_default": TypeInfo("untyped_default", int, 5, origin=int),
    }


def test_type_hint_dataclass() -> None:
    """Dataclass with default values."""

    @dataclass
    class Post:
        title: str = field(default="Untitled")
        tags: list[str] = field(default_factory=list[str])

    assert castfit.type_hints(Post) == {
        "title": TypeInfo("title", str, default="Untitled", origin=str, args=()),
        "tags": TypeInfo("tags", list[str], origin=list, args=(str,)),
    }
