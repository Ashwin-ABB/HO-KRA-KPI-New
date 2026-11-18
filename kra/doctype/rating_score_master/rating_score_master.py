import frappe
from frappe.model.document import Document

from kra_kpi.kra.rating_utils import RATING_OPTIONS


def ensure_defaults():
	"""Create the ten ratings (score = rating number) if missing. Runs after install and migrate."""
	for label in RATING_OPTIONS:
		if not frappe.db.exists("Rating Score Master", label):
			number = int(label.split(" - ")[0])
			frappe.get_doc(
				{"doctype": "Rating Score Master", "feedback_rating": label, "rating_no": number, "score": number}
			).insert(ignore_permissions=True)
	frappe.db.commit()


class RatingScoreMaster(Document):
	pass
