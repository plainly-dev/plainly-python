"""What each eviction policy throws out first: FIFO, LRU, LFU and random."""

import copy
import sys

from cachetools import FIFOCache, LFUCache, LRUCache, RRCache

from plainly import expect, given, spec


def size_is_the_value(value):
    return value


# ===== FIFO: first in, first out =============================================


def test_fifo_evicts_the_oldest_entry_even_if_it_was_just_read():
    cache = given(FIFOCache, maxsize=2)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache.then.holds_keys(2, 3)
    cache[2]
    expect(copy.copy(cache.unwrap()).popitem(), "a copy of the cache, evicting").should.be((2, 2))
    cache[4] = 4
    cache.then.holds_keys(3, 4).lacks(2)
    cache[5] = 5
    cache.then.holds_keys(4, 5).lacks(3)


def test_fifo_with_sizes_evicts_oldest_entries_until_the_new_one_fits():
    cache = given(FIFOCache, maxsize=3, getsizeof=size_is_the_value)
    cache[1] = 1
    cache[2] = 2
    cache.then.has_length(2)
    cache[3] = 3
    cache.then.holds_keys(3).lacks(1, 2)
    with cache.raises(ValueError):
        cache[4] = 4
    cache.then.holds_keys(3)


def test_fifo_replacing_a_value_does_not_make_it_newer():
    cache = given(FIFOCache, maxsize=2)
    cache[1] = 1
    cache[2] = 2
    cache[1] = "updated"
    cache[3] = 3
    cache.then.contains(3).lacks(2)
    cache[1]
    cache.then.gave("updated")


# ===== LRU: least recently used ======================================================


def test_lru_evicts_the_entry_that_was_used_longest_ago():
    cache = given(LRUCache, maxsize=2)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache.then.holds_keys(2, 3).lacks(1)
    cache[2]  # now 3 is the least recently used
    expect(copy.copy(cache.unwrap()).popitem(), "a copy of the cache, evicting").should.be((3, 3))
    cache[4] = 4
    cache.then.holds_keys(2, 4).lacks(3)
    cache[5] = 5
    cache.then.holds_keys(4, 5).lacks(2)


def test_lru_with_sizes_evicts_old_entries_until_the_new_one_fits():
    cache = given(LRUCache, maxsize=3, getsizeof=size_is_the_value)
    cache[1] = 1
    cache[2] = 2
    cache.then.has_length(2)
    cache[3] = 3
    cache.then.holds_keys(3).lacks(1, 2)
    with cache.raises(ValueError):
        cache[4] = 4
    cache.then.holds_keys(3)


def test_lru_replacing_a_value_counts_as_using_it():
    cache = given(LRUCache, maxsize=2)
    cache[1] = 1
    cache[2] = 2
    cache[1] = "updated"
    cache[3] = 3
    cache.then.contains(3).lacks(2)
    cache[1]
    cache.then.gave("updated")


def test_lru_forgets_the_order_when_cleared():
    cache = given(LRUCache, maxsize=2)
    cache[1] = 1
    cache[2] = 2
    cache.clear()
    cache.then.has_length(0).has(currsize=0)
    cache[3] = 3
    cache[4] = 4
    cache[3]  # 3 is now the most recently used
    cache[5] = 5
    cache.then.holds_keys(3, 5).lacks(4)


# ===== LFU: least frequently used =============================================


def test_lfu_evicts_the_entry_that_was_used_least_often():
    cache = given(LFUCache, maxsize=2)
    cache[1] = 1
    cache[1]
    cache[2] = 2
    cache[3] = 3
    cache.then.has_length(2).contains(1, 3).lacks(2)
    cache[3]
    cache[4] = 4
    cache.then.has_length(2).contains(3, 4).lacks(1)


def test_lfu_breaks_ties_by_evicting_the_oldest_of_the_least_used():
    cache = given(LFUCache, maxsize=3)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache[3]
    cache[2]
    cache[1]
    # every entry has now been used equally often (checked with `in`, which is not a use)
    cache.then.has_length(3).contains(1, 2, 3)
    cache[4] = 4
    cache.then.has_length(3).contains(1, 2, 4).lacks(3)
    cache[4]
    cache[5] = 5
    cache.then.has_length(3).contains(1, 4, 5).lacks(2, 3)


def test_lfu_entries_that_were_never_read_leave_in_the_order_they_came():
    # the set-based implementation used up to v7.2 failed this from key 17 on
    cache = given(LFUCache, maxsize=3)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    for key in range(4, 20):
        cache[key] = key
        cache.then.has_length(3).lacks(key - 3).contains(key - 2, key - 1, key)


def test_lfu_with_sizes_evicts_until_the_new_entry_fits():
    cache = given(LFUCache, maxsize=3, getsizeof=size_is_the_value)
    cache[1] = 1
    cache[2] = 2
    cache.then.has_length(2)
    cache[3] = 3
    cache.then.holds_keys(3).lacks(1, 2)
    with cache.raises(ValueError):
        cache[4] = 4
    cache.then.holds_keys(3)


