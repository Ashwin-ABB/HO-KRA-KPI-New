import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate

from kra_kpi.kra.rating_utils import MONTHS, check_reports_to, rating_score, require_own

QUESTIONS = ("approachability", "ethics_accountability", "continue_same_team", "work_allocation")


class EmployeeRatingManager(Document):
	def validate(self):
		require_own(self.employee, _("You can only rate your own manager."))
		check_reports_to(self.manager, self.employee)

		d = getdate(self.rating_month)
		if d.day != calendar.monthrange(d.year, d.month)[1]:
			frappe.throw(_("Please select the last date of the rating month."))
		self.rating_month_name, self.rating_year = MONTHS[d.month - 1], d.year

		self.rating_value, self.score = rating_score(self.overall_rating)
		self.questions_total = sum(cint(self.get(q)) for q in QUESTIONS)
		self.check_duplicate()

	def check_duplicate(self):
		existing = frappe.db.exists(
			"Employee Rating Manager",
			{
				"manager": self.manager,
				"employee": self.employee,
				"rating_month_name": self.rating_month_name,
				"rating_year": self.rating_year,
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("{0} has already rated {1} for {2} {3}: {4}").format(
					self.employee, self.manager, self.rating_month_name, self.rating_year, existing
				)
			)
