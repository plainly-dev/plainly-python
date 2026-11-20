"""Adding a contact: what is saved, and what the answer says."""
from plainly import expect, given

from crm import CRM


def test_a_new_contact_is_saved_and_given_back_with_id_1():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann Lee", email="ann@x.io", company="Acme", status="customer")
    crm.then.has(status=201, body={"id": 1, "name": "Ann Lee", "email": "ann@x.io", "company": "Acme",
                                   "status": "customer"})


def test_the_answer_says_where_the_new_contact_lives():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    crm.then.has(location="/api/contacts/1")


def test_ids_count_up_from_1():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    crm.post("/api/contacts", name="Bob", email="bob@x.io")
    crm.then.has(status=201, location="/api/contacts/2")
    expect(crm.body["id"]).should.be(2)


def test_company_and_status_are_optional():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    crm.then.has(status=201)
    expect(crm.body["company"]).should.be.none()
    expect(crm.body["status"]).should.be("lead")


def test_an_empty_company_is_saved_as_no_company():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io", company="   ")
    crm.then.has(status=201)
    expect(crm.body["company"]).should.be.none()


def test_spaces_around_fields_are_removed():
    crm = given(CRM)
    crm.post("/api/contacts", name="  Ann Lee ", email=" ann@x.io ", company=" Acme ")
    crm.then.has(status=201)
    expect(crm.body["name"]).should.be("Ann Lee")
    expect(crm.body["email"]).should.be("ann@x.io")
    expect(crm.body["company"]).should.be("Acme")


def test_emails_are_saved_in_lowercase():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="Ann.Lee@Example.COM")
    expect(crm.body["email"]).should.be("ann.lee@example.com")


def test_fields_the_crm_does_not_know_are_ignored():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io", age=42)
    crm.then.has(status=201)
    expect(crm.body).should.not_.contain("age")


def test_a_new_contact_can_be_read_back():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io", company="Acme")
    crm.get("/api/contacts/1")
    crm.then.has(status=200, body={"id": 1, "name": "Ann", "email": "ann@x.io", "company": "Acme",
                                   "status": "lead"})
