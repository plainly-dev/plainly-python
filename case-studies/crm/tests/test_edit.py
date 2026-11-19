"""Editing a contact with POST /contacts/<id>/edit. The form always sends all five fields."""

from plainly import compact, given, spec

from rules import CRM, after_editing

editing_unknown = spec(after_editing)


def two_people():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com", phone="555-0100", company="Acme Corp", status="lead")
    crm.add_contact(name="Bob Stone", email="bob@example.com", status="lost")
    return crm


def test_editing_a_contact_that_does_not_exist_answers_404():
    editing_unknown.if_(99, name="Ann", email="ann@example.com", status="lead").then_give("status 404")


def test_a_valid_edit_sends_you_back_to_the_page_of_the_contact():
    crm = two_people()
    crm.after_editing(1, name="Ann Smith", email="ann@example.com", status="customer")
    crm.then.gave("redirect to /contacts/1")


def test_an_edit_replaces_every_detail_of_the_contact():
    crm = two_people()
    crm.edit_contact(
        1, name="Ann Smith", email="ann.smith@example.com", phone="555-0199", company="Globex", status="customer"
    )
    crm.details_of(1)
    crm.then.gave("Ann Smith | ann.smith@example.com | 555-0199 | Globex | customer")


def test_an_edit_can_clear_the_phone_and_the_company():
    crm = two_people()
    crm.edit_contact(1, name="Ann Lee", email="ann@example.com", status="lead", phone="", company="")
    crm.details_of(1)
    crm.then.gave("Ann Lee | ann@example.com | (blank) | (blank) | lead")


def test_an_edit_trims_spaces_like_creating_does():
    crm = two_people()
    crm.edit_contact(1, name="  Ann Smith ", email=" ann@example.com ", status="lead", phone=" 555 ", company=" X ")
    crm.details_of(1)
    crm.then.gave("Ann Smith | ann@example.com | 555 | X | lead")


def test_an_edit_shows_a_confirmation():
    crm = two_people()
    crm.flash_after_editing(1, name="Ann Smith", email="ann@example.com", status="lead")
    crm.then.gave(["Contact updated."])


def test_an_edit_changes_only_that_contact():
    crm = two_people()
    crm.edit_contact(1, name="Ann Smith", email="ann@example.com", status="customer")
    crm.names_listed()
    crm.then.gave(["Ann Smith", "Bob Stone"])
    crm.details_of(2)
    crm.then.gave("Bob Stone | bob@example.com | (blank) | (blank) | lost")


def test_an_edit_is_checked_like_a_new_contact():
    crm = two_people()
    crm.errors_when_editing(1, name="", email="nope", status="lead")
    crm.then.gave({"name": "Name is required.", "email": "Enter a valid email address."})
    crm.errors_when_editing(1, name="Ann Lee", email="ann@example.com", status="vip")
    crm.then.gave({"status": "Status must be lead, customer or lost."})
    crm.errors_when_editing(1, name="Ann Lee", email="", status="lead")
    crm.then.gave({"email": "Email is required."})
    crm.after_editing(1, name="", email="ann@example.com", status="lead")
    crm.then.gave("status 400")


def test_a_refused_edit_changes_nothing():
    crm = two_people()
    crm.after_editing(1, name="", email="nope", status="customer", phone="000", company="Other")
    crm.then.gave("status 400")
    crm.details_of(1)
    crm.then.gave("Ann Lee | ann@example.com | 555-0100 | Acme Corp | lead")


def test_a_refused_edit_shows_the_form_again_with_what_was_typed():
    crm = two_people()
    crm.kept_value_when_editing(1, "name", name="Ann Smith", email="nope", status="lead")
    crm.then.gave("Ann Smith")
    crm.kept_value_when_editing(1, "email", name="Ann Smith", email="nope", status="lead")
    crm.then.gave("nope")


def test_a_name_of_more_than_100_characters_is_refused_when_editing_too():
    crm = given(CRM, show=compact)
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    crm.errors_when_editing(1, name="a" * 101, email="ann@example.com", status="lead")
    crm.then.gave({"name": "Name must be at most 100 characters."})


def test_a_contact_may_keep_its_own_email_whatever_the_case_or_spaces():
    crm = two_people()
    crm.after_editing(1, name="Ann Lee", email="ann@example.com", status="lead")
    crm.then.gave("redirect to /contacts/1")
    crm.after_editing(1, name="Ann Lee", email="ANN@Example.com", status="lead")
    crm.then.gave("redirect to /contacts/1")
    crm.after_editing(1, name="Ann Lee", email="  ann@example.com ", status="lead")
    crm.then.gave("redirect to /contacts/1")


def test_a_contact_cannot_take_the_email_of_another_contact():
    crm = two_people()
    crm.errors_when_editing(1, name="Ann Lee", email="bob@example.com", status="lead")
    crm.then.gave({"email": "This email is already in use."})
    crm.errors_when_editing(1, name="Ann Lee", email="BOB@EXAMPLE.COM", status="lead")
    crm.then.gave({"email": "This email is already in use."})
    crm.after_editing(1, name="Ann Lee", email="bob@example.com", status="lead")
    crm.then.gave("status 400")


def test_the_email_a_contact_gave_up_can_be_used_by_another_one():
    crm = two_people()
    crm.edit_contact(1, name="Ann Lee", email="ann.new@example.com", status="lead")
    crm.after_editing(2, name="Bob Stone", email="ann@example.com", status="lost")
    crm.then.gave("redirect to /contacts/2")
