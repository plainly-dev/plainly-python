"""TLRUCache: every entry says when it expires ("time to use"), and the least recently used goes first when full."""

from cachetools import TLRUCache

from conftest import Clock
from plainly import given


def expires_after_value_plus_one_seconds(_key, value, now):
    return now + value + 1


def expires_one_second_from_now(_key, _value, now):
    return now + 1


def expires_after_value_seconds(_key, value, now):
    return now + value


def expires_three_seconds_from_now(_key, _value, now):
    return now + 3


def test_each_entry_expires_when_its_own_time_to_use_says_so():
    clock = given(Clock)
    cache = given(TLRUCache, maxsize=6, ttu=expires_after_value_plus_one_seconds, timer=clock.unwrap())
    cache.ttu(0, 1, 1)
    cache.then.gave(3)
    cache[1] = 1  # expires at 0 + 1 + 1 = 2
    cache[1]
    cache.then.gave(1).holds_keys(1)

    clock.tick()
    cache[1]
    cache.then.gave(1).holds_keys(1)
    cache[2] = 2  # expires at 1 + 2 + 1 = 4
    cache.then.holds_keys(1, 2)

    clock.tick()  # entry 1 expires
    cache.then.lacks(1).holds_keys(2)
    cache[3] = 3  # expires at 2 + 3 + 1 = 6
    cache.then.holds_keys(2, 3)

    clock.tick()
    cache.then.lacks(1).holds_keys(2, 3)
    cache[1] = 1  # expires at 3 + 1 + 1 = 5
    cache.then.holds_keys(2, 3, 1)

    clock.tick()  # entry 2 expires
    cache.then.holds_keys(3, 1).lacks(2)

    clock.tick()  # entry 1 expires
    cache.then.holds_keys(3).lacks(1, 2)

    clock.tick()  # entry 3 expires
    cache.then.lacks(1, 2, 3)
    with cache.raises(KeyError):
        del cache[1]
    with cache.raises(KeyError):
        cache.pop(2)
    with cache.raises(KeyError):
        del cache[3]
    cache.then.has_length(0).holds_keys()


def test_when_full_tlru_evicts_the_least_recently_used_entry():
    clock = given(Clock)
    cache = given(TLRUCache, maxsize=2, ttu=expires_one_second_from_now, timer=clock.unwrap())
    cache.ttu(0, 0, 1)
    cache.then.gave(2)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache.then.has_length(2).lacks(1).holds_keys(2, 3)
    cache[2]
    cache[4] = 4
    cache.then.has_length(2).lacks(1, 3).holds_keys(2, 4)
    cache[5] = 5
    cache.then.has_length(2).lacks(1, 2, 3).holds_keys(4, 5)


def test_overwriting_an_entry_with_one_that_is_already_expired_removes_it():
    # the new value is dead on arrival, so the old value must not quietly stay
    clock = given(Clock)
    cache = given(TLRUCache, maxsize=2, ttu=expires_after_value_seconds, timer=clock.unwrap())
    cache[1] = 5
    cache[1]
    cache.then.gave(5).has_length(1).has(currsize=1)
    cache[1] = 0  # expires the moment it is stored
    cache.then.lacks(1).has_length(0).has(currsize=0).holds_keys()
    cache.get(1)
    cache.then.gave(None)


def test_expire_removes_entries_that_are_due_and_hands_them_back():
    clock = given(Clock)
    cache = given(TLRUCache, maxsize=3, ttu=expires_three_seconds_from_now, timer=clock.unwrap())
    cache[1] = 1
    clock.tick()
    cache[2] = 2
    clock.tick()
    cache[3] = 3
    cache.then.holds_keys(1, 2, 3).has_length(3)

    cache.expire()  # nothing is due yet
    cache.then.gave([]).holds_keys(1, 2, 3)

    cache.expire(3)  # entry 1 expires at 3
    cache.then.gave([(1, 1)]).holds_keys(2, 3).lacks(1)

    cache.expire(4)
    cache.then.gave([(2, 2)]).holds_keys(3).lacks(1, 2)

    cache.expire(5)
    cache.then.gave([(3, 3)]).holds_keys().lacks(1, 2, 3)


def expires_after_key_seconds(key, _value, now):
    return now + key


def test_an_entry_that_is_already_expired_is_never_stored_and_does_not_push_others_out():
    cache = given(TLRUCache, maxsize=1, ttu=expires_after_key_seconds, timer=Clock())
    cache[1] = None
    cache[1]
    cache.then.gave(None).has_length(1)
    cache[0] = None  # key 0 expires after 0 seconds: dead on arrival
    cache.then.lacks(0).contains(1)
    cache[1]
    cache.then.gave(None).has_length(1)
    cache[-1] = None  # key -1 expires before it is stored
    cache.then.lacks(-1, 0).contains(1)
    cache[1]
    cache.then.gave(None).has_length(1)


def test_every_operation_reads_the_clock_once_so_nothing_expires_halfway():
    cache = given(TLRUCache, maxsize=1, ttu=lambda key, value, now: now + 2, timer=Clock(auto=True))
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


def test_an_entry_read_at_the_exact_moment_it_expires_is_already_gone():
    clock = given(Clock)
    cache = given(TLRUCache, maxsize=2, ttu=expires_one_second_from_now, timer=clock.unwrap())
    cache[1] = 1  # expires at time 1
    cache[1]
    cache.then.gave(1)
    clock.tick()  # the clock now says 1
    with cache.raises(KeyError):
        cache[1]
