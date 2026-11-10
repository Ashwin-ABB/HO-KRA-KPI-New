import frappe
from frappe import _
from frappe.model.document import Document

DEFAULT_BRANCH = "Head Office"


def get_branches():
	"""Branches chosen in Internal Feedback Settings, otherwise Head Office."""
	chosen = frappe.get_all(
		"Internal Feedback Branch",
		filters={"parent": "Internal Feedback Settings", "parenttype": "Internal Feedback Settings"},
		pluck="branch",
		order_by="idx asc",
	)
	return [b for b in chosen if b] or [DEFAULT_BRANCH]


def ensure_defaults():
	"""First time only: pre-select Head Office if that branch exists. Runs after install and migrate."""
	doc = frappe.get_single("Internal Feedback Settings")
	if doc.get("branches"):
		return
	actual = frappe.db.get_value("Branch", DEFAULT_BRANCH, "name")
	if actual:
		doc.append("branches", {"branch": actual})
		doc.flags.ignore_permissions = True
		doc.save()
		frappe.db.commit()


class InternalFeedbackSettings(Document):
	def validate(self):
		chosen = [d.branch for d in self.get("branches", [])]
		if len(chosen) != len(set(chosen)):
			frappe.throw(_("A branch is listed more than once."))
