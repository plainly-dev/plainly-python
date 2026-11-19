# Contract: what the tests look at

The tests only use `from crm_app import create_app` and `app.test_client()`.
`create_app({"TESTING": True})` must return a new, EMPTY CRM every call (no state shared between calls).
Flash messages need a session: set a `secret_key` (the tests send cookies back, so the normal Flask session works).
Anything not listed here is free: layout, styling, extra elements, extra pages, storage.

## Addresses

| Request | Result |
|---|---|
| `GET /contacts` | 200 HTML list page. Query: `q`, `status` (both optional) |
| `POST /contacts` | create (form fields below) |
| `GET /contacts/<id>` | 200 HTML contact page, 404 for an unknown id (also `/contacts/abc`, `/contacts/0`) |
| `POST /contacts/<id>/edit` | edit, 404 for an unknown id |
| `POST /contacts/<id>/delete` | delete, 404 for an unknown id |
| `POST /contacts/<id>/notes` | add a note, 404 for an unknown id |
| `GET /contacts/<id>/edit`, `/delete`, `/notes` | 405 (these are POST only) |
| any other address, e.g. `/nothing-here`, `/contacts/1/unknown` | 404 |
| `GET /api/contacts`, `GET /api/contacts/<id>` | JSON (below) |

`<id>` is an integer. The first contact created in a new CRM has id 1, then 2, 3, ... A refused submission does not use up an id.
(Whether the id of a deleted contact is ever reused is NOT specified.)

## Form fields (all `application/x-www-form-urlencoded`)

- Contact: `name`, `email`, `phone`, `company`, `status`. A field that is not sent counts as blank.
- Note: `text`.
- Every text value is trimmed (leading and trailing whitespace) before it is checked or stored.
- The edit form always sends all five contact fields (so a missing `status` on edit is NOT specified).
  An edit replaces every field; a blank `phone` or `company` clears it.
- No other field names inside the forms listed below, and no `name` attribute on buttons (the tests list every `[name]` in a form).

## Validation (same rules for create and edit)

Rejected submissions answer **status 400**, render the same page again (the form shows what was typed), show one message
per wrong field (all wrong fields at once), and store/change nothing. Accepted ones answer a redirect (302 or 303 or any 3xx).

| Field | Rule | Message (exact text) |
|---|---|---|
| name | not blank | `Name is required.` |
| name | at most 100 characters after trimming (100 is fine, 101 is not) | `Name must be at most 100 characters.` |
| email | not blank | `Email is required.` |
| email | looks like `local@domain.tld`: one `@`, something before it, a domain with at least one dot, no whitespace. Valid: `a@b.co`, `first.last+tag@example.com`, `o'brien@mail.example.org`. Invalid: `plainaddress`, `ann@`, `@example.com`, `ann@example`, `ann@@example.com`, `ann smith@example.com`, `ann@exa mple.com` | `Enter a valid email address.` |
| email | unique among contacts, compared case-insensitively after trimming. On edit a contact never conflicts with itself (same email, other case, extra spaces are fine) | `This email is already in use.` |
| status | one of `lead`, `customer`, `lost` (lowercase). Missing or blank means `lead` on create | `Status must be lead, customer or lost.` |
| note `text` | not blank after trimming | `Note cannot be empty.` |

Error element: any element with `class="error"` and a `data-field` attribute, e.g.
`<p class="error" data-field="email">Enter a valid email address.</p>`.
`data-field` is `name`, `email`, `status` or (for notes) `text`. Its visible text is exactly the message.
Pages without a problem have NO element with `class="error"` and `data-field`.
Phone and company have no rules (not tested for length or format).

## Redirects and confirmations

| After | Redirect to | Confirmation (`class="flash"` element, exact text) |
|---|---|---|
| successful create | `/contacts/<new id>` | `Contact created.` |
| successful edit | `/contacts/<id>` | `Contact updated.` |
| delete | `/contacts` | `Contact deleted.` |
| successful note | `/contacts/<id>` | `Note added.` |

The confirmation is an element `class="flash"` on the page you land on, visible text exactly as above, one element per
message, and it is shown only once (the next page view has no `class="flash"` element). Use the Flask `flash` / session mechanism or similar.

## HTML hooks

Visible text is read with whitespace collapsed; HTML entities are decoded like a browser does. Close every element
explicitly (no omitted `</li>`, `</td>`, `</tr>`, `</p>`): the tests' tiny parser does not guess implied end tags.
Void tags (`<input>`, `<br>`) may be written with or without `/`.

