"""Reading, changing and deleting one contact."""
from plainly import expect, given

from crm import CRM


def ann_and_bob():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io", company="Acme")
    crm.post("/api/contacts", name="Bob", email="bob@x.io")
    return crm


def test_an_unknown_contact_is_not_found_and_the_answer_is_json():
    crm = given(CRM)
    crm.get("/api/contacts/99").then.has(status=404, error="not found")
    crm.patch("/api/contacts/99", name="Zed").then.has(status=404, error="not found")
    crm.delete("/api/contacts/99").then.has(status=404, error="not found")


def test_only_the_fields_sent_are_changed():
    crm = ann_and_bob()
    crm.patch("/api/contacts/1", status="customer")
    crm.then.has(status=200, body={"id": 1, "name": "Ann", "email": "ann@x.io", "company": "Acme",
                                   "status": "customer"})


def test_a_change_is_kept():
    crm = ann_and_bob()
    crm.patch("/api/contacts/1", name="Ann Lee", company="Initech")
    crm.get("/api/contacts/1")
    expect(crm.body["name"]).should.be("Ann Lee")
    expect(crm.body["company"]).should.be("Initech")


def test_a_change_follows_the_same_rules_as_a_new_contact():
    crm = ann_and_bob()
    crm.patch("/api/contacts/1", name=" ", email="nope", status="vip")
    crm.then.has(status=400, errors={"name": "is required", "email": "is not a valid email",
                                     "status": "is not a valid status"})


def test_a_refused_change_changes_nothing():
    crm = ann_and_bob()
    crm.patch("/api/contacts/1", name="Ann Lee", email="nope")
    crm.get("/api/contacts/1")
    expect(crm.body["name"]).should.be("Ann")


def test_a_contact_can_keep_its_own_email():
    crm = ann_and_bob()
    crm.patch("/api/contacts/1", email="ANN@x.io", name="Ann Lee").then.has(status=200)
    expect(crm.body["email"]).should.be("ann@x.io")


def test_a_contact_cannot_take_another_contacts_email():
    crm = ann_and_bob()
    crm.patch("/api/contacts/2", email="Ann@X.io").then.has(status=409, error="email already exists")


def test_the_id_cannot_be_changed():
    crm = ann_and_bob()
    crm.patch("/api/contacts/1", id=7, name="Ann Lee").then.has(status=200)
    expect(crm.body["id"]).should.be(1)
    crm.get("/api/contacts/7").then.has(status=404)


def test_a_deleted_contact_is_gone():
    crm = ann_and_bob()
    crm.delete("/api/contacts/1").then.has(status=204, page="")
    crm.get("/api/contacts/1").then.has(status=404)
    crm.get("/api/contacts").then.has(names=["Bob"])


def test_a_deleted_email_can_be_used_again():
    crm = ann_and_bob()
    crm.delete("/api/contacts/1")
    crm.post("/api/contacts", name="New Ann", email="ann@x.io").then.has(status=201)
