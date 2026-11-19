"""Text typed by people is never run as HTML, odd characters survive, and POST-only addresses refuse GET."""

from plainly import given, spec

from rules import CRM, kept_value_when_creating, search_box_value, status_of_get

SCRIPT = "<script>alert(1)</script>"
BREAKOUT = '"><script>alert(1)</script>'
search_box = spec(search_box_value)
unknown_page = spec(status_of_get)


def with_a_script_everywhere():
    crm = given(CRM)
    crm.add_contact(name=SCRIPT, email="evil@example.com", phone="<b>1</b>", company="<i>Acme</i>")
    crm.add_note(1, SCRIPT)
    return crm


def test_html_in_a_name_is_shown_as_text_and_never_as_a_tag():
    crm = with_a_script_everywhere()
    crm.names_listed()
    crm.then.gave([SCRIPT])
    crm.page_contains_raw("/contacts", SCRIPT)
    crm.then.gave(False)
    crm.page_contains_raw("/contacts/1", SCRIPT)
    crm.then.gave(False)


def test_html_in_the_company_and_phone_is_shown_as_text_too():
    crm = with_a_script_everywhere()
    crm.row_of(SCRIPT)
    crm.then.gave("evil@example.com | <b>1</b> | <i>Acme</i> | lead")
    crm.details_of(1)
    crm.then.gave("<script>alert(1)</script> | evil@example.com | <b>1</b> | <i>Acme</i> | lead")
    crm.page_contains_raw("/contacts", "<i>Acme</i>")
    crm.then.gave(False)
    crm.page_contains_raw("/contacts/1", "<b>1</b>")
    crm.then.gave(False)


def test_html_in_a_note_is_shown_as_text_and_never_as_a_tag():
    crm = with_a_script_everywhere()
    crm.notes_of(1)
    crm.then.gave([SCRIPT])


def test_a_value_that_tries_to_break_out_of_an_input_stays_inside_it():
    crm = given(CRM)
    crm.add_contact(name=BREAKOUT, email="evil@example.com", company="Acme")
    crm.edit_form_values(1)
    crm.then.gave('"><script>alert(1)</script> | evil@example.com | (blank) | Acme | lead')
    crm.page_contains_raw("/contacts/1", BREAKOUT)
    crm.then.gave(False)


def test_a_refused_form_that_is_shown_again_keeps_html_as_text():
    spec(kept_value_when_creating).if_("name", name=BREAKOUT, email="nope").then_give(BREAKOUT)
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    crm.kept_value_when_editing(1, "name", name=BREAKOUT, email="nope", status="lead")
    crm.then.gave(BREAKOUT)


def test_a_search_term_with_html_is_shown_as_text_in_the_search_box():
    search_box.if_(BREAKOUT).then_give(BREAKOUT)
    search_box.if_("<b>bold</b>").then_give("<b>bold</b>")


def test_text_that_looks_like_code_or_sql_is_just_text():
    crm = given(CRM)
    crm.add_contact(name="Robert'); DROP TABLE contacts;--", email="bobby@example.com")
    crm.add_contact(name="{{ 7 * 7 }} ${7*7} %s", email="template@example.com")
    crm.names_listed()
    crm.then.gave(["Robert'); DROP TABLE contacts;--", "{{ 7 * 7 }} ${7*7} %s"])


def test_names_with_accents_and_other_alphabets_are_kept():
    crm = given(CRM)
    crm.add_contact(name="Zoë Ñandú", email="zoe@example.com", company="東京 Trading")
    crm.row_of("Zoë Ñandú")
    crm.then.gave("zoe@example.com | (blank) | 東京 Trading | lead")


def test_get_is_refused_on_the_addresses_that_only_accept_post():
    crm = given(CRM)
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    crm.status_of_get("/contacts/1/edit")
    crm.then.gave(405)
    crm.status_of_get("/contacts/1/delete")
    crm.then.gave(405)
    crm.status_of_get("/contacts/1/notes")
    crm.then.gave(405)


def test_a_visit_to_an_address_that_does_not_exist_answers_404():
    unknown_page.if_("/nothing-here").then_give(404)
    unknown_page.if_("/contacts/1/unknown").then_give(404)
