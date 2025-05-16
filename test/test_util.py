# std
from typing import Any

# pkg
import castfit


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
    assert castfit.get_types(lambda x: x) == {"x": Any, "return": None}

    def _x(x: int) -> bool:
        return bool(x)

    assert castfit.get_types(_x) == {"x": int, "return": bool}

    class X:
        typed: int
        untyped = None
        untyped_default = 5
        typed_default: bool = True

    assert castfit.get_types(X) == {
        "typed": int,
        "untyped": Any,
        "untyped_default": int,
        "typed_default": bool,
    }
