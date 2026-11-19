"""The rules every cachetools cache promises, whatever its eviction policy.

Upstream shares these through a mixin that six test classes inherit. Here the same rules run once per
cache class (see the `Cache` fixture in conftest.py), and each run is printed as its own story.
"""

import math

from plainly import expect, given, spec


def size_is_the_value(value):
    return value


def test_a_new_cache_is_empty(Cache):
    cache = given(Cache, maxsize=1)
    cache.then.has_length(0).has(maxsize=1, currsize=0)
    cache.getsizeof(None)
    cache.then.gave(1)
    cache.getsizeof("")
    cache.then.gave(1)
    cache.getsizeof(0)
    cache.then.gave(1)
    expect(repr(cache.unwrap()), "repr(cache)").should.start_with(Cache.__name__)


def test_a_negative_maxsize_is_rejected(Cache):
    rule = spec(Cache)
    rule.if_(maxsize=-1).then_raise(ValueError)
    rule.if_(maxsize=-math.inf).then_raise(ValueError)


def test_a_cache_of_size_zero_stores_nothing(Cache):
    cache = given(Cache, maxsize=0)
    cache.then.has(maxsize=0)
    with cache.raises(ValueError):
        cache[1] = 1
    cache.then.has_length(0).has(currsize=0)


def test_a_cache_of_infinite_size_never_evicts(Cache):
    cache = given(Cache, maxsize=math.inf)
    cache.update((i, i) for i in range(100))
    cache.then.has_length(100).has(currsize=100)


def test_inserting_beyond_maxsize_evicts_something(Cache):
    cache = given(Cache, maxsize=2)
    cache.update({1: 1, 2: 2})
    cache.then.holds({1: 1, 2: 2})
    cache[3] = 3
    cache.then.has_length(2).contains(3).contains_one_of(1, 2)
    cache[4] = 4
    cache.then.has_length(2).contains(4).contains_one_of(1, 2, 3)


def test_update_adds_and_replaces_entries(Cache):
    cache = given(Cache, maxsize=2)
    cache.update({1: 1, 2: 2})
    cache.then.holds({1: 1, 2: 2})
    cache.update({1: 1, 2: 2})
    cache.then.holds({1: 1, 2: 2})
    cache.update({1: "a", 2: "b"})
    cache.then.holds({1: "a", 2: "b"})


def test_deleting_removes_the_entry_and_a_missing_key_is_an_error(Cache):
    cache = given(Cache, maxsize=2)
    cache.update({1: 1, 2: 2})
    del cache[2]
    cache.then.holds({1: 1})
    del cache[1]
    cache.then.holds_nothing()
    with cache.raises(KeyError):
        del cache[1]
    cache.then.holds_nothing()


def test_pop_removes_and_returns_the_value(Cache):
    cache = given(Cache, maxsize=2)
    cache.update({1: 1, 2: 2})
    cache.pop(2)
    cache.then.gave(2).holds({1: 1})
    cache.pop(1)
    cache.then.gave(1).holds_nothing()


def test_pop_of_a_missing_key_is_an_error_unless_a_default_is_given(Cache):
    cache = given(Cache, maxsize=2)
    for key in (2, 1, 0):
        with cache.raises(KeyError):
            cache.pop(key)
        cache.pop(key, None)
        cache.then.gave(None)


def test_popitem_removes_one_entry_at_a_time_until_empty(Cache):
    cache = given(Cache, maxsize=2)
    cache.update({1: 1, 2: 2})
    cache.popitem()
    cache.then.has_length(1)
    cache.popitem()
    cache.then.has_length(0)
    with cache.raises(KeyError):
        cache.popitem()


def test_popitem_on_an_empty_cache_hides_the_internal_cause(Cache):
    cache = given(Cache, maxsize=2)
    with cache.raises(KeyError) as error:
        cache.popitem()
    expect(error.value.__cause__, "the cause of that KeyError").should.be.none()
    expect(error.value.__suppress_context__, "that KeyError hides its context").should.be.true()


def test_missing_keys_can_be_filled_in_by_a_subclass(Cache):
    class DefaultCache(Cache):
        def __missing__(self, key):
            self[key] = key
            return key

    cache = given(DefaultCache, maxsize=2)
    cache.then.has(currsize=0, maxsize=2).has_length(0)
    cache[1]
    cache.then.gave(1)
    cache[2]
    cache.then.gave(2).holds({1: 1, 2: 2})
    cache[3]
    cache.then.gave(3).has_length(2).contains(3).contains_one_of(1, 2)
    cache[4]
    cache.then.gave(4).has_length(2).contains(4)


