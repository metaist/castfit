# castfit: basic type casting

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
uv add castfit

# old school:
python -m pip install castfit
```

Alternatively, you can just [download the single file](https://raw.githubusercontent.com/metaist/castfit/main/src/castfit/__init__.py) and name it `castfit.py`.

## Example

```python
from pathlib import Path
from castfit import castfit

class Cat:
  name: str
  age: int
  weight: float
  logo: Path

bob = castfit(Cat, dict(name="Bob", age="4", weight="3.2", logo="./bob.png"))
assert bob.name == "Bob"
assert bob.age == 4
assert bob.weight == 3.2
assert bob.logo == Path("./bob.png")
```

## Other Projects

- [`pydantic`](https://github.com/pydantic/pydantic) feels heavy.
- [`cattrs`](https://catt.rs/) requires classes to be decorated in a very specific way.
- [`type-docopt`](https://github.com/dreamgonfly/type-docopt) uses a new syntax.
- [`bottle`](https://github.com/bottlepy/bottle) seems like good inspiration for small, useful libraries.

## License

[MIT License](https://github.com/metaist/castfit/blob/main/LICENSE.md)
