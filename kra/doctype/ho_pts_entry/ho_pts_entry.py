import calendar
import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

MONTHS = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]
PRIVILEGED_ROLES = {"System Manager", "HR Manager"}
# Y = completed; H (holiday) and NA (on duty) are also counted. N, L (leave) and blank are not.
COUNTED = {"Y", "H", "NA"}
# (entry table, master table, key)
SECTIONS = (
	("daily_entries", "daily_tasks", "daily"),
	("weekly_entries", "weekly_tasks", "weekly"),
	("monthly_entries", "monthly_tasks", "monthly"),
)


def period_fields(key, days_in_month):
	"""The columns that exist for this month."""
	if key == "daily":
		return ["d%d" % i for i in range(1, days_in_month + 1)]
	if key == "weekly":
		return ["w%d" % i for i in range(1, -(-days_in_month // 7) + 1)]
	return ["status"]


def all_fields(key):
	if key == "daily":
		return ["d%d" % i for i in range(1, 32)]
	if key == "weekly":
		return ["w%d" % i for i in range(1, 6)]
	return ["status"]


def _check_access(employee):
	"""HR/System Manager can use any employee; everyone else only their own record."""
	if PRIVILEGED_ROLES & set(frappe.get_roles()):
		return
	own = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	if employee != own:
		frappe.throw(_("You can only fill in your own checklist."))


def _master(employee):
	if not frappe.db.exists("HO PTS Master", employee):
		frappe.throw(_("No HO PTS Master found for {0}. Please ask HR to create it.").format(employee))
	master = frappe.get_doc("HO PTS Master", employee)
	if not master.is_active:
		frappe.throw(_("The HO PTS Master for {0} is not active.").format(employee))
	return master


def _task_row(t):
	return {
		"master_row": t.name,
		"main_task": t.main_task,
		"expected_outcome": t.expected_outcome,
		"time_line": t.time_line,
		"data": t.data,
	}


@frappe.whitelist()
def get_checklist(employee):
	"""The logged-in employee's own checklist, from their HO PTS Master."""
	_check_access(employee)
	master = _master(employee)
	return {
		"daily": [_task_row(t) for t in master.daily_tasks],
		"weekly": [_task_row(t) for t in master.weekly_tasks],
		"monthly": [_task_row(t) for t in master.monthly_tasks],
		"weightage": {
			"daily": master.daily_weightage,
			"weekly": master.weekly_weightage,
			"monthly": master.monthly_weightage,
		},
	}


class HOPTSEntry(Document):
	def validate(self):
		_check_access(self.employee)
		self.set_period()
		self.check_duplicate()
		self.sync_with_master()
		self.calculate_score()

	def set_period(self):
		d = getdate(self.posting_date)
		self.month = MONTHS[d.month - 1]
		self.year = d.year
		self.days_in_month = calendar.monthrange(d.year, d.month)[1]

	def check_duplicate(self):
		existing = frappe.db.exists(
			"HO PTS Entry",
			{"employee": self.employee, "month": self.month, "year": self.year, "name": ["!=", self.name or ""]},
		)
		if existing:
			frappe.throw(
				_("{0} already has an entry for {1} {2}: {3}").format(self.employee, self.month, self.year, existing)
			)

	def sync_with_master(self):
		"""Task text comes from the master; tasks added to the master later are appended."""
		master = _master(self.employee)
		self.daily_weightage = master.daily_weightage
		self.weekly_weightage = master.weekly_weightage
		self.monthly_weightage = master.monthly_weightage
		for table, source, _key in SECTIONS:
			tasks = {t.name: t for t in master.get(source)}
			seen = set()
			for row in self.get(table):
				task = tasks.get(row.master_row)
				if task:
					row.update({k: v for k, v in _task_row(task).items() if k != "master_row"})
					seen.add(row.master_row)
			for name, task in tasks.items():
				if name not in seen:
					self.append(table, _task_row(task))

	def calculate_score(self):
		"""Score = achieved / target x weightage, rounded to a whole number, for daily, weekly and monthly."""
		days = self.days_in_month
		total_score = total_weight = 0
		for table, _source, key in SECTIONS:
			rows = self.get(table)
			used = period_fields(key, days)
			achieved = 0
			for row in rows:
				for fieldname in all_fields(key):
					if fieldname not in used:
						row.set(fieldname, None)
					elif row.get(fieldname) in COUNTED:
						achieved += 1
			target = len(rows) * len(used)
			weight = flt(self.get(key + "_weightage"))
			score = int(math.floor(achieved / target * weight + 0.5)) if target else 0
			self.set(key + "_target", target)
			self.set(key + "_achieved", achieved)
			self.set(key + "_score", score)
			total_score += score
			total_weight += weight
		self.total_weightage = total_weight
		self.total_score = total_score
