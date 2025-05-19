# std
from __future__ import annotations
from typing import Any
from typing import Union

# pkg
import castfit
from castfit import Typed


class Point:
    x: int = 0
    y: bool = False


def test_setattrs() -> None:
    """Set multiple attributes on an object."""
    obj = Point()
    castfit.setattrs(obj, x=1, y=True)
    assert obj.x == 1
    assert obj.y is True

    obj = Point()
    castfit.setattrs(obj, dict(x=1, y=True))
    assert obj.x == 1
    assert obj.y is True

    obj = Point()
    castfit.setattrs(obj, dict(x=1), y=True)
    assert obj.x == 1
    assert obj.y is True


def test_get_origin_type() -> None:
    """Get the appropriate constructor."""
    assert castfit.get_origin_type(list[int]) is list
    assert castfit.get_origin_type(list) is list
    assert castfit.get_origin_type([]) is list

    class MyList(list[int]):
        pass

    assert castfit.get_origin_type(MyList) is MyList
    assert castfit.get_origin_type(MyList([1, 2, 3])) is MyList


def test_get_types() -> None:
    """Get type hints."""
    # lambda produces an unknown return type
    assert castfit.get_types(lambda x: x) == {
        "x": Typed("x"),
        "return": Typed("return", Any),
    }

    def _x(x: int, y: str = "works") -> bool:
        return bool(x)

    assert castfit.get_types(_x) == {
        "x": Typed("x", int),
        "y": Typed("y", str, "works"),
        "return": Typed("return", bool),
    }

    class X:
        typed: int
        typed_none: Union[int, None] = None
        typed_default: bool = True
        untyped = None
        untyped_default = 5

    assert castfit.get_types(X) == {
        "typed": Typed("typed", int),
        "typed_none": Typed("typed_none", Union[int, None], None),
        "typed_default": Typed("typed_default", bool, True),
        "untyped": Typed("untyped", Any, None),
        "untyped_default": Typed("untyped_default", int, 5),
    }
