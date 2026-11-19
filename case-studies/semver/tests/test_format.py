"""semver.finalize_version, format_version and repr, rewritten with plainly."""

from semver import Version, finalize_version, format_version

from plainly import spec

finalize = spec(finalize_version)
format_ = spec(format_version, name="format_version")
show = spec(lambda text: repr(Version.parse(text)), name="repr")


def test_finalizing_drops_the_prerelease_and_the_build():
    finalize.if_("1.2.3").then_give("1.2.3")
    finalize.if_("1.2.3-rc.5").then_give("1.2.3")
    finalize.if_("1.2.3+build.2").then_give("1.2.3")
    finalize.if_("1.2.3-rc.1+build.5").then_give("1.2.3")
    finalize.if_("1.2.3-alpha").then_give("1.2.3")
    finalize.if_("1.2.0").then_give("1.2.0")


def test_format_version_joins_the_parts():
    format_.if_(3, 4, 5).then_give("3.4.5")
    format_.if_(3, 4, 5, "rc.1").then_give("3.4.5-rc.1")
    format_.if_(3, 4, 5, prerelease="rc.1").then_give("3.4.5-rc.1")
    format_.if_(3, 4, 5, build="build.4").then_give("3.4.5+build.4")
    format_.if_(3, 4, 5, "rc.1", "build.4").then_give("3.4.5-rc.1+build.4")


def test_repr_shows_every_part():
    show.if_("1.2.3").then_give("Version(major=1, minor=2, patch=3, prerelease=None, build=None)")
    show.if_("1.2.3-r.1").then_give("Version(major=1, minor=2, patch=3, prerelease='r.1', build=None)")
    show.if_("1.2.3-dev.1").then_give("Version(major=1, minor=2, patch=3, prerelease='dev.1', build=None)")
    show.if_("1.2.3-dev.1+b.1").then_give(
        "Version(major=1, minor=2, patch=3, prerelease='dev.1', build='b.1')"
    )
    show.if_("1.2.3-r.1+build.1").then_give(
        "Version(major=1, minor=2, patch=3, prerelease='r.1', build='build.1')"
    )
