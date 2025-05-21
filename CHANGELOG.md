# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to [Semantic Versioning].

Sections order is: `Fixed`, `Changed`, `Added`, `Deprecated`, `Removed`, `Security`.

[keep a changelog]: http://keepachangelog.com/en/1.0.0/
[semantic versioning]: http://semver.org/spec/v2.0.0.html

---

## [Unreleased]

[unreleased]: https://github.com/metaist/castfit/compare/prod...main

These are changes that are on `main` that are not yet in `prod`.

---

[#2]: https://github.com/metaist/castfit/issues/2
[#3]: https://github.com/metaist/castfit/issues/3
[#4]: https://github.com/metaist/castfit/issues/4
[#5]: https://github.com/metaist/castfit/issues/5
[#6]: https://github.com/metaist/castfit/issues/6
[#7]: https://github.com/metaist/castfit/issues/7
[#8]: https://github.com/metaist/castfit/issues/8
[#9]: https://github.com/metaist/castfit/issues/9
[#10]: https://github.com/metaist/castfit/issues/10
[#11]: https://github.com/metaist/castfit/issues/11
[#12]: https://github.com/metaist/castfit/issues/12
[#13]: https://github.com/metaist/castfit/issues/13
[#14]: https://github.com/metaist/castfit/issues/14
[#15]: https://github.com/metaist/castfit/issues/15
[#16]: https://github.com/metaist/castfit/issues/16
[#17]: https://github.com/metaist/castfit/issues/17
[#18]: https://github.com/metaist/castfit/issues/18
[#19]: https://github.com/metaist/castfit/issues/19
[#20]: https://github.com/metaist/castfit/issues/20
[#21]: https://github.com/metaist/castfit/issues/21
[#22]: https://github.com/metaist/castfit/issues/22
[#23]: https://github.com/metaist/castfit/issues/23
[#24]: https://github.com/metaist/castfit/issues/24
[#25]: https://github.com/metaist/castfit/issues/25
[#26]: https://github.com/metaist/castfit/issues/26
[#27]: https://github.com/metaist/castfit/issues/27
[#28]: https://github.com/metaist/castfit/issues/28
[#29]: https://github.com/metaist/castfit/issues/29
[#30]: https://github.com/metaist/castfit/issues/30
[#31]: https://github.com/metaist/castfit/issues/31
[#32]: https://github.com/metaist/castfit/issues/32
[0.1.2]: https://github.com/metaist/castfit/compare/0.1.1...0.1.2

## [0.1.2] - 2025-05-21T20:54:51Z

**Fixed**

- [#4]: `get_args` on raw types
- [#5]: `to_tuple` with too-long input
- [#18]: handling of `types.UnionType`
- [#25]: delinted using `pyrefly`
- [#27]: `str` to `int` conversion when the string has decimal places
- [#28]: `float` to `datetime` conversion; added UTC timezone
- [#29]: handling an untyped default value in a class

**Changed**

- [#14]: `TypeForm` comment to clarify what we want
- [#19]: set instance fields based on class metadata rather than tried to put all the data into the instance
- [#22]: register converters based on both source and destination types rather than assuming that each function must convert everything to a specific destination type
- [#24]: renamed `casts_to` to `casts` and added support for short-form (1 argument) cast function
- [#30]: updated the public API to be more compact and consistent

**Added**

- [#2]: support for nested types
- [#3]: original cause of `to_type` error
- [#6]: additional `datetime` formats
- [#7]: custom casts to `castfit` (closes #7)
- [#11]: more README examples
- [#12]: more complete docstrings for the public API
- [#15]: cache for fetching `get_origin` and `get_args` information
- [#16]: `DEFAULT_ENCODING` constant for `to_bytes` and `to_str`
- [#17]: alternatives to README
- [#20]: infer types based on class field defaults
- [#31]: more negative tests

**Removed**

- [#21]: `castfit` on an instance instead of a `type`

**Won't Fix**

- [#8]: Gemini suggested having an explicit caster for `pathlib.Path`
- [#9]: Gemini suggested having an explicit recursive dataclass/class casting
- [#10]: Gemini suggested optionally collecting errors instead of raising the first one encountered. It's a good idea, but not for now.
- [#13]: Tried implementing a workaround for `TypeGuard` in older versions of python, but it didn't work.
- [#23]: Started and rolled back `is_callable` because `castfit` can't currently do anything with a callable that is the wrong type.
- [#26]: Rolled back having a `checks` parameter that overrides how types are checked.
- [#32]: Tried fixing `TypeForm` to be the union of `type[T]` and `_SpecialForm`, but only `pyright` was able to handle it. `mypy` still can't handle it and `ty` isn't mature enough yet.

---

[#1]: https://github.com/metaist/castfit/issues/1
[metaist/LTS#8]: https://github.com/metaist/LTS/issues/8
[0.1.1]: https://github.com/metaist/castfit/compare/0.1.0...0.1.1

## [0.1.1] - 2025-04-28T14:32:37Z

**Fixed**

- [#1]: type hints for `castfit`

**Changed**

- [metaist/LTS#8]: using latest github actions

---

[0.1.0]: https://github.com/metaist/castfit/commits/0.1.0

## [0.1.0] - 2023-12-15T12:12:04Z

Initial release.
