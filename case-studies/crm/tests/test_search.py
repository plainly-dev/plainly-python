"""Searching with ?q= and filtering with ?status= on the list page."""

from plainly import given, spec

from rules import CRM, search_box_value, status_of_get

list_status = spec(status_of_get)
search_box = spec(search_box_value)


def people():
    """Four contacts. Each search term below can only match through the field the test is about."""
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@acme.com", company="Acme Corp", status="customer")
    crm.add_contact(name="Bob Stone", email="bob@globex.io", company="Globex", status="lead")
    crm.add_contact(name="Carla Annan", email="carla@initech.org", company="Umbrella Group", status="lead")
    crm.add_contact(name="Dan Roe", email="dan@acme.com", company="Acme Corp", status="lost")
    return crm


def test_a_search_matches_part_of_the_name():
    crm = people()
    crm.names_listed(q="stone")
    crm.then.gave(["Bob Stone"])
    crm.names_listed(q="ann")
    crm.then.gave(["Ann Lee", "Carla Annan"])


def test_a_search_matches_part_of_the_email():
    crm = people()
    crm.names_listed(q="initech")
    crm.then.gave(["Carla Annan"])
    crm.names_listed(q="globex.io")
    crm.then.gave(["Bob Stone"])


def test_a_search_matches_part_of_the_company():
    crm = people()
    crm.names_listed(q="umbrella")
    crm.then.gave(["Carla Annan"])
    crm.names_listed(q="corp")
    crm.then.gave(["Ann Lee", "Dan Roe"])


def test_a_search_ignores_upper_and_lower_case():
    crm = people()
    crm.names_listed(q="BOB")
    crm.then.gave(["Bob Stone"])
    crm.names_listed(q="uMbReLLa")
    crm.then.gave(["Carla Annan"])
    crm.names_listed(q="ACME.COM")
    crm.then.gave(["Ann Lee", "Dan Roe"])


def test_a_search_with_no_match_shows_the_no_match_message_instead_of_rows():
    crm = people()
    crm.names_listed(q="zzz")
    crm.then.gave([])
    crm.empty_state_text(q="zzz")
    crm.then.gave("No contacts match your search.")


def test_a_blank_search_lists_everybody():
    crm = people()
    crm.names_listed(q="")
    crm.then.gave(["Ann Lee", "Bob Stone", "Carla Annan", "Dan Roe"])
    crm.names_listed(q="   ")
    crm.then.gave(["Ann Lee", "Bob Stone", "Carla Annan", "Dan Roe"])


def test_spaces_around_the_search_term_are_ignored():
    crm = people()
    crm.names_listed(q="  stone ")
    crm.then.gave(["Bob Stone"])


def test_the_status_filter_lists_only_that_status():
    crm = people()
    crm.names_listed(status="lead")
    crm.then.gave(["Bob Stone", "Carla Annan"])
    crm.names_listed(status="customer")
    crm.then.gave(["Ann Lee"])
    crm.names_listed(status="lost")
    crm.then.gave(["Dan Roe"])


def test_a_blank_status_filter_lists_everybody():
    crm = people()
    crm.names_listed(status="")
    crm.then.gave(["Ann Lee", "Bob Stone", "Carla Annan", "Dan Roe"])


def test_an_unknown_status_filter_lists_nobody_and_does_not_break_the_page():
    crm = people()
    crm.status_of_get("/contacts", status="vip")
    crm.then.gave(200)
    crm.names_listed(status="vip")
    crm.then.gave([])
    crm.empty_state_text(status="vip")
    crm.then.gave("No contacts match your search.")


def test_search_and_status_filter_work_together():
    crm = people()
    crm.names_listed(q="ann", status="lead")
    crm.then.gave(["Carla Annan"])
    crm.names_listed(q="acme", status="lost")
    crm.then.gave(["Dan Roe"])
    crm.names_listed(q="acme", status="lead")
    crm.then.gave([])


def test_the_pipeline_summary_always_counts_everybody_whatever_is_searched():
    everybody = {"lead": 2, "customer": 1, "lost": 1}
    crm = people()
    crm.pipeline_counts(q="ann")
    crm.then.gave(everybody)
    crm.pipeline_counts(status="lost")
    crm.then.gave(everybody)
    crm.pipeline_counts(q="zzz", status="vip")
    crm.then.gave(everybody)


def test_the_search_box_shows_the_term_that_was_searched():
    search_box.if_("ann").then_give("ann")
    search_box.if_("acme corp").then_give("acme corp")
