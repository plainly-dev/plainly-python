"""Notes on a contact: POST /contacts/<id>/notes, shown on the contact page newest first."""

from plainly import given, spec

from rules import CRM, after_adding_note

noting_unknown = spec(after_adding_note)


def ann():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    return crm


def test_a_note_for_a_contact_that_does_not_exist_answers_404():
    noting_unknown.if_(99, "Call back on Monday").then_give("status 404")


def test_adding_a_note_sends_you_back_to_the_page_of_the_contact():
    crm = ann()
    crm.after_adding_note(1, "Call back on Monday")
    crm.then.gave("redirect to /contacts/1")


def test_adding_a_note_shows_a_confirmation():
    crm = ann()
    crm.flash_after_adding_note(1, "Call back on Monday")
    crm.then.gave(["Note added."])


def test_a_contact_without_notes_says_so():
    crm = ann()
    crm.notes_of(1)
    crm.then.gave([])
    crm.no_notes_text(1)
    crm.then.gave("No notes yet.")
    crm.add_note(1, "First call done")
    crm.no_notes_text(1)
    crm.then.gave(None)


def test_notes_are_shown_newest_first():
    crm = ann()
    crm.add_note(1, "First call, left a voicemail")
    crm.notes_of(1)
    crm.then.gave(["First call, left a voicemail"])
    crm.add_note(1, "Second call, sent the offer")
    crm.add_note(1, "Third call, signed")
    crm.notes_of(1)
    crm.then.gave(["Third call, signed", "Second call, sent the offer", "First call, left a voicemail"])


def test_two_notes_with_the_same_text_are_both_kept():
    crm = ann()
    crm.add_note(1, "No answer")
    crm.add_note(1, "No answer")
    crm.notes_of(1)
    crm.then.gave(["No answer", "No answer"])


def test_an_empty_note_is_refused_with_a_message():
    empty = {"text": "Note cannot be empty."}
    crm = ann()
    crm.errors_when_adding_note(1, "")
    crm.then.gave(empty)
    crm.errors_when_adding_note(1, "   ")
    crm.then.gave(empty)
    crm.errors_when_adding_note(1)
    crm.then.gave(empty)


def test_a_refused_note_answers_status_400_and_is_not_stored():
    crm = ann()
    crm.after_adding_note(1, "   ")
    crm.then.gave("status 400")
    crm.notes_of(1)
    crm.then.gave([])


def test_spaces_around_a_note_are_trimmed():
    crm = ann()
    crm.add_note(1, "   Asked for a discount  ")
    crm.notes_of(1)
    crm.then.gave(["Asked for a discount"])


def test_notes_belong_to_their_own_contact():
    crm = ann()
    crm.add_contact(name="Bob Stone", email="bob@example.com")
    crm.add_note(1, "Note for Ann")
    crm.add_note(2, "Note for Bob")
    crm.notes_of(1)
    crm.then.gave(["Note for Ann"])
    crm.notes_of(2)
    crm.then.gave(["Note for Bob"])


def test_notes_keep_accents_symbols_and_punctuation_as_typed():
    crm = ann()
    crm.add_note(1, "Café 'Olé' & co: 5 < 6 > 4 - \"quoted\"")
    crm.notes_of(1)
    crm.then.gave(["Café 'Olé' & co: 5 < 6 > 4 - \"quoted\""])


def test_notes_stay_when_the_contact_is_edited():
    crm = ann()
    crm.add_note(1, "Important client")
    crm.edit_contact(1, name="Ann Smith", email="ann@example.com", status="customer")
    crm.notes_of(1)
    crm.then.gave(["Important client"])
