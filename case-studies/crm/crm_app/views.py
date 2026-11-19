"""Routes: HTML pages and the JSON API."""

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)

from .store import STATUSES
from .validation import clean_contact_form, clean_note

pages = Blueprint("pages", __name__)
api = Blueprint("api", __name__)


def store():
    return current_app.extensions["contacts"]


def contact_or_404(contact_id):
    contact = store().get(contact_id)
    if contact is None:
        abort(404)
    return contact


def search_args():
    return request.args.get("q", "").strip(), request.args.get("status", "").strip()


def render_list(form=None, errors=None, code=200):
    q, status = search_args()
    contacts = store().all(q, status)
    return (
        render_template(
            "list.html",
            contacts=contacts,
            has_any=bool(store().all()),
            counts=store().pipeline(),
            q=q,
            status_filter=status,
            statuses=STATUSES,
            form=form or {"status": "lead"},
            errors=errors or {},
        ),
        code,
    )


def render_contact(contact, form=None, errors=None, note_text="", code=200):
    return (
        render_template(
            "contact.html",
            contact=contact,
            notes=list(reversed(contact.notes)),
            statuses=STATUSES,
            form=form or contact.as_dict(),
            errors=errors or {},
            note_text=note_text,
        ),
        code,
    )


@pages.get("/contacts")
def list_contacts():
    return render_list()


@pages.post("/contacts")
def create_contact():
    values, errors = clean_contact_form(request.form, store())
    if errors:
        return render_list(form=values, errors=errors, code=400)
    contact = store().add(values)
    flash("Contact created.")
    return redirect(url_for("pages.show_contact", contact_id=contact.id))


@pages.get("/contacts/<int:contact_id>")
def show_contact(contact_id):
    return render_contact(contact_or_404(contact_id))


@pages.post("/contacts/<int:contact_id>/edit")
def edit_contact(contact_id):
    contact = contact_or_404(contact_id)
    values, errors = clean_contact_form(request.form, store(), current=contact)
    if errors:
        return render_contact(contact, form=values, errors=errors, code=400)
    store().update(contact, values)
    flash("Contact updated.")
    return redirect(url_for("pages.show_contact", contact_id=contact.id))


@pages.post("/contacts/<int:contact_id>/delete")
def delete_contact(contact_id):
    contact_or_404(contact_id)
    store().delete(contact_id)
    flash("Contact deleted.")
    return redirect(url_for("pages.list_contacts"))


@pages.post("/contacts/<int:contact_id>/notes")
def add_note(contact_id):
    contact = contact_or_404(contact_id)
    text, errors = clean_note(request.form)
    if errors:
        return render_contact(contact, errors=errors, note_text=request.form.get("text", ""), code=400)
    store().add_note(contact, text)
    flash("Note added.")
    return redirect(url_for("pages.show_contact", contact_id=contact.id))


@api.get("/contacts")
def api_list():
    q, status = search_args()
    return jsonify([c.as_dict() for c in store().all(q, status)])


@api.get("/contacts/<int:contact_id>")
def api_show(contact_id):
    contact = contact_or_404(contact_id)
    return jsonify({**contact.as_dict(), "notes": list(reversed(contact.notes))})
