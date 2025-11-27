# std
from types import NoneType
from typing import Any
from typing import Callable
from typing import Generic
from typing import Literal
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import TypeVar
from typing import Union

# pkg
from castfit import Never
import castfit


def test_invariant() -> None:
    assert castfit.is_subtype(bool, bool)  # trivially true
    assert castfit.is_subtype(bool, int)  # implicitly true
    assert not castfit.is_subtype(bool, int, implicit=False)  # true invariant


def test_covariant() -> None:
    assert castfit.is_subtype(bool, int, covariant=True, implicit=False)
    assert not castfit.is_subtype(int, bool)


def test_contravariant() -> None:
    assert castfit.is_subtype(int, bool, contravariant=True)


def test_bivariant() -> None:
    assert castfit.is_subtype(
        bool, int, covariant=True, contravariant=True, implicit=False
    )
    assert castfit.is_subtype(
        int, bool, covariant=True, contravariant=True, implicit=False
    )


def test_any() -> None:
    """Every type is a member of `Any`."""
    assert castfit.is_subtype(None, Any)
    assert castfit.is_subtype(Never, Any)
    assert castfit.is_subtype(int, Any)
    assert castfit.is_subtype(list[str], Any)
    assert not castfit.is_subtype(Any, bool)  # Any isn't a subtype of others
    assert castfit.is_subtype(Any, Any)  # but it is a subtype of itself


def test_never() -> None:
    """No type is a member of `Never`."""
    assert not castfit.is_subtype(None, Never)
    assert not castfit.is_subtype(Never, Never)  # including Never itself
    assert not castfit.is_subtype(int, Never)
    assert not castfit.is_subtype(list[str], Never)

    assert castfit.is_subtype(Never, int)
    assert castfit.is_subtype(Never, list[str])


def test_none() -> None:
    assert castfit.is_subtype(None, None)
    assert castfit.is_subtype(None, NoneType)
    assert castfit.is_subtype(NoneType, None)
    assert castfit.is_subtype(NoneType, NoneType)
    assert castfit.is_subtype(NoneType, Optional[int])
    assert castfit.is_subtype(None, Union[int, None])

    assert not castfit.is_subtype(int, NoneType)
    assert not castfit.is_subtype(NoneType, int)


def test_numeric_tower() -> None:
    assert castfit.is_subtype(bool, int)
    assert castfit.is_subtype(bool, float)
    assert castfit.is_subtype(bool, complex)
    assert castfit.is_subtype(int, float)
    assert castfit.is_subtype(int, complex)
    assert castfit.is_subtype(float, complex)

    assert not castfit.is_subtype(int, bool)
    assert not castfit.is_subtype(float, bool)
    assert not castfit.is_subtype(complex, bool)
    assert not castfit.is_subtype(float, int)
    assert not castfit.is_subtype(complex, int)
    assert not castfit.is_subtype(complex, float)

    # use implicit numeric tower (and not `issubclass`)
    assert castfit.is_subtype(bool, complex, covariant=True)


def test_literal() -> None:
    assert castfit.is_subtype(Literal["r"], Literal["r", "w"])
    assert castfit.is_subtype(Literal["r"], Union[Literal["r"], Literal["w"]])
    assert not castfit.is_subtype(Literal["r", "x"], Literal["r", "w"])

    assert castfit.is_subtype(Literal[3], int)
    assert not castfit.is_subtype(Literal[3], bool), "int is not a subtype of bool"
    assert castfit.is_subtype(Literal[True], int), "bool is implicit subtype of int"
    assert not castfit.is_subtype(Literal[True], int, implicit=False)
    assert castfit.is_subtype(Literal[3, "hi"], Union[int, str])


def test_union() -> None:
    assert castfit.is_subtype(str, Union[str, int, bool])
    assert castfit.is_subtype(Union[str, int], Union[str, int, bool])
    assert not castfit.is_subtype(Union[str, None], Union[str, int, bool])
    assert castfit.is_subtype(str, str | int)


def test_callable() -> None:
    assert not castfit.is_subtype(Callable[..., bool], bool), "right not Callable"

    assert not castfit.is_subtype(
        Callable[[int], bool], Callable[[int], str]
    ), "different return"

    assert castfit.is_subtype(
        Callable[..., bool], Callable[[int], bool]
    ), "left Ellipsis always matches"
    assert not castfit.is_subtype(
        Callable[[int], bool], Callable[..., bool]
    ), "right Ellipsis never matches"

    assert not castfit.is_subtype(
        Callable[[int], bool], Callable[[int, str], bool]
    ), "wrong arg length"
    assert not castfit.is_subtype(
        Callable[[int, str], bool], Callable[[int], bool]
    ), "wrong arg length"

    assert castfit.is_subtype(Callable[[Any], bool], Callable[[int], bool])
    assert not castfit.is_subtype(Callable[[int], bool], Callable[[Any], bool])


def test_list() -> None:
    assert castfit.is_subtype(list[Union[str, int]], list[Union[str, int]])
    assert castfit.is_subtype(list[str], list[Union[str, int]])
    assert not castfit.is_subtype(list[int], list[str])
    assert not castfit.is_subtype(list[str], set[str])

    class MyList(list[Any]): ...

    assert castfit.is_subtype(MyList, list, covariant=True)


def test_dict() -> None:
    assert castfit.is_subtype(dict[str, int], dict[str, int])
    assert castfit.is_subtype(dict[str, int], dict[Union[str, int], int])


def test_tuple() -> None:
    assert castfit.is_subtype(tuple[int, str], tuple[int, str])
    assert castfit.is_subtype(tuple[int, int, int], tuple[int, ...])
    assert not castfit.is_subtype(tuple[int, ...], tuple[int, int, int])

    assert castfit.is_subtype(tuple[()], tuple[Any, ...])


def test_generics() -> None:
    class Animal: ...

    class Dog(Animal): ...

    class Labrador(Dog): ...

    assert castfit.is_subtype(Sequence[Dog], Sequence[Animal])
    assert castfit.is_subtype(Mapping[Dog, Dog], Mapping[Dog, Animal])
    assert not castfit.is_subtype(
        Mapping[Dog, Dog], Mapping[Animal, Animal]
    ), "keys are invariant"

    T = TypeVar("T")
    T_co = TypeVar("T_co", covariant=True)
    T_contra = TypeVar("T_contra", contravariant=True)

    class Inv(Generic[T]): ...

    class Cov(Generic[T_co]): ...

    class Contra(Generic[T_contra]): ...

    assert not castfit.is_subtype(Inv[Dog], Inv[Animal])
    assert castfit.is_subtype(Inv[Dog], Inv[Dog])
    assert not castfit.is_subtype(Inv[Dog], Inv[Labrador])

    assert castfit.is_subtype(Cov[Dog], Cov[Animal])
    assert castfit.is_subtype(Cov[Dog], Cov[Dog])
    assert not castfit.is_subtype(Cov[Dog], Cov[Labrador])

    assert not castfit.is_subtype(Contra[Dog], Contra[Animal])
    assert castfit.is_subtype(Contra[Dog], Contra[Dog])
    assert castfit.is_subtype(Contra[Dog], Contra[Labrador])

    class Cov2(Labrador, Cov[Dog]): ...

    assert castfit.is_subtype(Cov2, Labrador, covariant=True)
