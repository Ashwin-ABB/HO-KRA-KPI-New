frappe.ui.form.on("Internal Feedback", {
	onload(frm) {
		if (frm.is_new() && !(frm.doc.items || []).length) {
			fill_rows(frm);
		}
	},

	load_employees(frm) {
		fill_rows(frm);
	},

	// changing the sheet date moves every row to that date
	date(frm) {
		(frm.doc.items || []).forEach((r) => frappe.model.set_value(r.doctype, r.name, "date", frm.doc.date));
	},
});

function fill_rows(frm) {
	if (frm.doc.docstatus !== 0) {
		return;
	}
	frappe.call({
		method: "kra_kpi.kra.doctype.internal_feedback.internal_feedback.get_employees",
		args: { branch: frm.doc.branch || null },
		freeze: true,
		callback(r) {
			const old = {};
			(frm.doc.items || []).forEach((row) => (old[row.employee] = row));
			frm.clear_table("items");
			(r.message || []).forEach((emp) => {
				const prev = old[emp.employee];
				frm.add_child("items", {
					employee: emp.employee,
					employee_name: emp.employee_name,
					internal_feedback: prev ? prev.internal_feedback : null,
					date: frm.doc.date,
				});
			});
			frm.refresh_field("items");
			if (!(r.message || []).length) {
				frappe.show_alert({
					message: __("No active employees found for the selected branch."),
					indicator: "orange",
				});
			}
		},
	});
}