def test_only_reading_a_key_triggers_the_missing_hook(Cache):
    class DefaultCache(Cache):
        def __missing__(self, key):
            self[key] = key
            return key

    cache = given(DefaultCache, maxsize=2)
    cache[3]
    cache[4]
    cache.get(4)
    cache.then.gave(4)
    cache.get(5)
    cache.then.gave(None)
    cache.get(5, 25)
    cache.then.gave(25).has_length(2)
    cache.pop(4)
    cache.then.gave(4)
    with cache.raises(KeyError):
        cache.pop(5)
    cache.pop(5, None)
    cache.then.gave(None)
    cache.pop(5, 25)
    cache.then.gave(25).has_length(1)


def test_setdefault_stores_only_when_the_key_is_missing(Cache):
    class DefaultCache(Cache):
        def __missing__(self, key):
            self[key] = key
            return key

    cache = given(DefaultCache, maxsize=2)
    cache[1] = 2
    cache.setdefault(1)
    cache.then.gave(2)
    cache.setdefault(1, 1)
    cache.then.gave(2)
    cache.setdefault(2, 4)
    cache.then.gave(4)
    cache.setdefault(2, None)
    cache.then.gave(4)
    cache.then.holds({1: 2, 2: 4})
    cache.setdefault(3)
    cache.then.gave(None).has_length(2).contains(3).contains_one_of(1, 2)


def test_a_value_too_big_for_the_cache_is_left_out_of_the_cache(Cache):
    class DefaultCache(Cache):
        def __missing__(self, key):
            try:
                self[key] = key
            except ValueError:
                pass  # too big to store
            return key

    cache = given(DefaultCache, maxsize=2, getsizeof=size_is_the_value)
    cache[1]
    cache.then.gave(1).has_length(1).has(currsize=1).contains(1)
    cache[2]
    cache.then.gave(2).has_length(1).has(currsize=2).lacks(1).contains(2)
    cache[3]  # size 3 does not fit in 2: it is returned but not stored
    cache.then.gave(3).has_length(1).has(currsize=2)
    cache[1]
    cache.then.gave(1).has_length(1).has(currsize=1)
    cache.popitem()
    cache.then.gave((1, 1))


def _entries_have_a_size(cache):
    cache.then.has(currsize=0, maxsize=3)
    cache.getsizeof(1)
    cache.then.gave(1)
    cache.getsizeof(2)
    cache.then.gave(2)
    cache.getsizeof(3)
    cache.then.gave(3)

    cache.update({1: 1, 2: 2})
    cache.then.holds({1: 1, 2: 2}).has(currsize=3)

    cache[1] = 2  # replaces the size-1 entry with a size-2 one
    cache.then.holds({1: 2}).has(currsize=2).lacks(2)

    cache.update({1: 1, 2: 2})
    cache.then.holds({1: 1, 2: 2}).has(currsize=3)

    cache[3] = 3  # needs the whole cache
    cache.then.holds({3: 3}).has(currsize=3)

    with cache.raises(ValueError):
        cache[3] = 4  # bigger than the whole cache
    cache.then.holds({3: 3}).has(currsize=3)
    with cache.raises(ValueError):
        cache[4] = 4
    cache.then.holds({3: 3}).has(currsize=3)


def test_entries_have_a_size_given_as_a_parameter(Cache):
    _entries_have_a_size(given(Cache, maxsize=3, getsizeof=size_is_the_value))


def test_entries_have_a_size_given_by_a_subclass(Cache):
    class SizedCache(Cache):
        @staticmethod
        def getsizeof(value):
            return value

    _entries_have_a_size(given(SizedCache, maxsize=3))


def test_replacing_an_entry_with_a_bigger_one_only_needs_the_extra_space(Cache):
    cache = given(Cache, maxsize=10, getsizeof=size_is_the_value)
    cache[3] = 3
    cache[4] = 4
    cache.then.has_length(2).has(currsize=7)
    cache[4] = 7
    cache.then.holds({3: 3, 4: 7}).has(currsize=10)
    cache[4] = 9  # now something else has to go
    cache.then.holds({4: 9}).has(currsize=9).lacks(3)


def test_replacing_an_entry_with_one_of_the_same_size_changes_nothing_else(Cache):
    cache = given(Cache, maxsize=10, getsizeof=size_is_the_value)
    cache[3] = 3
    cache[4] = 4
    cache.then.has(currsize=7)
    cache[4] = 4
    cache.then.holds({3: 3, 4: 4}).has(currsize=7)


def test_replacing_an_entry_with_a_smaller_one_frees_space(Cache):
    cache = given(Cache, maxsize=10, getsizeof=size_is_the_value)
    cache[3] = 3
    cache[4] = 4
    cache.then.has(currsize=7)
    cache[4] = 1
    cache.then.holds({3: 3, 4: 1}).has(currsize=4)


def test_a_negative_size_is_rejected_and_nothing_is_stored(Cache):
    cache = given(Cache, maxsize=3, getsizeof=lambda value: -1)
    with cache.raises(ValueError):
        cache[1] = 1
    cache.then.has_length(0).has(currsize=0)


