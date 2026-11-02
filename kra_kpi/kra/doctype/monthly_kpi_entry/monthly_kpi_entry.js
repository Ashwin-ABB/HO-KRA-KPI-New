frappe.ui.form.on("Monthly KPI Entry", {
	onload(frm) {
		// Pre-fill the logged-in user's own Employee record
		if (frm.is_new() && !frm.doc.employee) {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then((r) => {
				if (r.message && r.message.name) {
					frm.set_value("employee", r.message.name);
				}
			});
		}
	},

	employee(frm) {
		if (!frm.is_new() || !frm.doc.employee) {
			return;
		}
		frappe.call({
			method: "kra_kpi.kra.doctype.monthly_kpi_entry.monthly_kpi_entry.get_kpi_rows",
			args: { employee: frm.doc.employee },
			callback(r) {
				frm.clear_table("items");
				(r.message || []).forEach((row) => frm.add_child("items", row));
				frm.refresh_field("items");
				recalc(frm);
			},
		});
	},
});

frappe.ui.form.on("Monthly KPI Entry Item", {
	actual_value(frm) {
		recalc(frm);
	},
});

function recalc(frm) {
	let total = 0;
	let weight = 0;
	(frm.doc.items || []).forEach((r) => {
		const target = flt(r.target);
		const ratio = target > 0 ? Math.min(flt(r.actual_value) / target, 1) : 0;
		r.achievement = ratio * 100;
		r.score = flt(ratio * flt(r.weightage), 2);
		total += r.score;
		weight += flt(r.weightage);
	});
	frm.set_value("total_score", flt(total, 2));
	frm.set_value("total_weightage", weight);
	frm.refresh_field("items");
}
