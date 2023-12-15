# castfit

_Basic type casting._

[![Build Status](https://img.shields.io/github/actions/workflow/status/metaist/castfit/.github/workflows/ci.yaml?branch=main&style=for-the-badge)](https://github.com/metaist/castfit/actions)
[![castfit on PyPI](https://img.shields.io/pypi/v/castfit.svg?color=blue&style=for-the-badge)](https://pypi.org/project/castfit)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/castfit?style=for-the-badge)](https://pypi.org/project/castfit)

[Changelog] - [Issues] - [Documentation]

[changelog]: https://github.com/metaist/castfit/blob/main/CHANGELOG.md
[issues]: https://github.com/metaist/castfit/issues
[documentation]: https://metaist.github.io/castfit/

## Why?

I'm writing more and more type-checked code, but I often get a bunch of strings I need to convert (e.g., from [`docopt`](https://github.com/docopt/docopt)).

- [`pydantic`](https://github.com/pydantic/pydantic) feels heavy.
- [`type-docopt`](https://github.com/dreamgonfly/type-docopt) uses a new syntax.
- [`bottle`](https://github.com/bottlepy/bottle) seems like good inspiration for small, useful libraries.

## Install

```bash
python -m pip install castfit
```

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

## License

[MIT License](https://github.com/metaist/castfit/blob/main/LICENSE.md)
