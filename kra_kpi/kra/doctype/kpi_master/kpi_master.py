import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class KPIMaster(Document):
	def validate(self):
		if not self.items:
			frappe.throw(_("Add at least one KPI task."))
		total = 0
		for row in self.items:
			if flt(row.target) <= 0:
				frappe.throw(_("Row {0}: Target must be greater than 0.").format(row.idx))
			if flt(row.weightage) <= 0:
				frappe.throw(_("Row {0}: Weightage must be greater than 0.").format(row.idx))
			total += flt(row.weightage)
		self.total_weightage = total
		if abs(total - 100) > 0.01:
			frappe.throw(_("Total weightage must be 100. It is currently {0}.").format(total))