def test_clearing_empties_the_cache_and_it_can_be_used_again(Cache):
    cache = given(Cache, maxsize=2)
    cache.update({1: 1, 2: 2})
    cache.then.has_length(2).has(currsize=2)
    cache.clear()
    cache.then.holds_nothing().has(currsize=0).lacks(1, 2)
    cache[3] = 3
    cache[4] = 4
    cache.then.holds({3: 3, 4: 4})
    cache[5] = 5  # eviction still works after a clear
    cache.then.has_length(2).contains(5)


def test_clearing_an_empty_cache_is_fine(Cache):
    cache = given(Cache, maxsize=2)
    cache.clear()
    cache.then.has_length(0).has(currsize=0)


def test_clearing_resets_the_used_size(Cache):
    cache = given(Cache, maxsize=10, getsizeof=size_is_the_value)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache.then.has_length(3).has(currsize=6)
    cache.clear()
    cache.then.has_length(0).has(currsize=0)
    cache[4] = 4  # still usable afterwards, with sizes
    cache.then.has_length(1).has(currsize=4)


def test_updating_entries_while_looping_visits_each_key_once_in_order(Cache):
    cache = given(Cache, maxsize=3)
    cache.update({1: 1, 2: 2, 3: 3})
    visited = []
    for key in cache:
        visited.append(key)
        cache[key] = key * 10
    expect(visited, "keys visited while updating every entry").should.be([1, 2, 3])
    expect(list(cache.values()), "values afterwards").should.be([10, 20, 30])


# ----- copies ----------------------------------------------------------------


def test_a_copy_has_the_same_content_but_its_own_state(Cache, duplicate):
    source = given(Cache, maxsize=2)
    source.update({1: 1, 2: 2})
    cache = given(duplicate(source.unwrap()), described_as="a copy of that cache")
    expect(cache.unwrap() is source.unwrap(), "the copy is the same object as the source").should.be.false()
    expect(cache.unwrap() == source.unwrap(), "the copy equals the source").should.be.true()
    cache.then.has(maxsize=2, currsize=2).holds({1: 1, 2: 2})
    cache[3] = 3
    cache.then.has_length(2).has(currsize=2).contains(3).contains_one_of(1, 2)
    source.then.holds({1: 1, 2: 2}).has(currsize=2).lacks(3)


def test_copies_of_copies_are_equal_too(Cache, duplicate):
    source = given(Cache, maxsize=2)
    source.update({1: 1, 2: 2})
    cache = duplicate(source.unwrap())
    expect(duplicate(cache) == cache, "a copy of the copy equals the copy").should.be.true()


def test_copying_works_for_empty_one_entry_and_very_large_caches(Cache, duplicate):
    for n in [0, 1, 2000]:
        source = Cache(maxsize=n)
        source.update((i, i) for i in range(n))
        cache = duplicate(source)
        expect(len(cache), f"size of a copy of a cache with {n} entries").should.be(n)
        expect(cache == source, f"a copy of a cache with {n} entries equals its source").should.be.true()


def test_a_shallow_copy_shares_attributes_and_values_but_not_the_cache_state(Cache):
    import copy
    import threading

    class CacheWithExtras(Cache):
        def __init__(self, maxsize, **kwargs):
            super().__init__(maxsize, **kwargs)
            self.lock = threading.Lock()  # cannot be deep-copied
            self.stats = {"hits": 0}

    source = given(CacheWithExtras, maxsize=2)
    source.update({1: [1], 2: [2]})
    cache = given(copy.copy(source.unwrap()), described_as="a shallow copy of that cache")
    expect(type(cache.unwrap()) is type(source.unwrap()), "the copy has the same type").should.be.true()
    expect(cache.lock is source.lock, "the copy shares the lock").should.be.true()
    expect(cache.stats is source.stats, "the copy shares the stats").should.be.true()
    expect(cache.unwrap()[1] is source.unwrap()[1], "the copy shares the value of 1").should.be.true()
    expect(cache.unwrap()[2] is source.unwrap()[2], "the copy shares the value of 2").should.be.true()
    cache[3] = [3]
    del cache[next(iter(cache))]
    cache.then.has_length(1)
    source.then.has_length(2).has(currsize=2).contains(1, 2).lacks(3)


def test_a_shallow_copy_keeps_its_own_record_of_entry_sizes(Cache):
    import copy

    class SizeOf:
        def __call__(self, value):
            return value

    source = given(Cache, maxsize=3, getsizeof=SizeOf())
    source.update({1: 1, 2: 2})
    cache = given(copy.copy(source.unwrap()), described_as="a shallow copy of that cache")
    expect(
        cache.unwrap().getsizeof is source.unwrap().getsizeof, "the copy uses the same getsizeof"
    ).should.be.true()
    cache.then.has(currsize=3)
    cache[2] = 1
    cache.then.has(currsize=2)
    source.then.has(currsize=3)
    del source[2]
    source.then.has(currsize=1)
    cache.then.has(currsize=2)
    del cache[2]
    cache.then.has(currsize=1)
