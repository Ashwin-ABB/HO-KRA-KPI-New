import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

# Maximum of each column. KPI is stored out of 100 and shown out of 65.
INTERNAL_FEEDBACK_MAX = 20
KPI_MAX = 65
PTS_MAX = 15
TOTAL_MAX = 100

# key (report fieldname), label, maximum
COLUMNS = [
	("internal_feedback", "Internal Feedback", INTERNAL_FEEDBACK_MAX),
	("kpi_score", "KPI Score", KPI_MAX),
	("pts_score", "PTS", PTS_MAX),
	("total_score", "Total Score", TOTAL_MAX),
]


def default_rules():
	"""key -> {green, yellow, red}. Total starts at 70 / 50 / 40; the others at 80% / 60% of their maximum."""
	rules = {}
	for key, _label, maximum in COLUMNS:
		if key == "total_score":
			rules[key] = {"green": 70, "yellow": 50, "red": 40}
		else:
			rules[key] = {"green": round(maximum * 0.8, 2), "yellow": round(maximum * 0.6, 2), "red": 0}
	return rules


def get_rules():
	"""Colour limits from HO Traffic Light Settings, falling back to the defaults."""
	rules = default_rules()
	rows = frappe.get_all(
		"HO Traffic Light Rule",
		filters={"parent": "HO Traffic Light Settings", "parenttype": "HO Traffic Light Settings"},
		fields=["column_key", "green_from", "yellow_from", "red_from"],
	)
	for row in rows:
		if row.column_key in rules:
			rules[row.column_key] = {
				"green": flt(row.green_from),
				"yellow": flt(row.yellow_from),
				"red": flt(row.red_from),
			}
	return rules


def rating_for(value, rule):
	if value is None:
		return None
	value = flt(value)
	if value >= rule["green"]:
		return "Green"
	if value >= rule["yellow"]:
		return "Yellow"
	if value >= rule["red"]:
		return "Red"
	return "Grey"


def ensure_defaults():
	"""First time only: fill the rule rows. Runs after install and migrate."""
	doc = frappe.get_single("HO Traffic Light Settings")
	existing = {r.column_key for r in doc.get("rules", [])}
	defaults = default_rules()
	changed = False
	for key, label, maximum in COLUMNS:
		if key not in existing:
			d = defaults[key]
			doc.append(
				"rules",
				{
					"column_key": key,
					"column_label": label,
					"maximum": maximum,
					"green_from": d["green"],
					"yellow_from": d["yellow"],
					"red_from": d["red"],
				},
			)
			changed = True
	if changed:
		doc.flags.ignore_permissions = True
		doc.save()
		frappe.db.commit()


class HOTrafficLightSettings(Document):
	def validate(self):
		for row in self.rules:
			green, yellow, red = flt(row.green_from), flt(row.yellow_from), flt(row.red_from)
			maximum = flt(row.maximum) or 100
			if not (0 <= red < yellow < green <= maximum):
				frappe.throw(
					_("Row {0} ({1}): limits must satisfy 0 <= Red < Yellow < Green <= {2}.").format(
						row.idx, row.column_label, maximum
					)
				)
