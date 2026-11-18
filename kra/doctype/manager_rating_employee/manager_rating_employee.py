import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from kra_kpi.kra.rating_utils import check_reports_to, previous_month, rating_score, require_own


class ManagerRatingEmployee(Document):
	def validate(self):
		require_own(self.manager, _("You can only rate employees who report to you."))
		check_reports_to(self.manager, self.employee)
		self.rated_month, self.rated_year = previous_month(getdate(self.date))
		self.rating_value, self.score = rating_score(self.overall_rating)
		self.check_duplicate()

	def check_duplicate(self):
		existing = frappe.db.exists(
			"Manager Rating Employee",
			{
				"manager": self.manager,
				"employee": self.employee,
				"rated_month": self.rated_month,
				"rated_year": self.rated_year,
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("{0} is already rated for {1} {2}: {3}").format(self.employee, self.rated_month, self.rated_year, existing)
			)
