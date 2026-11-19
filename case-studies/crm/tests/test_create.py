"""Creating a contact with POST /contacts when everything is fine."""

from plainly import given, spec

from rules import (
    CRM,
    after_creating,
    flash_after_creating,
    flash_on_the_page_after_that,
    form_field_names,
    form_target,
)

creating = spec(after_creating)
confirmation = spec(flash_after_creating)


def test_a_valid_contact_sends_you_to_the_page_of_the_new_contact():
    creating.if_(name="Ann Lee", email="ann@example.com").then_give("redirect to /contacts/1")


def test_each_new_contact_gets_the_next_id():
    crm = given(CRM)
    crm.after_creating(name="Ann Lee", email="ann@example.com")
    crm.then.gave("redirect to /contacts/1")
    crm.after_creating(name="Bob Stone", email="bob@example.com")
    crm.then.gave("redirect to /contacts/2")
    crm.after_creating(name="Carla Annan", email="carla@example.com")
    crm.then.gave("redirect to /contacts/3")


def test_only_the_name_and_the_email_are_required():
    creating.if_(name="Ann Lee", email="ann@example.com").then_give("redirect to /contacts/1")
    creating.if_(name="Bob Stone", email="bob@example.com", phone="", company="", status="").then_give(
        "redirect to /contacts/2"
    )
    creating.if_(
        name="Carla Annan", email="carla@example.com", phone="555-0100", company="Initech", status="lost"
    ).then_give("redirect to /contacts/3")


def test_each_of_the_three_statuses_is_accepted():
    creating.if_(name="A", email="a@example.com", status="lead").then_give("redirect to /contacts/1")
    creating.if_(name="B", email="b@example.com", status="customer").then_give("redirect to /contacts/2")
    creating.if_(name="C", email="c@example.com", status="lost").then_give("redirect to /contacts/3")


def test_the_new_contact_is_stored_with_everything_that_was_typed():
    crm = given(CRM)
    crm.add_contact(
        name="Ann Lee", email="ann@example.com", phone="555-0100", company="Acme Corp", status="customer"
    )
    crm.details_of(1)
    crm.then.gave("Ann Lee | ann@example.com | 555-0100 | Acme Corp | customer")


def test_a_contact_without_a_status_starts_as_a_lead():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    crm.add_contact(name="Bob Stone", email="bob@example.com", status="")
    crm.row_of("Ann Lee")
    crm.then.gave("ann@example.com | (blank) | (blank) | lead")
    crm.row_of("Bob Stone")
    crm.then.gave("bob@example.com | (blank) | (blank) | lead")


def test_spaces_around_every_field_are_trimmed():
    crm = given(CRM)
    crm.add_contact(
        name="  Ann Lee  ", email="  ann@example.com ", phone=" 555-0100 ", company="  Acme Corp ", status="customer"
    )
    crm.details_of(1)
    crm.then.gave("Ann Lee | ann@example.com | 555-0100 | Acme Corp | customer")


def test_a_confirmation_is_shown_after_creating_a_contact():
    confirmation.if_(name="Ann Lee", email="ann@example.com").then_give(["Contact created."])


def test_the_confirmation_is_shown_only_once():
    spec(flash_on_the_page_after_that).if_(name="Ann Lee", email="ann@example.com").then_give([])


def test_a_new_contact_appears_in_the_list_and_in_the_pipeline():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com", status="customer")
    crm.names_listed()
    crm.then.gave(["Ann Lee"])
    crm.pipeline_counts()
    crm.then.gave({"lead": 0, "customer": 1, "lost": 0})


def test_the_new_contact_form_is_on_the_list_page_and_posts_to_the_contacts_address():
    spec(form_target).if_("/contacts", "new-contact-form").then_give("POST /contacts")
    spec(form_field_names).if_("/contacts", "new-contact-form").then_give(
        ["company", "email", "name", "phone", "status"]
    )
