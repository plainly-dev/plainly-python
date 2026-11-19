"""cachetools.keys: the keys that decorators build from function arguments."""

import pickle

from cachetools.keys import hashkey, methodkey, typedkey, typedmethodkey

from plainly import expect, spec


def same(key, a, b):
    return key(*a[0], **a[1]) == key(*b[0], **b[1])


def hashes_alike(key, a, b):
    return hash(key(*a[0], **a[1])) == hash(key(*b[0], **b[1]))


def call(*args, **kwargs):
    return (args, kwargs)


def test_hashkey_is_the_same_for_the_same_arguments():
    key = spec(lambda a, b: same(hashkey, a, b), says="hashkey{0} == hashkey{1}")
    for args in [call(), call(1, 2, 3), call(1, 2, 3, x=0)]:
        key.if_(args, args).then_give(True)
    hashed = spec(lambda a, b: hashes_alike(hashkey, a, b), says="hash(hashkey{0}) == hash(hashkey{1})")
    for args in [call(), call(1, 2, 3), call(1, 2, 3, x=0)]:
        hashed.if_(args, args).then_give(True)


def test_hashkey_differs_when_the_arguments_differ():
    key = spec(lambda a, b: same(hashkey, a, b), says="hashkey{0} == hashkey{1}")
    key.if_(call(1, 2, 3), call(3, 2, 1)).then_give(False)
    key.if_(call(1, 2, 3), call(1, 2, 3, x=None)).then_give(False)
    key.if_(call(1, 2, 3, x=0), call(1, 2, 3, x=None)).then_give(False)
    key.if_(call(1, 2, 3, x=0), call(1, 2, 3, y=0)).then_give(False)


def test_hashkey_treats_numbers_that_are_equal_as_equal():
    key = spec(lambda a, b: same(hashkey, a, b), says="hashkey{0} == hashkey{1}")
    hashed = spec(lambda a, b: hashes_alike(hashkey, a, b), says="hash(hashkey{0}) == hash(hashkey{1})")
    key.if_(call(1, 2, 3), call(1.0, 2.0, 3.0)).then_give(True)
    hashed.if_(call(1, 2, 3), call(1.0, 2.0, 3.0)).then_give(True)


def test_hashkey_cannot_be_made_from_something_that_cannot_be_hashed():
    spec(lambda: hash(hashkey({})), name="hash(hashkey({}))").if_().then_raise(TypeError)


def test_methodkey_ignores_the_first_argument():
    key = spec(lambda a, b: same(methodkey, a, b), says="methodkey{0} == methodkey{1}")
    hashed = spec(lambda a, b: hashes_alike(methodkey, a, b), says="hash(methodkey{0}) == hash(methodkey{1})")
    for x, y in [
        (call("x"), call("y")),
        (call("x", 1, 2, 3), call("y", 1, 2, 3)),
        (call("x", 1, 2, 3, x=0), call("y", 1, 2, 3, x=0)),
    ]:
        key.if_(x, y).then_give(True)
        hashed.if_(x, y).then_give(True)


def test_methodkey_still_tells_the_other_arguments_apart():
    key = spec(lambda a, b: same(methodkey, a, b), says="methodkey{0} == methodkey{1}")
    key.if_(call("x", 1, 2, 3), call("x", 3, 2, 1)).then_give(False)
    key.if_(call("x", 1, 2, 3), call("x", 1, 2, 3, x=None)).then_give(False)
    key.if_(call("x", 1, 2, 3, x=0), call("x", 1, 2, 3, x=None)).then_give(False)
    key.if_(call("x", 1, 2, 3, x=0), call("x", 1, 2, 3, y=0)).then_give(False)
    key.if_(call("x", 1, 2, 3), call("y", 1.0, 2.0, 3.0)).then_give(True)


def test_methodkey_accepts_self_as_a_keyword_too():
    key = spec(lambda a, b: same(methodkey, a, b), says="methodkey{0} == methodkey{1}")
    key.if_(call("x", self=1), call("y", self=1)).then_give(True)
    key.if_(call("x", self=1), call("x")).then_give(False)


def test_methodkey_cannot_be_made_from_something_that_cannot_be_hashed():
    spec(lambda: hash(methodkey("x", {})), name='hash(methodkey("x", {}))').if_().then_raise(TypeError)


def test_typedkey_tells_equal_numbers_of_different_types_apart():
    key = spec(lambda a, b: same(typedkey, a, b), says="typedkey{0} == typedkey{1}")
    key.if_(call(1, 2, 3), call(1, 2, 3)).then_give(True)
    key.if_(call(1, 2, 3, x=0), call(1, 2, 3, x=0)).then_give(True)
    key.if_(call(1, 2, 3), call(1.0, 2.0, 3.0)).then_give(False)
    key.if_(call(1, 2, 3, x=0), call(1, 2, 3, x=0.0)).then_give(False)
    key.if_(call(1, 2, 3, x=0), call(1, 2, 3, x=False)).then_give(False)
    key.if_(call(1, 2, 3), call(3, 2, 1)).then_give(False)
    key.if_(call(1, 2, 3, x=0), call(1, 2, 3, y=0)).then_give(False)
    spec(lambda: hash(typedkey({})), name="hash(typedkey({}))").if_().then_raise(TypeError)


def test_typedmethodkey_ignores_the_first_argument_but_not_the_types_of_the_rest():
    key = spec(lambda a, b: same(typedmethodkey, a, b), says="typedmethodkey{0} == typedmethodkey{1}")
    key.if_(call("x"), call("y")).then_give(True)
    key.if_(call("x", 1, 2, 3), call("y", 1, 2, 3)).then_give(True)
    key.if_(call("x", 1, 2, 3), call("x", 1.0, 2.0, 3.0)).then_give(False)
    key.if_(call("x", 1, 2, 3, x=0), call("x", 1, 2, 3, x=False)).then_give(False)
    key.if_(call("x", self=1), call("y", self=1)).then_give(True)
    key.if_(call("x", self=1), call("x", self=1.0)).then_give(False)
    spec(lambda: hash(typedmethodkey("x", {})), name='hash(typedmethodkey("x", {}))').if_().then_raise(
        TypeError
    )


def test_adding_keys_together_gives_a_key():
    expect(
        type(hashkey(1, 2, 3) + hashkey(4, 5, 6)) is type(hashkey()),
        "hashkey(1, 2, 3) + hashkey(4, 5, 6) is a key",
    ).should.be.true()
    expect(
        type(hashkey(1, 2, 3) + (4, 5, 6)) is type(hashkey()), "hashkey(1, 2, 3) + (4, 5, 6) is a key"
    ).should.be.true()
    expect(
        type((1, 2, 3) + hashkey(4, 5, 6)) is type(hashkey()), "(1, 2, 3) + hashkey(4, 5, 6) is a key"
    ).should.be.true()


def test_a_key_survives_pickling_with_the_same_hash():
    for key in [hashkey(), hashkey("abc"), hashkey("abc", 123), hashkey("abc", q="abc")]:
        again = pickle.loads(pickle.dumps(key))
        expect(again == key, f"{key!r} after pickling equals itself").should.be.true()
        expect(
            hash(again) == hash(key) == hash(tuple(key)), f"{key!r} keeps its hash after pickling"
        ).should.be.true()
