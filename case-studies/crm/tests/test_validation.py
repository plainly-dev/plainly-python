"""What makes a new contact be refused, and what the person sees when it happens.

A refused submission answers status 400, shows the form again with one message per wrong field, and stores nothing.
"""

from plainly import compact, given, spec

from rules import CRM, after_creating, errors_when_creating, kept_value_when_creating

errors = spec(errors_when_creating)
long_values = spec(errors_when_creating, show=compact)
creating = spec(after_creating)
long_creating = spec(after_creating, show=compact)
kept = spec(kept_value_when_creating)

OK_EMAIL = "ann@example.com"
OK_NAME = "Ann Lee"


def test_a_name_is_required():
    errors.if_(name="", email=OK_EMAIL).then_give({"name": "Name is required."})
    errors.if_(name="   ", email=OK_EMAIL).then_give({"name": "Name is required."})
    errors.if_(email=OK_EMAIL).then_give({"name": "Name is required."})


def test_an_email_is_required():
    errors.if_(name=OK_NAME, email="").then_give({"email": "Email is required."})
    errors.if_(name=OK_NAME, email="   ").then_give({"email": "Email is required."})
    errors.if_(name=OK_NAME).then_give({"email": "Email is required."})


def test_an_email_that_does_not_look_valid_is_rejected():
    invalid = {"email": "Enter a valid email address."}
    errors.if_(name=OK_NAME, email="plainaddress").then_give(invalid)
    errors.if_(name=OK_NAME, email="ann@").then_give(invalid)
    errors.if_(name=OK_NAME, email="@example.com").then_give(invalid)
    errors.if_(name=OK_NAME, email="ann@example").then_give(invalid)
    errors.if_(name=OK_NAME, email="ann@@example.com").then_give(invalid)
    errors.if_(name=OK_NAME, email="ann smith@example.com").then_give(invalid)
    errors.if_(name=OK_NAME, email="ann@exa mple.com").then_give(invalid)


def test_ordinary_looking_emails_are_accepted():
    creating.if_(name=OK_NAME, email="a@b.co").then_give("redirect to /contacts/1")
    creating.if_(name=OK_NAME, email="first.last+tag@example.com").then_give("redirect to /contacts/2")
    creating.if_(name=OK_NAME, email="ANN@Example.COM").then_give("redirect to /contacts/3")
    creating.if_(name=OK_NAME, email="o'brien@mail.example.org").then_give("redirect to /contacts/4")


def test_an_email_that_is_already_taken_is_rejected():
    crm = given(CRM)
    crm.add_contact(name=OK_NAME, email=OK_EMAIL)
    crm.errors_when_creating(name="Someone Else", email=OK_EMAIL)
    crm.then.gave({"email": "This email is already in use."})
    crm.after_creating(name="Someone Else", email=OK_EMAIL)
    crm.then.gave("status 400")


def test_an_email_counts_as_taken_whatever_its_case_or_surrounding_spaces():
    crm = given(CRM)
    crm.add_contact(name=OK_NAME, email=OK_EMAIL)
    crm.errors_when_creating(name="Someone Else", email="ANN@EXAMPLE.COM")
    crm.then.gave({"email": "This email is already in use."})
    crm.errors_when_creating(name="Someone Else", email="Ann@Example.com")
    crm.then.gave({"email": "This email is already in use."})
    crm.errors_when_creating(name="Someone Else", email="  ann@example.com  ")
    crm.then.gave({"email": "This email is already in use."})


def test_an_email_saved_with_capitals_still_blocks_the_lowercase_version():
    crm = given(CRM)
    crm.add_contact(name=OK_NAME, email="Ann@Example.com")
    crm.errors_when_creating(name="Someone Else", email="ann@example.com")
    crm.then.gave({"email": "This email is already in use."})
    crm.errors_when_creating(name="Someone Else", email="ANN@EXAMPLE.COM")
    crm.then.gave({"email": "This email is already in use."})


def test_a_different_email_is_not_a_duplicate_even_with_the_same_name():
    crm = given(CRM)
    crm.add_contact(name=OK_NAME, email=OK_EMAIL)
    crm.after_creating(name=OK_NAME, email="ann.lee@example.com")
    crm.then.gave("redirect to /contacts/2")


def test_the_status_must_be_lead_customer_or_lost():
    invalid = {"status": "Status must be lead, customer or lost."}
    errors.if_(name=OK_NAME, email=OK_EMAIL, status="vip").then_give(invalid)
    errors.if_(name=OK_NAME, email=OK_EMAIL, status="archived").then_give(invalid)
    errors.if_(name=OK_NAME, email=OK_EMAIL, status="lead customer").then_give(invalid)


def test_a_name_of_more_than_100_characters_is_rejected_with_a_message():
    too_long = {"name": "Name must be at most 100 characters."}
    long_values.if_(name="a" * 101, email=OK_EMAIL).then_give(too_long)
    long_values.if_(name="a" * 500, email=OK_EMAIL).then_give(too_long)


def test_a_name_of_exactly_100_characters_is_fine_and_spaces_do_not_count():
    long_creating.if_(name="a" * 100, email="exact@example.com").then_give("redirect to /contacts/1")
    long_creating.if_(name="  " + "b" * 100 + "  ", email="padded@example.com").then_give("redirect to /contacts/2")


def test_every_wrong_field_is_reported_at_once():
    errors.if_(name="", email="nope").then_give({"name": "Name is required.", "email": "Enter a valid email address."})
    errors.if_(name="", email=OK_EMAIL, status="vip").then_give(
        {"name": "Name is required.", "status": "Status must be lead, customer or lost."}
    )


def test_a_refused_submission_answers_status_400():
    creating.if_(name="", email=OK_EMAIL).then_give("status 400")
    creating.if_(name=OK_NAME, email="nope").then_give("status 400")
    creating.if_(name=OK_NAME, email=OK_EMAIL, status="vip").then_give("status 400")


def test_the_form_shows_again_with_what_was_typed():
    kept.if_("name", name=OK_NAME, email="nope").then_give(OK_NAME)
    kept.if_("email", name=OK_NAME, email="nope").then_give("nope")
    kept.if_("company", name="", email=OK_EMAIL, company="Acme Corp").then_give("Acme Corp")
    kept.if_("phone", name="", email=OK_EMAIL, phone="555-0100").then_give("555-0100")


def test_nothing_is_stored_when_the_submission_is_refused():
    crm = given(CRM)
    crm.after_creating(name="", email="nope", status="vip")
    crm.then.gave("status 400")
    crm.names_listed()
    crm.then.gave([])
    crm.pipeline_counts()
    crm.then.gave({"lead": 0, "customer": 0, "lost": 0})
    crm.empty_state_text()
    crm.then.gave("No contacts yet.")


def test_a_refused_submission_does_not_use_up_an_id():
    crm = given(CRM)
    crm.after_creating(name="", email=OK_EMAIL)
    crm.then.gave("status 400")
    crm.after_creating(name=OK_NAME, email=OK_EMAIL)
    crm.then.gave("redirect to /contacts/1")
