"""Storage layer: an in-memory contact book. One instance per app."""

from dataclasses import dataclass, field

STATUSES = ("lead", "customer", "lost")


@dataclass
class Contact:
    id: int
    name: str
    email: str
    phone: str = ""
    company: str = ""
    status: str = "lead"
    notes: list = field(default_factory=list)  # oldest first

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "status": self.status,
        }

    def matches(self, term):
        term = term.lower()
        return any(term in value.lower() for value in (self.name, self.email, self.company))


class ContactStore:
    def __init__(self):
        self._contacts = {}
        self._next_id = 1

    def all(self, q="", status=""):
        """Contacts in creation order, optionally filtered by search term and status."""
        q, status = q.strip(), status.strip()
        return [
            c
            for c in self._contacts.values()
            if (not q or c.matches(q)) and (not status or c.status == status)
        ]

    def get(self, contact_id):
        return self._contacts.get(contact_id)

    def email_taken(self, email, ignore_id=None):
        wanted = email.strip().lower()
        return any(c.email.lower() == wanted and c.id != ignore_id for c in self._contacts.values())

    def add(self, data):
        contact = Contact(id=self._next_id, **data)
        self._contacts[contact.id] = contact
        self._next_id += 1
        return contact

    def update(self, contact, data):
        for key, value in data.items():
            setattr(contact, key, value)

    def delete(self, contact_id):
        self._contacts.pop(contact_id, None)

    def add_note(self, contact, text):
        contact.notes.append(text)

    def pipeline(self):
        counts = dict.fromkeys(STATUSES, 0)
        for contact in self._contacts.values():
            counts[contact.status] += 1
        return counts
