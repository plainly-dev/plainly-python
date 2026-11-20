"""The HTML page a person opens in the browser."""
from plainly import expect, given

from crm import CRM


def test_an_empty_crm_says_so():
    crm = given(CRM)
    crm.get("/").then.has(status=200)
    expect(crm.page).should.contain("No contacts yet")


def test_the_page_lists_names_and_companies_in_name_order():
    crm = given(CRM)
    crm.post("/api/contacts", name="Bob Stone", email="bob@x.io", company="Globex")
    crm.post("/api/contacts", name="Ann Lee", email="ann@x.io", company="Acme")
    crm.get("/").then.has(status=200)
    expect(crm.page).should.contain("Ann Lee")
    expect(crm.page).should.contain("Acme")
    expect(crm.page).should.not_.contain("No contacts yet")
    expect(crm.page).should.match(r"(?s)Ann Lee.*Bob Stone")


def test_names_and_companies_are_escaped():
    crm = given(CRM)
    crm.post("/api/contacts", name="<b>Bo</b>", email="bo@x.io", company="<script>x()</script>")
    crm.get("/")
    expect(crm.page).should.contain("&lt;b&gt;Bo&lt;/b&gt;")
    expect(crm.page).should.not_.contain("<script>x()</script>")
