import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HOPTSMaster(Document):
	def validate(self):
		if not (self.daily_tasks or self.weekly_tasks or self.monthly_tasks):
			frappe.throw(_("Add at least one task to the checklist."))
		weights = [flt(self.daily_weightage), flt(self.weekly_weightage), flt(self.monthly_weightage)]
		if any(x < 0 for x in weights):
			frappe.throw(_("Weightage cannot be negative."))
		self.total_weightage = sum(weights)
