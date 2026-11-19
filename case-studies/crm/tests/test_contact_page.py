"""The page of one contact: GET /contacts/<id>."""

from plainly import given, spec

from rules import CRM, status_of_get

page_status = spec(status_of_get)


def ann():
    crm = given(CRM)
    crm.add_contact(
        name="Ann Lee", email="ann@example.com", phone="555-0100", company="Acme Corp", status="customer"
    )
    return crm


def test_an_unknown_contact_answers_404():
    page_status.if_("/contacts/99").then_give(404)
    page_status.if_("/contacts/0").then_give(404)
    page_status.if_("/contacts/abc").then_give(404)


def test_an_existing_contact_answers_200():
    crm = ann()
    crm.status_of_get("/contacts/1")
    crm.then.gave(200)
    crm.status_of_get("/contacts/2")
    crm.then.gave(404)


def test_the_page_shows_every_detail_of_the_contact():
    crm = ann()
    crm.details_of(1)
    crm.then.gave("Ann Lee | ann@example.com | 555-0100 | Acme Corp | customer")


def test_missing_optional_details_are_shown_empty():
    crm = given(CRM)
    crm.add_contact(name="Bob Stone", email="bob@example.com")
    crm.details_of(1)
    crm.then.gave("Bob Stone | bob@example.com | (blank) | (blank) | lead")


def test_the_edit_form_is_filled_in_with_the_current_details():
    crm = ann()
    crm.edit_form_values(1)
    crm.then.gave("Ann Lee | ann@example.com | 555-0100 | Acme Corp | customer")


def test_each_form_on_the_page_posts_to_its_own_contact():
    crm = ann()
    crm.form_target("/contacts/1", "edit-contact-form")
    crm.then.gave("POST /contacts/1/edit")
    crm.form_target("/contacts/1", "delete-contact-form")
    crm.then.gave("POST /contacts/1/delete")
    crm.form_target("/contacts/1", "note-form")
    crm.then.gave("POST /contacts/1/notes")


def test_the_forms_use_the_agreed_field_names():
    crm = ann()
    crm.form_field_names("/contacts/1", "edit-contact-form")
    crm.then.gave(["company", "email", "name", "phone", "status"])
    crm.form_field_names("/contacts/1", "note-form")
    crm.then.gave(["text"])


def test_the_page_of_a_contact_shows_no_error_messages():
    crm = ann()
    crm.errors_on_page("/contacts/1")
    crm.then.gave({})
