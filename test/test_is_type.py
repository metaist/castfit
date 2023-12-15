# std
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union
from typing import NoReturn

# pkg
import castfit
from castfit import Never


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


def test_empty() -> None:
    """Empty containers match."""
    assert castfit.is_type(dict(), Dict[str, int])
    assert castfit.is_type(list(), List[int])
    assert castfit.is_type(set(), Set[int])


def test_list() -> None:
    """Every item in the list or set must match."""
    assert castfit.is_type([1], List[int])
    assert castfit.is_type({6, 7}, Set[int])

    assert castfit.is_type([3, 5, "test", "fun"], List[Union[int, str]])

    assert not castfit.is_type([1], Set[int])
    assert not castfit.is_type({1}, List[int])


def test_tuple() -> None:
    """Every item in the tuple must match."""
    assert castfit.is_type((), Tuple)
    assert castfit.is_type((), Tuple[()])
    assert castfit.is_type((3, "yes", 7.5), Tuple[int, str, float])
    assert castfit.is_type((1, 2, 3), Tuple[int, ...])

    assert not castfit.is_type([], Tuple)


def test_dict() -> None:
    """Keys and values must match."""
    assert castfit.is_type({"field": 2.0}, Dict[str, float])
    assert castfit.is_type({"x": 1, "y": "test"}, Dict[str, Union[int, str]])

    assert castfit.is_type({("x", 1): ["z"]}, Dict[Tuple[str, int], List[str]])
    assert not castfit.is_type([], Dict[str, str])


def test_datetime() -> None:
    """Check datetime objects."""
    assert castfit.is_type(datetime.now(), datetime)
