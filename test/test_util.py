# std
from __future__ import annotations
from typing import Any
from typing import Union
from typing import Literal

# pkg
from castfit import TypeInfo
from castfit import UnionType
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
    castfit.setattrs(obj, {"x": 1, "y": True})
    assert obj.x == 1
    assert obj.y is True

    obj = Point()
    castfit.setattrs(obj, {"x": 1}, y=True)
    assert obj.x == 1
    assert obj.y is True


def test_type_info() -> None:
    """Get type information."""
    assert castfit.type_info(Any) == TypeInfo(name="Any", hint=Any, origin=Any)
    assert castfit.type_info(Any, use_cache=False) == TypeInfo(
        name="Any", hint=Any, origin=Any
    )
    assert castfit.type_info(Literal) == TypeInfo(
        name="Literal", hint=Literal, origin=Literal
    )
    assert castfit.type_info(Literal["r", "w"]) == TypeInfo(
        name="Literal", hint=Literal["r", "w"], origin=Literal, args=("r", "w")
    )
    assert castfit.type_info(Literal["w", "r"]) == TypeInfo(
        name="Literal", hint=Literal["w", "r"], origin=Literal, args=("w", "r")
    ), "expect preserved arg order"

    assert castfit.type_info(Union) == TypeInfo(name="Union", hint=Union, origin=Union)
    assert castfit.type_info(UnionType) == TypeInfo(
        name="UnionType", hint=UnionType, origin=UnionType
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

    assert castfit.type_info(list) == TypeInfo(name="list", hint=list, origin=list)
    assert castfit.type_info(list[int]) == TypeInfo(
        name="list", hint=list[int], origin=list, args=(int,)
    )

    assert castfit.type_info([1, 2, 3]) == TypeInfo(hint=list, origin=list)
    assert castfit.type_info(3) == TypeInfo(hint=int, origin=int)

    class MyList(list[int]): ...

    assert castfit.type_info(MyList) == TypeInfo(
        name="MyList", hint=MyList, origin=MyList
    )
    assert castfit.type_info(MyList([1, 2, 3])) == TypeInfo(
        hint=MyList, origin=MyList
    ), "instances don't have __name__"


def test_type_hints() -> None:
    """Get type hints."""
    # lambda produces an unknown return type
    assert castfit.type_hints(lambda x: x) == {
        "x": TypeInfo("x", Any),
        "return": TypeInfo("return"),
    }

    def _x(x: int, y: str = "works") -> bool:
        return bool(x)

    assert castfit.type_hints(_x) == {
        "x": TypeInfo("x", int, origin=int),
        "y": TypeInfo("y", str, "works", origin=str),
        "return": TypeInfo("return", bool, origin=bool),
    }

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
