import calendar
from datetime import date

import frappe
from frappe import _
from frappe.utils import cint, flt

from kra_kpi.kra.doctype.ho_traffic_light_settings.ho_traffic_light_settings import (
	INTERNAL_FEEDBACK_MAX,
	KPI_MAX,
	PTS_MAX,
	get_rules,
	rating_for,
)
from kra_kpi.kra.doctype.internal_feedback_settings.internal_feedback_settings import get_branches

MONTHS = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]
RATING_COLOURS = {"Green": "#16a34a", "Yellow": "#eab308", "Red": "#dc2626", "Grey": "#9ca3af"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	month = filters.month
	year = cint(filters.year)
	if month not in MONTHS or not year:
		frappe.throw(_("Please select a Month and a Year."))
	month_no = MONTHS.index(month) + 1
	start = date(year, month_no, 1)
	end = date(year, month_no, calendar.monthrange(year, month_no)[1])

	branches = [filters.branch] if filters.branch else get_branches()
	employees = frappe.get_all(
		"Employee",
		filters={"branch": ["in", branches], "status": "Active"},
		fields=["name", "employee_name"],
		order_by="employee_name asc",
	)

	# Internal Feedback: average of the employee's submitted scores dated in the month (already out of 20)
	feedback = {
		r.employee: r.score
		for r in frappe.db.sql(
			"""
			select c.employee, avg(c.internal_feedback) as score
			from `tabInternal Feedback Item` c
			inner join `tabInternal Feedback` p on p.name = c.parent
			where p.docstatus = 1 and coalesce(c.date, p.date) between %s and %s
			group by c.employee
			""",
			(start, end),
			as_dict=True,
		)
	}
	# KPI: Monthly KPI Entry total is out of 100; shown out of 65
	kpi = {
		r.employee: r.total_score
		for r in frappe.get_all(
			"Monthly KPI Entry",
			filters={"month": month, "year": year, "docstatus": ["<", 2]},
			fields=["employee", "total_score"],
		)
	}
	# PTS: HO PTS Entry total is out of 15 and used as it is
	pts = {
		r.employee: r.total_score
		for r in frappe.get_all(
			"HO PTS Entry",
			filters={"month": month, "year": year, "docstatus": ["<", 2]},
			fields=["employee", "total_score"],
		)
	}

	rules = get_rules()
	data = []
	counts = {"Green": 0, "Yellow": 0, "Red": 0, "Grey": 0}
	for emp in employees:
		internal = round(min(flt(feedback[emp.name]), INTERNAL_FEEDBACK_MAX), 1) if emp.name in feedback else None
		kpi_score = round(flt(kpi[emp.name]) * KPI_MAX / 100, 1) if emp.name in kpi else None
		pts_score = round(min(flt(pts[emp.name]), PTS_MAX), 1) if emp.name in pts else None

		parts = [internal, kpi_score, pts_score]
		total = round(sum(p for p in parts if p is not None), 1)
		pending = [n for n, p in (("Internal Feedback", internal), ("KPI", kpi_score), ("PTS", pts_score)) if p is None]

		row = {
			"employee": emp.name,
			"employee_name": emp.employee_name,
			"internal_feedback": internal,
			"kpi_score": kpi_score,
			"pts_score": pts_score,
			"total_score": total,
			"pending": ", ".join(pending),
		}
		for key in ("internal_feedback", "kpi_score", "pts_score", "total_score"):
			row[key + "_rating"] = rating_for(row[key], rules[key])
		counts[row["total_score_rating"]] += 1
		data.append(row)

	return get_columns(), data, None, get_chart(counts), get_summary(counts, len(data))


def get_columns():
	def col(fieldname, label, fieldtype="Float", width=120, **kw):
		return {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, "width": width, **kw}

	return [
		col("employee", _("Emp Code"), "Link", 110, options="Employee"),
		col("employee_name", _("Employee Name"), "Data", 180),
		col("internal_feedback", _("Internal Feedback ({0})").format(INTERNAL_FEEDBACK_MAX), precision=1),
		col("kpi_score", _("KPI Score ({0})").format(KPI_MAX), precision=1),
		col("pts_score", _("PTS ({0})").format(PTS_MAX), precision=1),
		col("total_score", _("Total Score (100)"), precision=1),
		col("pending", _("Pending"), "Data", 200),
		# ratings travel with each row so the report can colour the cells
		col("internal_feedback_rating", "", "Data", 0, hidden=1),
		col("kpi_score_rating", "", "Data", 0, hidden=1),
		col("pts_score_rating", "", "Data", 0, hidden=1),
		col("total_score_rating", "", "Data", 0, hidden=1),
	]


def get_summary(counts, total):
	summary = [{"value": total, "label": _("Employees"), "datatype": "Int", "indicator": "Blue"}]
	for name in ("Green", "Yellow", "Red", "Grey"):
		summary.append({"value": counts[name], "label": _(name), "datatype": "Int", "indicator": name})
	return summary


def get_chart(counts):
	names = ["Green", "Yellow", "Red", "Grey"]
	return {
		"data": {
			"labels": [_(n) for n in names],
			"datasets": [{"name": _("Employees"), "values": [counts[n] for n in names]}],
		},
		"type": "bar",
		"colors": [RATING_COLOURS[n] for n in names],
	}
