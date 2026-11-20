"""The only test helper: a CRM you talk to over HTTP, one request per method.

Reviewers: this file is the one place where wording is chosen by hand, so check it once.
Each method sends exactly one request, keeps what came back as plain attributes, and returns the CRM,
so the check can sit on the same line: `crm.post(...).then.has(status=201)`. The attributes are:

    status    the HTTP status code, e.g. 201
    body      the JSON answer (None if the answer is not JSON)
    error     body["error"]         (None if missing)
    errors    body["errors"]        (None if missing)
    names     the names in body["contacts"], in order
    texts     the texts in body["notes"], in order
    location  the Location header, e.g. "/api/contacts/1"
    page      the answer as text (for the HTML page)

The app is imported when the first CRM is created, so the tests can be collected before `crm_app` exists:
each test then fails on its own with ModuleNotFoundError.
"""
import json


class CRM:
    def __init__(self):
        from crm_app import create_app  # imported here on purpose, see the module docstring

        app = create_app()
        app.testing = True
        self._client = app.test_client()
        self.status = self.body = self.error = self.errors = self.location = None
        self.names, self.texts, self.page = [], [], ""

    # ----- one method per kind of request ---------------------------------------
    def post(self, path, **fields):
        """POST a JSON object made of the keyword arguments."""
        return self._keep(self._client.post(path, json=fields))

    def post_body(self, path, body):
        """POST raw text sent as application/json, for bodies that are not a JSON object."""
        return self._keep(self._client.post(path, data=body, content_type="application/json"))

    def get(self, path, **query):
        """GET, with the keyword arguments as the query string."""
        return self._keep(self._client.get(path, query_string=query))

    def patch(self, path, **fields):
        return self._keep(self._client.patch(path, json=fields))

    def delete(self, path):
        return self._keep(self._client.delete(path))

    # ----- what came back ------------------------------------------------------------
    def _keep(self, response):
        self.status = response.status_code
        self.page = response.get_data(as_text=True)
        self.location = _path_only(response.headers.get("Location"))
        try:
            self.body = json.loads(self.page) if self.page else None
        except ValueError:
            self.body = None
        body = self.body if isinstance(self.body, dict) else {}
        self.error = body.get("error")
        self.errors = body.get("errors")
        self.names = [c.get("name") for c in body.get("contacts", [])]
        self.texts = [n.get("text") for n in body.get("notes", [])]
        return self  # so a check can follow on the same line: crm.post(...).then.has(status=201)


def _path_only(location):
    """Flask may answer with a full URL (http://localhost/api/contacts/1); keep only the path."""
    if location and "://" in location:
        location = "/" + location.split("://", 1)[1].split("/", 1)[-1]
    return location


def add_contact(**fields):
    """POST /api/contacts on a new, empty CRM; gives (status, body). Used for many examples of one rule."""
    crm = CRM()
    crm.post("/api/contacts", **fields)
    return crm.status, crm.body