### List page `GET /contacts`

- Search form: `<form id="search-form" method="get" action="/contacts">` containing `<input name="q" value="...">`
  whose `value` is the search term as given (escaped normally). (A `status` select may be in it; not tested.)
- Pipeline summary: three elements `id="pipeline-lead"`, `id="pipeline-customer"`, `id="pipeline-lost"`;
  the visible text of each is only the integer count (`3`). Counts are over ALL contacts, never narrowed by `q`/`status`.
- Rows: one `<tr data-contact-id="<id>">` per contact, in id order (the order they were created), and NO other `tr` has
  `data-contact-id`. Inside a row, one element per field with these classes (visible text only, empty text when blank, no placeholder):
  `.name` (contains `<a href="/contacts/<id>">`), `.email`, `.phone`, `.company`, `.status` (text `lead` / `customer` / `lost`).
- Empty state: an element `id="empty-state"`, present ONLY when there are no rows. Text exactly `No contacts yet.` when the CRM has
  no contacts at all, and exactly `No contacts match your search.` when contacts exist but `q`/`status` leave none.
  (When there are rows there is no `id="empty-state"`.)
- New contact form: `<form id="new-contact-form" method="post" action="/contacts">` with inputs named `name`, `email`, `phone`, `company`
  and a `<select name="status">`; nothing else with a `name`.
- Search: `q` is trimmed; blank `q` means no search. Matches when the trimmed term is contained, case-insensitively, in the name, the
  email or the company (phone and status are not searched). `status` filters on equality (`lead`, `customer`, `lost`); blank means
  no filter; an unknown value (e.g. `vip`) gives status 200 with no rows (and the no-match message). Both together mean both must hold.

### Contact page `GET /contacts/<id>`

- Elements with ids `contact-name`, `contact-email`, `contact-phone`, `contact-company`, `contact-status`;
  visible text is just the value (empty when blank; `lead`/`customer`/`lost` for status).
- Edit form: `<form id="edit-contact-form" method="post" action="/contacts/<id>/edit">` with `<input name="name|email|phone|company" value="current">`
  and `<select name="status">` whose current status has `<option value="customer" selected>`. Nothing else with a `name`.
- Delete form: `<form id="delete-contact-form" method="post" action="/contacts/<id>/delete">`.
- Note form: `<form id="note-form" method="post" action="/contacts/<id>/notes">` with exactly one named field, `<textarea name="text">`
  (or an input named `text`).
- Notes: `<ul id="notes">` with one `<li class="note">` per note, newest first (the last note added is first), each containing
  an element `class="note-text"` whose visible text is exactly the (trimmed) note. Identical notes are both kept.
- When the contact has no notes: an element `id="no-notes"` with text exactly `No notes yet.`; it is absent otherwise.

### Re-shown forms after a refusal (status 400)

- Refused create: the response is a full HTML page containing `form#new-contact-form` again, its inputs' `value` attributes holding what was
  typed (trimmed or not: the tests only use values without surrounding spaces), plus the `class="error"` elements.
- Refused edit: the page of the contact (with `form#edit-contact-form`, same pre-filling rule, holding what was typed) plus the errors.
- Refused note: the page of the contact plus the `data-field="text"` error; no note is stored.
- A refused submission to an unknown contact id is a 404, not a 400.

## Escaping

All user text (name, email, phone, company, notes, the `q` echoed in the search box, values re-shown in forms) is HTML-escaped on every page.
The tests submit `<script>alert(1)</script>` and `"><script>alert(1)</script>` and check that the raw page source never contains them,
while the visible text and the input `value`s decode back to exactly what was typed.
The JSON API returns the raw text (JSON, not HTML-escaped).

## JSON API

- Both endpoints answer `Content-Type: application/json`.
- `GET /api/contacts` returns a bare JSON array, in creation order, each item an object with (at least) `id` (integer), `name`, `email`,
  `phone`, `company` (strings, `""` when blank) and `status`. Supports `q` and `status` exactly like the page (unknown status gives `[]`, status 200).
- `GET /api/contacts/<id>` returns one such object plus `notes`: an array of note texts, newest first (`[]` when none).
- Unknown id: status 404, JSON body `{"error": "Contact not found"}` (the `error` text is exact).
