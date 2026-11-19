"""Notes on a contact."""
from plainly import compact, expect, given

from crm import CRM


def ann():
    crm = given(CRM)
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    return crm


def test_a_new_contact_has_no_notes():
    crm = ann()
    crm.get("/api/contacts/1/notes")
    crm.then.has(status=200, body={"notes": []})


def test_a_note_is_saved_and_given_back():
    crm = ann()
    crm.post("/api/contacts/1/notes", text="Called, wants a demo")
    crm.then.has(status=201, body={"id": 1, "text": "Called, wants a demo"})


def test_notes_are_listed_newest_first():
    crm = ann()
    crm.post("/api/contacts/1/notes", text="first")
    crm.post("/api/contacts/1/notes", text="second")
    crm.post("/api/contacts/1/notes", text="third")
    crm.get("/api/contacts/1/notes")
    crm.then.has(texts=["third", "second", "first"])


def test_notes_belong_to_one_contact():
    crm = ann()
    crm.post("/api/contacts", name="Bob", email="bob@x.io")
    crm.post("/api/contacts/1/notes", text="for Ann")
    crm.post("/api/contacts/2/notes", text="for Bob")
    crm.get("/api/contacts/2/notes")
    crm.then.has(texts=["for Bob"])


def test_note_ids_count_across_the_whole_crm():
    crm = ann()
    crm.post("/api/contacts", name="Bob", email="bob@x.io")
    crm.post("/api/contacts/1/notes", text="for Ann")
    crm.post("/api/contacts/2/notes", text="for Bob")
    expect(crm.body["id"]).should.be(2)


def test_spaces_around_a_note_are_removed():
    crm = ann()
    crm.post("/api/contacts/1/notes", text="  hello  ")
    expect(crm.body["text"]).should.be("hello")


def test_an_empty_note_is_refused_and_not_saved():
    crm = ann()
    crm.post("/api/contacts/1/notes", text="   ")
    crm.then.has(status=400, errors={"text": "is required"})
    crm.post("/api/contacts/1/notes")
    crm.then.has(status=400, errors={"text": "is required"})
    crm.get("/api/contacts/1/notes")
    crm.then.has(texts=[])


def test_a_note_can_be_1000_characters_but_not_1001():
    crm = given(CRM, show=compact)
    crm.post("/api/contacts", name="Ann", email="ann@x.io")
    crm.post("/api/contacts/1/notes", text="n" * 1000)
    crm.then.has(status=201)
    crm.post("/api/contacts/1/notes", text="n" * 1001)
    crm.then.has(status=400, errors={"text": "is too long"})


def test_notes_on_an_unknown_contact_are_not_found():
    crm = ann()
    crm.post("/api/contacts/99/notes", text="hello")
    crm.then.has(status=404, error="not found")
    crm.get("/api/contacts/99/notes")
    crm.then.has(status=404, error="not found")


def test_deleting_a_contact_deletes_its_notes():
    crm = ann()
    crm.post("/api/contacts/1/notes", text="hello")
    crm.delete("/api/contacts/1")
    crm.get("/api/contacts/1/notes")
    crm.then.has(status=404)