def test_lfu_replacing_a_value_keeps_the_entry_alive():
    cache = given(LFUCache, maxsize=2)
    cache[1] = 1
    cache[2] = 2
    cache[1] = "updated"
    cache[3] = 3
    cache.then.contains(3).lacks(2)
    cache[1]
    cache.then.gave("updated")


def test_lfu_forgets_the_use_counts_when_cleared():
    cache = given(LFUCache, maxsize=2)
    cache[1] = 1
    cache[1]
    cache[1]
    cache[2] = 2
    cache.clear()
    cache.then.has_length(0).has(currsize=0)
    cache[3] = 3
    cache[4] = 4
    cache[3]  # 3 is now used more than 4
    cache[5] = 5
    cache.then.has_length(2).contains(3, 5).lacks(4)


def test_lfu_copies_keep_the_use_counts_even_with_thousands_of_distinct_counts():
    """Regression: copying or pickling used to hit the recursion limit."""
    import pickle

    n = sys.getrecursionlimit()
    source = LFUCache(maxsize=n + 1)
    for key in range(n):
        source[key] = key
        for _ in range(key):
            source[key]  # key ends up used key + 1 times
    source[n] = n  # tied with key 0, which has been used once
    for how, make in [
        ("copy.copy", copy.copy),
        ("copy.deepcopy", copy.deepcopy),
        ("pickle", lambda c: pickle.loads(pickle.dumps(c))),
    ]:
        cache = make(source)
        expect(
            list(cache) == list(source), f"the {how} copy has the same keys as the source, in the same order"
        ).should.be.true()
        evicted = [cache.popitem()[0] for _ in range(len(cache))]
        expect(
            evicted == [0, n, *range(1, n)],
            f"the {how} copy evicts key 0 first, then key {n}, then keys 1 to {n - 1} (fewest uses first, oldest on a tie)",
        ).should.be.true()
    expect(len(source), "size of the source afterwards").should.be(n + 1)


# ===== RR: random replacement (made predictable by choosing with min) ===========


def test_rr_evicts_whichever_entry_the_choice_function_picks():
    cache = given(RRCache, maxsize=2, choice=min)
    cache.then.has(choice=min)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache.then.holds_keys(2, 3).lacks(1)
    cache[0] = 0
    cache.then.holds_keys(3, 0).lacks(2)
    cache[4] = 4
    cache.then.holds_keys(3, 4).lacks(0)


def test_rr_with_sizes_evicts_until_the_new_entry_fits():
    cache = given(RRCache, maxsize=3, choice=min, getsizeof=size_is_the_value)
    cache[1] = 1
    cache[2] = 2
    cache.then.has_length(2)
    cache[3] = 3
    cache.then.holds_keys(3).lacks(1, 2)
    with cache.raises(ValueError):
        cache[4] = 4
    cache.then.holds_keys(3)


def test_rr_replacing_a_value_does_not_evict_it():
    cache = given(RRCache, maxsize=2, choice=min)
    cache[1] = 1
    cache[2] = 2
    cache[1] = "updated"
    cache[3] = 3
    cache.then.contains(2, 3).lacks(1)


def test_rr_keeps_its_content_when_the_choice_function_fails():
    def bad_choice(seq):
        raise ValueError("test error")

    cache = given(RRCache, maxsize=2, choice=bad_choice)
    cache[1] = 1
    cache[2] = 2
    with cache.raises(ValueError, "test error"):
        cache[3] = 3
    cache.then.holds_keys(1, 2).has(currsize=2).lacks(3)


def test_rr_picks_at_random_by_default():
    import random

    cache = given(RRCache, maxsize=2)
    expect(cache.unwrap().choice is random.choice, "the default choice is random.choice").should.be.true()


def test_rr_popitem_never_asks_the_choice_function_to_pick_from_nothing():
    for name, choice in [("min", min), ("max", max), ("first", lambda seq: next(iter(seq)))]:
        cache = given(RRCache, maxsize=2, choice=choice, described_as=f"an RRCache that picks with {name}")
        with cache.raises(KeyError):
            cache.popitem()
        cache[1] = 1
        cache.popitem()
        cache.then.gave((1, 1))
        with cache.raises(KeyError):
            cache.popitem()


def test_rr_copy_chooses_among_its_own_keys():
    source = given(RRCache, maxsize=3, choice=min)
    source.update({1: 1, 2: 2, 3: 3})
    cache = given(copy.copy(source.unwrap()), described_as="a copy of that cache")
    del cache[1]
    cache.popitem()
    cache.then.gave((2, 2))
    source.popitem()
    source.then.gave((1, 1))
    source.popitem()
    source.then.gave((2, 2))
    source.popitem()
    source.then.gave((3, 3))
    cache.popitem()
    cache.then.gave((3, 3))
