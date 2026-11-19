"""humanize.naturalsize, rewritten with plainly.

Run `pytest --plainly` to read this file as a list of sentences.
"""

from humanize import naturalsize

from plainly import expect, spec

rule = spec(naturalsize)

DECIMAL_UNITS = ["kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB", "RB", "QB"]
BINARY_UNITS = ["KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB", "RiB", "QiB"]


def test_small_values_are_shown_as_plain_bytes():
    rule.if_(0).then_give("0 Bytes")
    rule.if_(1).then_give("1 Byte")
    rule.if_(1.0).then_give("1 Byte")
    rule.if_("1").then_give("1 Byte")
    rule.if_(300).then_give("300 Bytes")
    rule.if_(999).then_give("999 Bytes")
    rule.if_(1.123456789).then_give("1 Bytes")


def test_decimal_is_the_default_and_uses_powers_of_1000():
    rule.if_("1000").then_give("1.0 kB")
    rule.if_(10**3).then_give("1.0 kB")
    rule.if_(10**6).then_give("1.0 MB")
    rule.if_(10**9).then_give("1.0 GB")
    rule.if_(10**12).then_give("1.0 TB")
    rule.if_(10**15).then_give("1.0 PB")
    rule.if_(10**18).then_give("1.0 EB")
    rule.if_(10**21).then_give("1.0 ZB")
    rule.if_(10**24).then_give("1.0 YB")
    rule.if_(10**27).then_give("1.0 RB")
    rule.if_(10**30).then_give("1.0 QB")
    rule.if_(1.123456789 * 10**3).then_give("1.1 kB")
    rule.if_(1.123456789 * 10**6).then_give("1.1 MB")
    rule.if_(3141592).then_give("3.1 MB")
    rule.if_(10**34 * 3).then_give("30000.0 QB")


def test_every_decimal_unit_is_reachable():
    # 31 kB, 32 MB, 33 GB ... 40 QB
    for i, unit in enumerate(DECIMAL_UNITS):
        rule.if_(1000 ** (i + 1) * (31 + i)).then_give(f"{31 + i}.0 {unit}")


def test_binary_uses_powers_of_1024_and_iec_names():
    rule.if_(300, True).then_give("300 Bytes")
    rule.if_(1023, True).then_give("1023 Bytes")
    rule.if_(1024, True).then_give("1.0 KiB")
    for i, unit in enumerate(BINARY_UNITS):
        rule.if_(1024 ** (i + 1) * (31 + i), True).then_give(f"{31 + i}.0 {unit}")


def test_binary_converts_decimal_amounts():
    for i, text in enumerate(
        [
            "30.3 KiB",
            "30.5 MiB",
            "30.7 GiB",
            "30.9 TiB",
            "31.1 PiB",
            "31.2 EiB",
            "31.3 ZiB",
            "31.4 YiB",
            "31.5 RiB",
            "31.6 QiB",
        ]
    ):
        rule.if_(1000 ** (i + 1) * (31 + i), True).then_give(text)


def test_gnu_style_uses_one_letter_suffixes_with_no_space():
    rule.if_(0, gnu=True).then_give("0B")
    rule.if_(300, gnu=True).then_give("300B")
    rule.if_(1.123456789, gnu=True).then_give("1B")
    rule.if_(3000, gnu=True).then_give("2.9K")
    rule.if_(1024, gnu=True).then_give("1.0K")
    rule.if_(3000000, gnu=True).then_give("2.9M")
    rule.if_(1.123456789 * 10**3, gnu=True).then_give("1.1K")
    rule.if_(1.123456789 * 10**6, gnu=True).then_give("1.1M")
    for i, text in enumerate(
        ["30.3K", "30.5M", "30.7G", "30.9T", "31.1P", "31.2E", "31.3Z", "31.4Y", "31.5R", "31.6Q"]
    ):
        rule.if_(1000 ** (i + 1) * (31 + i), gnu=True).then_give(text)


def test_gnu_wins_over_binary_when_both_are_asked_for():
    spec(naturalsize).if_(3000, binary=True, gnu=True).then_give("2.9K")


def test_a_custom_format_controls_the_decimals():
    rule.if_(3141592, format="%.2f").then_give("3.14 MB")
    rule.if_(3000, gnu=True, format="%.3f").then_give("2.930K")
    rule.if_(3000000000, gnu=True, format="%.0f").then_give("3G")
    rule.if_(10**26 * 30, binary=True, format="%.3f").then_give("2.423 RiB")


def test_rounding_up_to_the_next_unit_carries_over():
    # 999999 bytes is 999.999 kB: it must read "1.0 MB", never "1000.0 kB"
    rule.if_(999999).then_give("1.0 MB")
    rule.if_(999999999).then_give("1.0 GB")
    rule.if_(999999999999).then_give("1.0 TB")
    rule.if_(1024**2 - 1, True).then_give("1.0 MiB")
    rule.if_(1024**3 - 1, True).then_give("1.0 GiB")
    rule.if_(1024**2 - 1, gnu=True).then_give("1.0M")


def test_negative_sizes_are_the_positive_text_with_a_minus_sign():
    for size in [1, 300, 10**3, 10**6, 31 * 1000, 3141592, 10**30]:
        expect(naturalsize(-size), f"naturalsize(-{size})").should.be("-" + naturalsize(size))
    expect(naturalsize(-4096, True)).should.be("-4.0 KiB")
    expect(naturalsize("-1000")).should.be("-1.0 kB")


def test_text_that_is_not_a_number_is_rejected():
    spec(naturalsize).if_("abc").then_raise(ValueError)
    spec(naturalsize).if_(None).then_raise(TypeError)
