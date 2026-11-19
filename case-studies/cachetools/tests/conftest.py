import copy
import math
import pickle

import pytest
from cachetools import Cache as BaseCache
from cachetools import FIFOCache, LFUCache, LRUCache, RRCache, TLRUCache, TTLCache


class Clock:
    """A clock that only moves when the test says so."""

    def __init__(self, auto=False):
        self.auto = auto
        self.time = 0

    def __call__(self):
        if self.auto:
            self.time += 1
        return self.time

    def tick(self):
        self.time += 1


class TTLCacheWithClock(TTLCache):
    """A TTLCache that never expires on its own, so the shared rules can run against it."""

    def __init__(self, maxsize, ttl=math.inf, **kwargs):
        super().__init__(maxsize, ttl=ttl, timer=Clock(), **kwargs)


def never_expires(_key, _value, _now):
    return math.inf


class TLRUCacheWithClock(TLRUCache):
    """A TLRUCache whose entries never expire on their own."""

    def __init__(self, maxsize, ttu=never_expires, **kwargs):
        super().__init__(maxsize, ttu, timer=Clock(), **kwargs)


ALL_CACHES = [BaseCache, FIFOCache, LFUCache, LRUCache, RRCache, TTLCacheWithClock, TLRUCacheWithClock]


@pytest.fixture(params=ALL_CACHES, ids=lambda cls: cls.__name__)
def Cache(request):
    """Every cache class in turn: the rules below are promised by all of them."""
    return request.param


def _pickled(cache):
    return pickle.loads(pickle.dumps(cache))


@pytest.fixture(
    params=[copy.copy, copy.deepcopy, _pickled],
    ids=["copy.copy", "copy.deepcopy", "pickle"],
)
def duplicate(request):
    """Every way to make an independent copy of a cache."""
    return request.param
