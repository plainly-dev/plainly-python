"""How many contacts are at each stage."""
from plainly import given

from crm import CRM


def test_a_new_crm_counts_zero_at_every_stage():
    crm = given(CRM)
    crm.get("/api/pipeline").then.has(status=200, body={"lead": 0, "customer": 0, "lost": 0})


def test_each_contact_is_counted_at_its_stage():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    crm.post("/api/contacts", name="Bob", email="bob@x.io", status="customer")
    crm.post("/api/contacts", name="Cy", email="cy@x.io", status="customer")
    crm.get("/api/pipeline").then.has(body={"lead": 1, "customer": 2, "lost": 0})


def test_the_counts_follow_changes_and_deletes():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    crm.post("/api/contacts", name="Bob", email="bob@x.io")
    crm.patch("/api/contacts/1", status="lost")
    crm.delete("/api/contacts/2")
    crm.get("/api/pipeline").then.has(body={"lead": 0, "customer": 0, "lost": 1})
