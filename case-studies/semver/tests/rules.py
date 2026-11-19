"""Adapters so every semver rule reads as text in, text out.

semver works on Version objects; a reviewer should not have to read object construction.
Each rule below takes version *strings* and gives back strings, numbers or booleans.
"""

import operator

import semver
from semver import Version

from plainly import compact, method, spec


def on_version(name, result=str):
    """Rule for a Version method: build the version from the first input, call `name`, show the result as text."""
    return spec(method(Version.parse, name, result))


def parts_of(text, **options):
    return Version.parse(text, **options).to_tuple()


# the version, split into (major, minor, patch, prerelease, build)
parse = spec(parts_of, name="parse")
parse_with_optional_minor_and_patch = spec(
    lambda text: parts_of(text, optional_minor_and_patch=True),
    name="parse (minor and patch optional)",
)


def _compare_with(symbol, function):
    return spec(
        lambda a, b: function(Version.parse(a), Version.parse(b)),
        says="Version({}) " + symbol + " Version({})",
        show=compact,
    )


is_less_than = _compare_with("<", operator.lt)
is_less_or_equal = _compare_with("<=", operator.le)
is_greater_than = _compare_with(">", operator.gt)
is_greater_or_equal = _compare_with(">=", operator.ge)
is_equal = _compare_with("==", operator.eq)
is_different = _compare_with("!=", operator.ne)

# oldest to newest, as text
sorted_versions = spec(
    lambda *texts: [str(v) for v in sorted(Version.parse(t) for t in texts)], name="sort", show=compact
)
