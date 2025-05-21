# castfit: basic type casting

<!--
[[[cog from cog_helpers import * ]]]
[[[end]]]
-->
<p align="center">
  <a href="https://metaist.github.io/castfit/"><img alt="Cuddles the Cat" width="200" src="https://raw.githubusercontent.com/metaist/castfit/main/cats-fit.png" /></a><br />
  <em>Cuddles the Cat<br />
  "If it fits, I sits."</em>
</p>
<p align="center">
  <a href="https://github.com/metaist/castfit/actions/workflows/ci.yaml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/metaist/castfit/.github/workflows/ci.yaml?branch=main&logo=github"/></a>
  <a href="https://pypi.org/project/castfit"><img alt="PyPI" src="https://img.shields.io/pypi/v/castfit.svg?color=blue" /></a>
  <a href="https://pypi.org/project/castfit"><img alt="Supported Python Versions" src="https://img.shields.io/pypi/pyversions/castfit" /></a>
</p>

## Why?

`castfit` helps you convert things like command-line arguments (e.g., from [`docopt`](https://github.com/docopt/docopt)) and simple API responses into something more typed with low overhead.

## Install

```bash
# modern (recommended)
uv add castfit

# classic
python -m pip install castfit
```

Alternatively, you can just [download the single file](https://raw.githubusercontent.com/metaist/castfit/main/src/castfit/__init__.py) and name it `castfit.py`.

## Example: CLI-like Args

<!--[[[cog insert_file("examples/cli_args.py")]]]-->

```py
# Example: CLI-like args
from typing import Optional
from pathlib import Path
from castfit import castfit


class Args:
    host: str
    port: int
    timeout: Optional[float]
    log: Path


data = {
    "host": "localhost",
    "port": "8080",
    # "timeout": "5.0" # key can be missing
    "log": "app.log",
}

config = castfit(Args, data)
assert config.host == "localhost"
assert config.port == 8080
assert config.timeout is None
assert config.log == Path("app.log")

# if timeout was present:
data = {"host": "localhost", "port": "8080", "timeout": "5.0", "log": "app.log"}
config = castfit(Args, data)
assert config.host == "localhost"
assert config.port == 8080
assert config.timeout == 5.0
assert config.log == Path("app.log")
```

<!--[[[end]]]-->

## Example: Nested Types

<!--[[[cog insert_file("examples/nested.py")]]]-->

```py
# Example: nested types
from dataclasses import dataclass
from typing import Literal
from castfit import castfit


@dataclass
class Pet:
    name: str
    type: Literal["cat", "dog", "other"]
    age: int


@dataclass
class Owner:
    name: str
    pets: list[Pet]


owner_data = {
    "name": "Alice",
    "pets": [
        {"name": "Cuddles", "type": "cat", "age": "4"},
        {"name": "Buddy", "type": "dog", "age": "2.5"},  # age will be cast to int(2)
    ],
}

owner = castfit(Owner, owner_data)

assert owner.name == "Alice"
assert len(owner.pets) == 2
assert isinstance(owner.pets[0], Pet)
assert owner.pets[0].name == "Cuddles"
assert owner.pets[0].type == "cat"
assert owner.pets[0].age == 4
assert owner.pets[1].name == "Buddy"
assert owner.pets[1].age == 2  # Cast from "2.5" to int
```

<!--[[[end]]]-->

## Example: Custom Functions

<!--[[[cog insert_file("examples/custom.py")]]]-->

```py
# Example: adding a custom converter

from dataclasses import dataclass
import castfit


@dataclass
class LatLon:
    lat: float
    lon: float


@castfit.casts
def str_to_latlon(s: str) -> LatLon:
    lat, lon = map(float, s.split(","))
    return LatLon(lat, lon)


assert castfit.to_type("40.7,-74.0", LatLon) == LatLon(40.7, -74.0)
```

<!--[[[end]]]-->

## Other Projects

- [`pydantic`](https://github.com/pydantic/pydantic): comprehensive, but feels heavy.
- [`cattrs`](https://catt.rs/): good simple cases, but has a complex set of converters.

## License

[MIT License](https://github.com/metaist/castfit/blob/main/LICENSE.md)
