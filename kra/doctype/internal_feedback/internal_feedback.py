import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kra_kpi.kra.doctype.internal_feedback_settings.internal_feedback_settings import get_branches


@frappe.whitelist()
def get_employees(branch=None):
	"""Active employees of the chosen branch, or of the branches saved in Internal Feedback Settings."""
	frappe.has_permission("Internal Feedback", "create", throw=True)
	branches = [branch] if branch else get_branches()
	return frappe.get_all(
		"Employee",
		filters={"branch": ["in", branches], "status": "Active"},
		fields=["name as employee", "employee_name"],
		order_by="employee_name asc",
	)


class InternalFeedback(Document):
	def validate(self):
		if not self.items:
			frappe.throw(_("The sheet has no employees."))
		allowed = {b.casefold() for b in ([self.branch] if self.branch else get_branches())}
		seen = set()
		for row in self.items:
			if row.employee in seen:
				frappe.throw(_("Row {0}: {1} is listed more than once.").format(row.idx, row.employee))
			seen.add(row.employee)

			branch = frappe.db.get_value("Employee", row.employee, "branch") or ""
			if branch.casefold() not in allowed:
				frappe.throw(
					_("Row {0}: {1} belongs to branch '{2}', which is not allowed for this sheet.").format(
						row.idx, row.employee, branch
					)
				)
			if flt(row.internal_feedback) < 0:
				frappe.throw(_("Row {0}: Internal Feedback cannot be negative.").format(row.idx))
			row.date = row.date or self.date
