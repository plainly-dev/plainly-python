"""Adapters so every CRM rule reads as plain values in, plain values out.

The CRM is a web page. A reviewer should not have to read HTTP plumbing, so each function below takes
plain values (a name, an email, a search term) and gives back something small and readable: the visible
text of one element, a list of names, a status code, or where a form submission leads.

Nothing here knows how the app is built. It only talks to `app.test_client()`, and it only looks for the
HTML hooks listed in tests/CONTRACT.md.

Two groups of functions:
  * "probes" (after_creating, errors_when_creating, names_listed, ...) are used as rules:
        creating = spec(after_creating)
        creating.if_(name="Ann", email="ann@example.com").then_give("redirect to /contacts/1")
  * the same functions are also the steps of a story, through the `CRM` class at the bottom:
        crm = given(CRM)
        crm.add_contact(name="Ann", email="ann@example.com")
        crm.names_listed()
        crm.then.gave(["Ann"])
"""

from urllib.parse import urlparse

from dom import parse

REDIRECTS = (301, 302, 303, 307, 308)
STATUS_NAMES = ("lead", "customer", "lost")

_state = {"client": None}


def start_new_crm():
    """Forget the previous app. The next request builds a brand new, empty CRM (see conftest.py)."""
    _state["client"] = None


def client():
    if _state["client"] is None:
        from crm_app import create_app  # imported late, so that collecting the tests never needs the app

        _state["client"] = create_app({"TESTING": True}).test_client()
    return _state["client"]


# ----- plumbing (private) ----------------------------------------------------------


def _present(values):
    """Leave out the fields that are None, so a field can be 'not sent at all'. An empty string is still sent."""
    return {key: value for key, value in values.items() if value is not None}


def _get(path, **query):
    return client().get(path, query_string=_present(query))


def _post(path, follow=False, **form):
    return client().post(path, data=_present(form), follow_redirects=follow)


def _page(response):
    return parse(response.get_data(as_text=True))


def _where(response):
    """'redirect to /contacts/1' when the server redirects, otherwise 'status 400'."""
    if response.status_code in REDIRECTS:
        return "redirect to " + urlparse(response.headers["Location"]).path
    return f"status {response.status_code}"


def _must_succeed(response, what):
    if response.status_code not in REDIRECTS and response.status_code != 200:
        raise AssertionError(f"{what} should have worked but the server answered {_where(response)}")


def _text_of(page, selector):
    node = page.select_one(selector)
    if node is None:
        raise AssertionError(f"the page has no element matching {selector!r}")
    return node.text()


def _errors_of(page):
    """{field: message} for every <... class="error" data-field="field">message</...> on the page."""
    return {node.attrs["data-field"]: node.text() for node in page.select(".error[data-field]")}


def _clear_pending_messages():
    """Show any confirmation still waiting (from an earlier step), so the next one stands alone."""
    _get("/contacts")


def _flash_of(response):
    return [node.text() for node in _page(response).select(".flash")]


def _json(response):
    if response.mimetype != "application/json":
        raise AssertionError(f"expected JSON but the server answered {response.mimetype!r} (status {response.status_code})")
    return response.get_json()


def _list_page(q=None, status=None):
    response = _get("/contacts", q=q, status=status)
    if response.status_code != 200:
        raise AssertionError(f"GET /contacts answered status {response.status_code}")
    return _page(response)


def _line(*values):
    """One short line for several values, 'Ann Lee | ann@example.com | (blank) | Acme | lead' (empty ones read '(blank)')."""
    return " | ".join(str(value) if value not in ("", None) else "(blank)" for value in values)


def _form_values(page, form_id, fields):
    values = {}
    for field in fields:
        node = page.select_one(f"form#{form_id} input[name={field}]")
        if node is None:
            raise AssertionError(f"form#{form_id} has no input named {field!r}")
        values[field] = node.attrs.get("value", "")
    return values


# ----- submitting forms: where does it lead? ------------------------------------


def after_creating(**form):
    return _where(_post("/contacts", **form))


def after_editing(contact_id, **form):
    return _where(_post(f"/contacts/{contact_id}/edit", **form))


def after_deleting(contact_id):
    return _where(_post(f"/contacts/{contact_id}/delete"))


def after_adding_note(contact_id, text=None):
    return _where(_post(f"/contacts/{contact_id}/notes", text=text))


# ----- submitting forms that fail: which message is shown for which field? ----------


def _errors_after(response):
    if response.status_code != 400:
        return _where(response)
    return _errors_of(_page(response))


def errors_when_creating(**form):
    return _errors_after(_post("/contacts", **form))


