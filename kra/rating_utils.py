import frappe
from frappe import _
from frappe.utils import cint, flt

MONTHS = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]
PRIVILEGED_ROLES = {"System Manager", "HR Manager"}

# The 1 to 10 scale shown in the rating dropdowns. The score for each is kept in Rating Score Master.
RATING_OPTIONS = [
	"1 - Unacceptable",
	"2 - Poor Performance",
	"3 - Weak",
	"4 - Not Satisfied",
	"5 - Average",
	"6 - Above Average",
	"7 - Good",
	"8 - Very Good",
	"9 - Excellent",
	"10 - Outstanding",
]


def own_employee():
	return frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "name")


def require_own(employee, message):
	"""HR / System Manager can act for anyone; everyone else only as themselves."""
	if PRIVILEGED_ROLES & set(frappe.get_roles()):
		return
	if own_employee() != employee:
		frappe.throw(message)


def check_reports_to(manager, employee):
	if manager == employee:
		frappe.throw(_("The manager and the employee cannot be the same person."))
	if frappe.db.get_value("Employee", employee, "reports_to") != manager:
		frappe.throw(_("{0} does not report to {1}.").format(employee, manager))


def rating_score(label):
	"""(rating number, score) for a rating such as '8 - Very Good'; the score comes from Rating Score Master."""
	if not label:
		return 0, 0
	number = cint(label.split(" - ")[0])
	score = frappe.db.get_value("Rating Score Master", label, "score")
	return number, flt(score) if score is not None else flt(number)


def previous_month(d):
	"""Month name and year of the month before date d."""
	year, month = d.year, d.month - 1
	if month == 0:
		month, year = 12, year - 1
	return MONTHS[month - 1], year


@frappe.whitelist()
def get_managers():
	"""Active employees that at least one active employee reports to."""
	rows = frappe.get_all("Employee", filters={"status": "Active", "reports_to": ["is", "set"]}, pluck="reports_to")
	return sorted(set(rows))
