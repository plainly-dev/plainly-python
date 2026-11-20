"""Listing, searching and filtering contacts."""
from plainly import given

from crm import CRM


def three_contacts():
    crm = given(CRM)
    crm.post("/api/contacts", name="carla Diaz", email="carla@globex.com", company="Globex", status="customer")
    crm.post("/api/contacts", name="Ann Lee", email="ann@x.io", company="Acme", status="lead")
    crm.post("/api/contacts", name="Bob Stone", email="bob@acme.com", status="lost")
    return crm


def test_a_new_crm_has_no_contacts():
    crm = given(CRM)
    crm.get("/api/contacts").then.has(status=200, body={"contacts": []})


def test_contacts_are_listed_by_name_ignoring_case():
    crm = three_contacts()
    crm.get("/api/contacts").then.has(status=200, names=["Ann Lee", "Bob Stone", "carla Diaz"])


def test_search_looks_in_name_email_and_company_ignoring_case():
    crm = three_contacts()
    crm.get("/api/contacts", q="ACME").then.has(status=200, names=["Ann Lee", "Bob Stone"])
    crm.get("/api/contacts", q="diaz").then.has(names=["carla Diaz"])
    crm.get("/api/contacts", q="@x.io").then.has(names=["Ann Lee"])


def test_a_search_that_matches_nothing_gives_an_empty_list():
    crm = three_contacts()
    crm.get("/api/contacts", q="zebra").then.has(status=200, names=[])


def test_contacts_can_be_filtered_by_status():
    crm = three_contacts()
    crm.get("/api/contacts", status="customer").then.has(status=200, names=["carla Diaz"])
    crm.get("/api/contacts", status="lead").then.has(names=["Ann Lee"])


def test_search_and_status_filter_work_together():
    crm = three_contacts()
    crm.get("/api/contacts", q="acme", status="lost").then.has(status=200, names=["Bob Stone"])


def test_an_unknown_status_filter_is_refused():
    crm = three_contacts()
    crm.get("/api/contacts", status="vip").then.has(status=400, error="unknown status")
