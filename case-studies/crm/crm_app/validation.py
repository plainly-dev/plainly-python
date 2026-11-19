"""All input cleaning and validation rules live here."""

import re

from .store import STATUSES

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s.]+(\.[^@\s.]+)+")
FIELDS = ("name", "email", "phone", "company", "status")


def clean_contact_form(form, store, current=None):
    """Return (values, errors). `current` is the contact being edited (None on create).

    values always holds the trimmed text typed, so a refused form can be shown again.
    A blank status means 'lead' on create and 'unchanged' on edit.
    """
    values = {f: (form.get(f) or "").strip() for f in FIELDS}
    if not values["status"]:
        values["status"] = current.status if current else "lead"
    errors = {}

    if not values["name"]:
        errors["name"] = "Name is required."
    elif len(values["name"]) > 100:
        errors["name"] = "Name must be at most 100 characters."

    if not values["email"]:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.fullmatch(values["email"]):
        errors["email"] = "Enter a valid email address."
    elif store.email_taken(values["email"], ignore_id=current.id if current else None):
        errors["email"] = "This email is already in use."

    if values["status"] not in STATUSES:
        errors["status"] = "Status must be lead, customer or lost."
    return values, errors


def clean_note(form):
    text = (form.get("text") or "").strip()
    return text, ({} if text else {"text": "Note cannot be empty."})