def errors_when_editing(contact_id, **form):
    return _errors_after(_post(f"/contacts/{contact_id}/edit", **form))


def errors_when_adding_note(contact_id, text=None):
    return _errors_after(_post(f"/contacts/{contact_id}/notes", text=text))


def kept_value_when_creating(field, **form):
    """What the re-shown 'new contact' form has in `field` after a rejected submission."""
    response = _post("/contacts", **form)
    if response.status_code != 400:
        return _where(response)
    return _form_values(_page(response), "new-contact-form", [field])[field]


def kept_value_when_editing(contact_id, field, **form):
    response = _post(f"/contacts/{contact_id}/edit", **form)
    if response.status_code != 400:
        return _where(response)
    return _form_values(_page(response), "edit-contact-form", [field])[field]


# ----- the confirmation message shown after a successful submission --------------------


def flash_after_creating(**form):
    _clear_pending_messages()
    return _flash_of(_post("/contacts", follow=True, **form))


def flash_after_editing(contact_id, **form):
    _clear_pending_messages()
    return _flash_of(_post(f"/contacts/{contact_id}/edit", follow=True, **form))


def flash_after_deleting(contact_id):
    _clear_pending_messages()
    return _flash_of(_post(f"/contacts/{contact_id}/delete", follow=True))


def flash_after_adding_note(contact_id, text):
    _clear_pending_messages()
    return _flash_of(_post(f"/contacts/{contact_id}/notes", follow=True, text=text))


def flash_on_the_page_after_that(**form):
    """Create a contact, follow the redirect, then open the list: is the confirmation still there?"""
    _clear_pending_messages()
    _post("/contacts", follow=True, **form)
    return _flash_of(_get("/contacts"))


# ----- the list page ------------------------------------------------------------------


def names_listed(q=None, status=None):
    return [node.text() for node in _list_page(q, status).select("tr[data-contact-id] .name")]


def emails_listed(q=None, status=None):
    return [node.text() for node in _list_page(q, status).select("tr[data-contact-id] .email")]


def ids_listed():
    """The data-contact-id of every row, in the order shown."""
    return [row.attrs["data-contact-id"] for row in _list_page().select("tr[data-contact-id]")]


def link_of(name):
    """Where the name in the list links to."""
    for row in _list_page().select("tr[data-contact-id]"):
        if row.select_one(".name").text() == name:
            return _text_of_attr(row, ".name a", "href")
    return None


def row_of(name):
    """What the list shows in the row of the contact with this name: 'email | phone | company | status'."""
    for row in _list_page().select("tr[data-contact-id]"):
        if row.select_one(".name").text() == name:
            return _line(*(_text_of(row, f".{field}") for field in ("email", "phone", "company", "status")))
    return None


def pipeline_counts(q=None, status=None):
    page = _list_page(q, status)
    return {name: int(_text_of(page, f"#pipeline-{name}")) for name in STATUS_NAMES}


def empty_state_text(q=None, status=None):
    node = _list_page(q, status).select_one("#empty-state")
    return node.text() if node else None


def search_box_value(q):
    return _text_of_attr(_list_page(q), "form#search-form input[name=q]", "value")


def _text_of_attr(page, selector, attribute):
    node = page.select_one(selector)
    if node is None:
        raise AssertionError(f"the page has no element matching {selector!r}")
    return node.attrs.get(attribute, "")


# ----- one contact ----------------------------------------------------------------------


def status_of_get(path, q=None, status=None):
    return _get(path, q=q, status=status).status_code


def details_of(contact_id):
    """What the contact page shows: 'name | email | phone | company | status'."""
    response = _get(f"/contacts/{contact_id}")
    if response.status_code != 200:
        raise AssertionError(f"GET /contacts/{contact_id} answered status {response.status_code}")
    page = _page(response)
    return _line(*(_text_of(page, f"#contact-{field}") for field in ("name", "email", "phone", "company", "status")))


def edit_form_values(contact_id):
    """What the edit form on the contact page is pre-filled with: 'name | email | phone | company | status'."""
    page = _page(_get(f"/contacts/{contact_id}"))
    values = _form_values(page, "edit-contact-form", ["name", "email", "phone", "company"])
    chosen = page.select_one("form#edit-contact-form option[selected]")
    status = chosen.attrs.get("value") if chosen else None
    return _line(values["name"], values["email"], values["phone"], values["company"], status)


def form_target(path, form_id):
    """'POST /contacts/1/notes': the method and address a form on that page submits to."""
    node = _page(_get(path)).select_one(f"form#{form_id}")
    if node is None:
        raise AssertionError(f"{path} has no form#{form_id}")
    return node.attrs.get("method", "get").upper() + " " + node.attrs.get("action", "")


