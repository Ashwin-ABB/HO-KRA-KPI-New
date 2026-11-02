import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

MONTHS = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]
PRIVILEGED_ROLES = {"System Manager", "HR Manager"}


def _check_access(employee):
	"""HR/System Manager can use any employee; others only their own record."""
	if PRIVILEGED_ROLES & set(frappe.get_roles()):
		return
	own = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	if employee != own:
		frappe.throw(_("You can only enter KPIs for your own employee record."))


def _master_rows(employee):
	if not frappe.db.exists("KPI Master", employee):
		frappe.throw(_("No KPI Master found for {0}. Please ask HR to create it.").format(employee))
	master = frappe.get_doc("KPI Master", employee)
	if not master.is_active:
		frappe.throw(_("The KPI Master for {0} is not active.").format(employee))
	return master.items


@frappe.whitelist()
def get_kpi_rows(employee):
	_check_access(employee)
	return [
		{"kra": r.kra, "goal_name": r.goal_name, "target": r.target, "weightage": r.weightage}
		for r in _master_rows(employee)
	]


class MonthlyKPIEntry(Document):
	def validate(self):
		_check_access(self.employee)
		self.set_period()
		self.check_duplicate()
		self.sync_with_master()
		self.calculate_score()

	def set_period(self):
		d = getdate(self.entry_date)
		self.month = MONTHS[d.month - 1]
		self.year = d.year

	def check_duplicate(self):
		existing = frappe.db.exists(
			"Monthly KPI Entry",
			{
				"employee": self.employee,
				"month": self.month,
				"year": self.year,
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("{0} already has an entry for {1} {2}: {3}").format(
					self.employee, self.month, self.year, existing
				)
			)

	def sync_with_master(self):
		"""Target and weightage always come from the KPI Master, never from the form."""
		master = {(r.kra, r.goal_name): r for r in _master_rows(self.employee)}
		seen = set()
		for row in self.items:
			key = (row.kra, row.goal_name)
			if key not in master:
				frappe.throw(_("Row {0}: '{1}' is not in the KPI Master.").format(row.idx, row.kra))
			row.target = master[key].target
			row.weightage = master[key].weightage
			seen.add(key)
		# pick up any KPI added to the master after this entry was started
		for key, m in master.items():
			if key not in seen:
				self.append(
					"items",
					{"kra": m.kra, "goal_name": m.goal_name, "target": m.target, "weightage": m.weightage},
				)

	def calculate_score(self):
		"""Score per KPI = min(actual / target, 1) x weightage. Total is out of the total weightage (100)."""
		total_score = total_weightage = 0
		for row in self.items:
			if flt(row.actual_value) < 0:
				frappe.throw(_("Row {0}: Actual Value cannot be negative.").format(row.idx))
			ratio = min(flt(row.actual_value) / flt(row.target), 1) if flt(row.target) > 0 else 0
			row.achievement = ratio * 100
			row.score = round(ratio * flt(row.weightage), 2)
			total_score += row.score
			total_weightage += flt(row.weightage)
		self.total_score = round(total_score, 2)
		self.total_weightage = total_weightage
