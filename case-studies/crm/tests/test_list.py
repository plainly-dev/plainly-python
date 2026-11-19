"""The contacts list page: the table, the empty state and the pipeline summary."""

from plainly import given, spec

from rules import CRM, empty_state_text, errors_on_page, names_listed, pipeline_counts, status_of_get

list_status = spec(status_of_get)
page_errors = spec(errors_on_page)
nobody = {"lead": 0, "customer": 0, "lost": 0}


def test_the_list_page_opens_on_a_new_crm():
    list_status.if_("/contacts").then_give(200)


def test_a_new_crm_shows_an_empty_state_and_no_rows():
    spec(empty_state_text).if_().then_give("No contacts yet.")
    spec(names_listed).if_().then_give([])


def test_the_pipeline_of_a_new_crm_counts_zero_of_each_status():
    spec(pipeline_counts).if_().then_give(nobody)


def test_the_list_page_shows_no_error_messages():
    page_errors.if_("/contacts").then_give({})


def test_the_empty_state_goes_away_once_there_is_a_contact():
    crm = given(CRM)
    crm.empty_state_text()
    crm.then.gave("No contacts yet.")
    crm.add_contact(name="Ann Lee", email="ann@example.com")
    crm.empty_state_text()
    crm.then.gave(None)


def test_contacts_are_listed_in_the_order_they_were_added():
    crm = given(CRM)
    crm.add_contact(name="Carol", email="carol@example.com")
    crm.add_contact(name="Alice", email="alice@example.com")
    crm.add_contact(name="Bob", email="bob@example.com")
    crm.names_listed()
    crm.then.gave(["Carol", "Alice", "Bob"])
    crm.emails_listed()
    crm.then.gave(["carol@example.com", "alice@example.com", "bob@example.com"])


def test_each_row_is_marked_with_the_id_of_its_contact_and_links_to_it():
    crm = given(CRM)
    crm.add_contact(name="Carol", email="carol@example.com")
    crm.add_contact(name="Alice", email="alice@example.com")
    crm.ids_listed()
    crm.then.gave(["1", "2"])
    crm.link_of("Alice")
    crm.then.gave("/contacts/2")


def test_each_row_shows_the_email_phone_company_and_status():
    crm = given(CRM)
    crm.add_contact(
        name="Ann Lee", email="ann@example.com", phone="555-0100", company="Acme Corp", status="customer"
    )
    crm.row_of("Ann Lee")
    crm.then.gave("ann@example.com | 555-0100 | Acme Corp | customer")


def test_a_contact_without_phone_or_company_shows_them_empty():
    crm = given(CRM)
    crm.add_contact(name="Bob Stone", email="bob@example.com")
    crm.row_of("Bob Stone")
    crm.then.gave("bob@example.com | (blank) | (blank) | lead")


def test_the_pipeline_counts_the_contacts_of_each_status():
    crm = given(CRM)
    crm.add_contact(name="One", email="one@example.com", status="lead")
    crm.add_contact(name="Two", email="two@example.com", status="lead")
    crm.add_contact(name="Three", email="three@example.com", status="lead")
    crm.add_contact(name="Four", email="four@example.com", status="customer")
    crm.add_contact(name="Five", email="five@example.com", status="lost")
    crm.add_contact(name="Six", email="six@example.com", status="lost")
    crm.pipeline_counts()
    crm.then.gave({"lead": 3, "customer": 1, "lost": 2})


def test_the_pipeline_follows_edits_and_deletes():
    crm = given(CRM)
    crm.add_contact(name="One", email="one@example.com", status="lead")
    crm.add_contact(name="Two", email="two@example.com", status="lead")
    crm.edit_contact(1, name="One", email="one@example.com", status="customer")
    crm.pipeline_counts()
    crm.then.gave({"lead": 1, "customer": 1, "lost": 0})
    crm.delete_contact(2)
    crm.pipeline_counts()
    crm.then.gave({"lead": 0, "customer": 1, "lost": 0})
