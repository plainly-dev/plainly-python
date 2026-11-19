"""TTLCache: entries expire after a time to live. The clock only moves when the test says so."""

import copy
import math
from datetime import datetime, timedelta

from cachetools import TTLCache

from conftest import Clock
from plainly import expect, given


def test_an_entry_disappears_when_it_is_older_than_the_ttl():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=2, ttl=2, timer=clock.unwrap())
    cache.then.has(ttl=2)
    cache[1] = 1
    cache[1]
    cache.then.gave(1).has_length(1).holds_keys(1)

    clock.tick()  # 1 second old
    cache[1]
    cache.then.gave(1).has_length(1).holds_keys(1)
    cache[2] = 2
    cache.then.holds_keys(1, 2).has_length(2)

    clock.tick()  # entry 1 is 2 seconds old: expired
    cache.then.lacks(1).holds_keys(2).has_length(1)
    cache[2]
    cache.then.gave(2)
    cache[3] = 3
    cache.then.lacks(1).holds_keys(2, 3).has_length(2)

    clock.tick()  # entry 2 expires
    cache.then.lacks(1, 2).holds_keys(3).has_length(1)
    cache[3]
    cache.then.gave(3)

    clock.tick()  # entry 3 expires
    cache.then.lacks(1, 2, 3)
    with cache.raises(KeyError):
        del cache[1]
    with cache.raises(KeyError):
        cache.pop(2)
    with cache.raises(KeyError):
        del cache[3]
    cache.then.has_length(0).holds_keys()


def test_the_cache_uses_the_clock_it_was_given():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=2, ttl=2, timer=clock.unwrap())
    cache[1] = 1
    clock.tick()
    cache[1]
    cache.then.gave(1)
    clock.tick()
    cache.then.lacks(1)


def test_when_full_ttl_evicts_the_least_recently_used_entry():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=2, ttl=1, timer=clock.unwrap())
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache.then.has_length(2).lacks(1).holds_keys(2, 3)
    cache[2]
    cache[4] = 4
    cache.then.has_length(2).lacks(1, 3).holds_keys(2, 4)
    cache[5] = 5
    cache.then.has_length(2).lacks(1, 2, 3).holds_keys(4, 5)


def test_expire_removes_old_entries_and_hands_them_back():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=3, ttl=3, timer=clock.unwrap())
    cache.then.has(ttl=3)
    cache[1] = 1
    clock.tick()
    cache[2] = 2
    clock.tick()
    cache[3] = 3  # entries are 2, 1 and 0 seconds old
    cache.then.holds_keys(1, 2, 3).has_length(3)

    cache.expire()  # nothing is old enough yet
    cache.then.gave([]).holds_keys(1, 2, 3)

    cache.expire(3)  # as if the clock said 3: entry 1 is 3 old
    cache.then.gave([(1, 1)]).holds_keys(2, 3).lacks(1)

    cache.expire(4)
    cache.then.gave([(2, 2)]).holds_keys(3).lacks(1, 2)

    cache.expire(5)
    cache.then.gave([(3, 3)]).holds_keys().lacks(1, 2, 3)


def test_looping_skips_expired_entries_without_removing_them():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=2, ttl=2, timer=clock.unwrap())
    cache[1] = 1
    clock.tick()
    cache[2] = 2
    clock.tick()
    expect([key for key in cache], "keys seen by a for loop").should.be([2])
    cache.expire()
    cache.then.gave([(1, 1)])
    expect([key for key in cache], "keys seen by a for loop afterwards").should.be([2])


def test_every_operation_reads_the_clock_once_so_nothing_expires_halfway():
    clock = Clock(auto=True)  # the clock moves forward every time it is read
    cache = given(TTLCache, maxsize=1, ttl=2, timer=clock)
    cache[1] = 1
    cache[1]
    cache.then.gave(1)
    cache[1] = 1
    cache.get(1)
    cache.then.gave(1)
    cache[1] = 1
    cache.pop(1)
    cache.then.gave(1)
    cache[1] = 1
    cache.setdefault(1)
    cache.then.gave(1)
    cache[1] = 1
    cache.clear()
    cache.then.has_length(0)


def test_a_tuple_can_be_a_key_and_expires_like_any_other():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=1, ttl=1, timer=clock.unwrap())
    cache.then.has(ttl=1)
    cache[(1, 2, 3)] = 42
    cache[(1, 2, 3)]
    cache.then.gave(42)
    clock.tick()
    with cache.raises(KeyError):
        cache[(1, 2, 3)]
    cache.then.lacks((1, 2, 3))


