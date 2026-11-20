# CRM contract

This is everything the tests in this folder promise. The app does not exist yet: whoever builds it
(Trello card 11) reads this file and the tests, and must not change either.

## Shape

- A package `crm_app` with a function `create_app()` that returns a Flask app.
- Every call to `create_app()` starts a brand new, empty CRM. Nothing is shared between two apps
  (no files, no database on disk, no module-level lists).
- Contact ids are whole numbers. In a new CRM the first contact gets id 1, the next one id 2, and so on.
  Whether a deleted id can be reused is **not** promised.
- Note ids follow the same rule, counted across the whole CRM.

## Contacts

A contact, as the API returns it:

```json
{"id": 1, "name": "Ann Lee", "email": "ann@x.io", "company": "Acme", "status": "lead"}
```

| Field | Rule |
|---|---|
| `name` | required; spaces at both ends are removed; then 1 to 100 characters |
| `email` | required; spaces at both ends are removed; stored in lowercase; must look like `something@something.something` with no spaces; unique, ignoring case |
| `company` | optional; spaces at both ends are removed; an empty or missing company is stored as `null`; at most 100 characters |
| `status` | optional; one of `lead`, `customer`, `lost`; defaults to `lead` |

Fields the API does not know (for example `"age"`) are ignored.

## Endpoints

| Request | Success | Failure |
|---|---|---|
| `POST /api/contacts` (JSON body) | `201`, the new contact, and a `Location: /api/contacts/<id>` header | `400` invalid, `409` email taken |
| `GET /api/contacts` | `200`, `{"contacts": [...]}` sorted by name, ignoring case | `400` unknown `status` filter |
| `GET /api/contacts?q=<text>` | contacts whose name, email or company contains the text, ignoring case | |
| `GET /api/contacts?status=<status>` | only contacts with that status; combines with `q` | |
| `GET /api/contacts/<id>` | `200`, the contact | `404` |
| `PATCH /api/contacts/<id>` (JSON body) | `200`, the updated contact; only the fields sent change | `400`, `404`, `409` |
| `DELETE /api/contacts/<id>` | `204`, empty body; the contact and its notes are gone | `404` |
| `POST /api/contacts/<id>/notes` (JSON `{"text": ...}`) | `201`, `{"id": ..., "text": ...}` | `400` empty text, `404` unknown contact |
| `GET /api/contacts/<id>/notes` | `200`, `{"notes": [...]}`, newest first | `404` |
| `GET /api/pipeline` | `200`, `{"lead": n, "customer": n, "lost": n}`, always all three keys | |
| `GET /` | `200`, an HTML page listing every contact's name and company, sorted like the API | |

PATCH uses the same field rules as POST. Changing a contact's email to the email it already has is allowed.
`id` cannot be changed: an `id` in a PATCH body is ignored.

Note text: spaces at both ends are removed; then 1 to 1000 characters.

## Errors

- Every error answer is JSON, even for unknown ids.
- `400` for invalid fields: `{"errors": {"<field>": "<message>"}}`, one entry per invalid field.
  The messages are: `"is required"`, `"is too long"`, `"is not a valid email"`, `"is not a valid status"`.
- `400` for a body that is not a JSON object: `{"error": "expected a JSON object"}`.
- `400` for an unknown status filter: `{"error": "unknown status"}`.
- `404`: `{"error": "not found"}`.
- `409`: `{"error": "email already exists"}`.
- A refused request changes nothing.

## The HTML page

- Names and companies are HTML-escaped: a contact named `<b>Bo</b>` appears as `&lt;b&gt;Bo&lt;/b&gt;`.
- With no contacts, the page says `No contacts yet`.
