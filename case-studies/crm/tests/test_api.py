"""The JSON endpoints: GET /api/contacts and GET /api/contacts/<id>."""

from plainly import given, spec

from rules import CRM, api_content_type, api_failure, api_names

content_type = spec(api_content_type)
failure = spec(api_failure)


def people():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@acme.com", phone="555-0100", company="Acme Corp", status="customer")
    crm.add_contact(name="Bob Stone", email="bob@globex.io", company="Globex", status="lead")
    crm.add_contact(name="Carla Annan", email="carla@initech.org", company="Umbrella Group", status="lead")
    crm.add_contact(name="Dan Roe", email="dan@acme.com", company="Acme Corp", status="lost")
    return crm


def test_the_list_of_a_new_crm_is_an_empty_json_list():
    spec(api_names).if_().then_give([])


def test_the_api_answers_json():
    content_type.if_("/api/contacts").then_give("application/json")
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    crm.api_content_type("/api/contacts/1")
    crm.then.gave("application/json")


def test_the_list_has_every_contact_in_the_order_they_were_added():
    crm = people()
    crm.api_names()
    crm.then.gave(["Ann Lee", "Bob Stone", "Carla Annan", "Dan Roe"])


def test_each_listed_contact_has_its_id_and_its_details():
    crm = people()
    crm.api_row("Ann Lee")
    crm.then.gave("1 | Ann Lee | ann@acme.com | 555-0100 | Acme Corp | customer")
    crm.api_row("Bob Stone")
    crm.then.gave("2 | Bob Stone | bob@globex.io | (blank) | Globex | lead")


def test_the_list_can_be_searched_with_q_like_the_page():
    crm = people()
    crm.api_names(q="ann")
    crm.then.gave(["Ann Lee", "Carla Annan"])
    crm.api_names(q="UMBRELLA")
    crm.then.gave(["Carla Annan"])
    crm.api_names(q="initech")
    crm.then.gave(["Carla Annan"])
    crm.api_names(q="zzz")
    crm.then.gave([])


def test_the_list_can_be_filtered_with_status_like_the_page():
    crm = people()
    crm.api_names(status="lead")
    crm.then.gave(["Bob Stone", "Carla Annan"])
    crm.api_names(status="lost")
    crm.then.gave(["Dan Roe"])
    crm.api_names(status="vip")
    crm.then.gave([])


def test_search_and_status_filter_work_together_in_the_api():
    crm = people()
    crm.api_names(q="ann", status="lead")
    crm.then.gave(["Carla Annan"])
    crm.api_names(q="acme", status="lead")
    crm.then.gave([])


def test_one_contact_is_returned_with_its_notes_newest_first():
    crm = people()
    crm.add_note(1, "First call")
    crm.add_note(1, "Second call")
    crm.api_contact(1)
    crm.then.gave("1 | Ann Lee | ann@acme.com | 555-0100 | Acme Corp | customer")
    crm.api_notes_of(1)
    crm.then.gave(["Second call", "First call"])
    crm.api_notes_of(2)
    crm.then.gave([])


def test_an_unknown_contact_answers_404_as_json():
    failure.if_("/api/contacts/99").then_give({"status": 404, "error": "Contact not found"})
    failure.if_("/api/contacts/0").then_give({"status": 404, "error": "Contact not found"})


def test_the_api_follows_edits_and_deletes():
    crm = people()
    crm.edit_contact(2, name="Bobby Stone", email="bob@globex.io", status="customer")
    crm.api_names(status="customer")
    crm.then.gave(["Ann Lee", "Bobby Stone"])
    crm.delete_contact(1)
    crm.api_names()
    crm.then.gave(["Bobby Stone", "Carla Annan", "Dan Roe"])
    crm.status_of_get("/api/contacts/1")
    crm.then.gave(404)