def test_dates_can_be_used_instead_of_numbers():
    cache = given(
        TTLCache,
        maxsize=1,
        ttl=timedelta(days=1),
        timer=datetime.now,
        described_as="a TTLCache with a ttl of one day",
    )
    cache[1] = 1
    cache.then.has_length(1)
    cache.expire(datetime.now())
    cache.then.gave([]).has_length(1)
    cache.expire(datetime.now() + timedelta(days=1))
    cache.then.gave([(1, 1)]).has_length(0)


def test_a_date_that_overflows_is_rejected_and_leaves_the_cache_untouched():
    cache = given(
        TTLCache,
        maxsize=1,
        ttl=timedelta(days=1),
        timer=lambda: datetime.max,
        described_as="a TTLCache whose clock says the end of time",
    )
    with cache.raises(OverflowError):
        cache["overflow"] = 1
    cache.then.lacks("overflow").has_length(0).has(currsize=0).holds_keys()
    cache.expire()
    cache.then.gave([])


def test_clearing_forgets_both_the_order_of_use_and_the_ages():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=2, ttl=2, timer=clock.unwrap())
    cache[1] = 1
    cache[2] = 2
    cache.clear()
    cache.then.has_length(0).has(currsize=0)
    cache[3] = 3
    cache[4] = 4
    cache[3]  # 3 is now the most recently used
    cache[5] = 5
    cache.then.has_length(2).contains(3, 5).lacks(4)
    cache[42] = 42
    clock.tick()
    clock.tick()
    clock.tick()  # far past the ttl
    cache.then.lacks(42)


def test_the_default_clock_never_expires_anything_with_an_infinite_ttl():
    cache = given(TTLCache, maxsize=2, ttl=math.inf)
    cache["a"] = 1
    cache["a"]
    cache.then.gave(1).has_length(1).contains("a")
    sized = given(TTLCache, maxsize=10, ttl=math.inf, getsizeof=len)
    sized["abc"] = "abc"
    sized["abc"]
    sized.then.gave("abc").has(currsize=3)


def test_a_shallow_copy_shares_the_clock_but_ages_on_its_own():
    clock = given(Clock)
    source = given(TTLCache, maxsize=3, ttl=2, timer=clock.unwrap())
    source[1] = 1
    source[2] = 2
    clock.tick()
    source[3] = 3
    source[1]  # now 2 is the least recently used
    source.then.gave(1)
    cache = given(copy.copy(source.unwrap()), described_as="a shallow copy of that cache")
    cache.then.holds_keys(1, 2, 3)
    cache[4] = 4  # the copy evicts as its source would, on its own
    cache.then.holds_keys(1, 3, 4)
    source.then.holds_keys(1, 2, 3)
    expect(cache.timer is source.timer, "the copy uses the same timer object").should.be.false()
    clock.tick()  # entries 1 and 2 are now 2 old
    cache.then.holds_keys(3, 4)
    source.then.holds_keys(3)


class ClockThatCopiesItself(Clock):
    def __deepcopy__(self, memo):
        return copy.copy(self)


def test_a_deep_copy_uses_the_timer_s_own_idea_of_copying():
    clock = ClockThatCopiesItself()
    source = given(TTLCache, maxsize=2, ttl=1, timer=clock)
    source[1] = 1
    cache = given(copy.deepcopy(source.unwrap()), described_as="a deep copy of that cache")
    cache.then.holds_keys(1)
    cache.unwrap().timer.tick()  # the copy has a clock of its own
    cache.then.holds_keys()
    source.then.holds_keys(1)


def test_entries_added_while_looping_are_not_visited_and_removed_ones_are_skipped():
    clock = given(Clock)
    cache = given(TTLCache, maxsize=6, ttl=2, timer=clock.unwrap())
    cache.update({1: 1, 2: 2, 3: 3})
    visited = []
    for key in cache:
        visited.append(key)
        cache[key + 10] = key
    expect(visited, "keys visited while adding entries").should.be([1, 2, 3])
    cache.then.holds_keys(1, 2, 3, 11, 12, 13)
    visited = []
    for key in cache:
        visited.append(key)
        cache.clear()
    expect(visited, "keys visited while clearing").should.be([1])
    cache.then.holds_keys()
