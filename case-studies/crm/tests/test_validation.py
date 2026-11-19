"""Which new contacts are refused, and what the refusal says.

Each example below runs on a new, empty CRM: add_contact(...) sends POST /api/contacts and gives (status, body).
"""
from plainly import compact, given, spec

from crm import CRM, add_contact

adding = spec(add_contact, show=compact)


def test_name_and_email_are_required():
    adding.if_(email="ann@x.io").then_give((400, {"errors": {"name": "is required"}}))
    adding.if_(name="Ann").then_give((400, {"errors": {"email": "is required"}}))
    adding.if_(name="   ", email="ann@x.io").then_give((400, {"errors": {"name": "is required"}}))
    adding.if_(name="", email="").then_give(
        (400, {"errors": {"name": "is required", "email": "is required"}}))


def test_a_name_can_be_100_characters_but_not_101():
    adding.if_(name="x" * 100, email="ann@x.io").then_give(
        (201, {"id": 1, "name": "x" * 100, "email": "ann@x.io", "company": None, "status": "lead"}))
    adding.if_(name="x" * 101, email="ann@x.io").then_give((400, {"errors": {"name": "is too long"}}))


def test_a_name_is_measured_after_removing_spaces():
    crm = given(CRM, show=compact)
    crm.post("/api/contacts", name=" " + "x" * 100 + " ", email="ann@x.io")
    crm.then.has(status=201)


def test_a_company_can_be_100_characters_but_not_101():
    adding.if_(name="Ann", email="ann@x.io", company="c" * 101).then_give(
        (400, {"errors": {"company": "is too long"}}))


def test_an_email_must_look_like_an_email():
    for bad in ["ann", "ann@", "@x.io", "ann@x", "ann lee@x.io", "ann@@x.io"]:
        adding.if_(name="Ann", email=bad).then_give((400, {"errors": {"email": "is not a valid email"}}))


def test_ordinary_emails_are_accepted():
    crm = given(CRM)
    for good in ["ann@x.io", "ann.lee+crm@mail.example.com", "a_b-c@x-y.co"]:
        crm.post("/api/contacts", name="Ann", email=good)
        crm.then.has(status=201)


def test_status_must_be_lead_customer_or_lost():
    adding.if_(name="Ann", email="ann@x.io", status="vip").then_give(
        (400, {"errors": {"status": "is not a valid status"}}))
    adding.if_(name="Ann", email="ann@x.io", status="Customer").then_give(
        (400, {"errors": {"status": "is not a valid status"}}))


def test_every_invalid_field_is_reported_at_once():
    adding.if_(name="", email="nope", status="vip").then_give(
        (400, {"errors": {"name": "is required", "email": "is not a valid email",
                          "status": "is not a valid status"}}))


def test_a_body_that_is_not_a_json_object_is_refused():
    crm = given(CRM)
    crm.post_body("/api/contacts", "not json")
    crm.then.has(status=400, error="expected a JSON object")
    crm.post_body("/api/contacts", '["Ann", "ann@x.io"]')
    crm.then.has(status=400, error="expected a JSON object")


def test_an_email_can_only_be_used_once_ignoring_case():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="Ann@X.io")
    crm.post("/api/contacts", name="Other Ann", email="ann@x.io")
    crm.then.has(status=409, error="email already exists")


def test_a_refused_contact_is_not_saved():
    crm = given(CRM)
    crm.post("/api/contacts", name="", email="ann@x.io")
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    crm.then.has(status=201, location="/api/contacts/1")
    crm.get("/api/contacts")
    crm.then.has(names=["Ann"])