def form_field_names(path, form_id):
    nodes = _page(_get(path)).select(f"form#{form_id} [name]")
    return sorted({node.attrs["name"] for node in nodes})


def errors_on_page(path):
    return _errors_of(_page(_get(path)))


def page_contains_raw(path, text):
    """Does the HTML source of the page contain this exact text (not the text as a browser would show it)?"""
    return text in _get(path).get_data(as_text=True)


# ----- notes -------------------------------------------------------------------------


def notes_of(contact_id):
    """The notes on the contact page, in the order shown (newest first)."""
    page = _page(_get(f"/contacts/{contact_id}"))
    return [node.text() for node in page.select("#notes .note-text")]


def no_notes_text(contact_id):
    node = _page(_get(f"/contacts/{contact_id}")).select_one("#no-notes")
    return node.text() if node else None


# ----- setup steps for stories: these must succeed ------------------------------------------


def add_contact(name, email, phone=None, company=None, status=None):
    _must_succeed(
        _post("/contacts", follow=True, name=name, email=email, phone=phone, company=company, status=status),
        "adding the contact",
    )


def edit_contact(contact_id, name, email, status, phone="", company=""):
    response = _post(
        f"/contacts/{contact_id}/edit", follow=True, name=name, email=email, phone=phone, company=company, status=status
    )
    _must_succeed(response, "editing the contact")


def delete_contact(contact_id):
    _must_succeed(_post(f"/contacts/{contact_id}/delete", follow=True), "deleting the contact")


def add_note(contact_id, text):
    _must_succeed(_post(f"/contacts/{contact_id}/notes", follow=True, text=text), "adding the note")


# ----- the JSON API -----------------------------------------------------------------------------


def api_names(q=None, status=None):
    return [item["name"] for item in _json(_get("/api/contacts", q=q, status=status))]


def _api_line(item):
    return _line(item["id"], item["name"], item["email"], item["phone"], item["company"], item["status"])


def api_row(name):
    """The JSON of the contact with this name in the list: 'id | name | email | phone | company | status'."""
    for item in _json(_get("/api/contacts")):
        if item["name"] == name:
            return _api_line(item)
    return None


def api_contact(contact_id):
    """The JSON of one contact: 'id | name | email | phone | company | status'."""
    return _api_line(_json(_get(f"/api/contacts/{contact_id}")))


def api_notes_of(contact_id):
    return _json(_get(f"/api/contacts/{contact_id}"))["notes"]


def api_failure(path):
    """What an API address that fails answers: its status code and the error message in the JSON body."""
    response = _get(path)
    return {"status": response.status_code, "error": _json(response).get("error")}


def api_content_type(path):
    return _get(path).mimetype


class CRM:
    """The CRM as a story sees it. Every method is one visit to the app or one form submission."""

    add_contact = staticmethod(add_contact)
    edit_contact = staticmethod(edit_contact)
    delete_contact = staticmethod(delete_contact)
    add_note = staticmethod(add_note)
    after_creating = staticmethod(after_creating)
    after_editing = staticmethod(after_editing)
    after_deleting = staticmethod(after_deleting)
    after_adding_note = staticmethod(after_adding_note)
    errors_when_creating = staticmethod(errors_when_creating)
    errors_when_editing = staticmethod(errors_when_editing)
    errors_when_adding_note = staticmethod(errors_when_adding_note)
    kept_value_when_editing = staticmethod(kept_value_when_editing)
    flash_after_editing = staticmethod(flash_after_editing)
    flash_after_deleting = staticmethod(flash_after_deleting)
    flash_after_adding_note = staticmethod(flash_after_adding_note)
    names_listed = staticmethod(names_listed)
    emails_listed = staticmethod(emails_listed)
    row_of = staticmethod(row_of)
    ids_listed = staticmethod(ids_listed)
    link_of = staticmethod(link_of)
    pipeline_counts = staticmethod(pipeline_counts)
    empty_state_text = staticmethod(empty_state_text)
    status_of_get = staticmethod(status_of_get)
    details_of = staticmethod(details_of)
    edit_form_values = staticmethod(edit_form_values)
    form_target = staticmethod(form_target)
    form_field_names = staticmethod(form_field_names)
    errors_on_page = staticmethod(errors_on_page)
    page_contains_raw = staticmethod(page_contains_raw)
    notes_of = staticmethod(notes_of)
    no_notes_text = staticmethod(no_notes_text)
    api_names = staticmethod(api_names)
    api_row = staticmethod(api_row)
    api_contact = staticmethod(api_contact)
    api_notes_of = staticmethod(api_notes_of)
    api_content_type = staticmethod(api_content_type)
