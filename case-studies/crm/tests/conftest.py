"""Every test starts with a brand new, empty CRM.

The app is built lazily, by the first request a test makes (see `rules.client`), so that collecting the tests
works even when `crm_app` does not exist yet: each test then fails on its own with a clear ImportError.
"""

import pytest

import rules


@pytest.fixture(autouse=True)
def fresh_crm():
    rules.start_new_crm()
    yield
    rules.start_new_crm()
