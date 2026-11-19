"""Deleting a contact with POST /contacts/<id>/delete."""

from plainly import given, spec

from rules import CRM, after_deleting

deleting_unknown = spec(after_deleting)


def two_people():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com", status="customer")
    crm.add_contact(name="Bob Stone", email="bob@example.com", status="lead")
    return crm


def test_deleting_a_contact_that_does_not_exist_answers_404():
    deleting_unknown.if_(99).then_give("status 404")
    deleting_unknown.if_(1).then_give("status 404")


def test_deleting_sends_you_back_to_the_list():
    crm = two_people()
    crm.after_deleting(1)
    crm.then.gave("redirect to /contacts")


def test_deleting_shows_a_confirmation():
    crm = two_people()
    crm.flash_after_deleting(1)
    crm.then.gave(["Contact deleted."])


def test_a_deleted_contact_disappears_from_the_list_and_the_others_stay():
    crm = two_people()
    crm.delete_contact(1)
    crm.names_listed()
    crm.then.gave(["Bob Stone"])
    crm.ids_listed()
    crm.then.gave(["2"])


def test_the_page_of_a_deleted_contact_answers_404():
    crm = two_people()
    crm.status_of_get("/contacts/1")
    crm.then.gave(200)
    crm.delete_contact(1)
    crm.status_of_get("/contacts/1")
    crm.then.gave(404)
    crm.status_of_get("/contacts/2")
    crm.then.gave(200)


def test_a_contact_can_only_be_deleted_once():
    crm = two_people()
    crm.delete_contact(1)
    crm.after_deleting(1)
    crm.then.gave("status 404")


def test_deleting_the_last_contact_brings_back_the_empty_state():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    crm.delete_contact(1)
    crm.empty_state_text()
    crm.then.gave("No contacts yet.")
    crm.pipeline_counts()
    crm.then.gave({"lead": 0, "customer": 0, "lost": 0})


def test_the_email_of_a_deleted_contact_can_be_used_again():
    crm = two_people()
    crm.delete_contact(1)
    crm.add_contact(name="Ann Again", email="ann@example.com")
    crm.names_listed()
    crm.then.gave(["Bob Stone", "Ann Again"])


def test_a_deleted_contact_no_longer_shows_in_the_json_list():
    crm = two_people()
    crm.delete_contact(2)
    crm.api_names()
    crm.then.gave(["Ann Lee"])
