const MONTH_NAMES = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
];
let MANAGERS = [];

frappe.ui.form.on("Employee Rating Manager", {
	setup(frm) {
		try {
			// Manager: people others report to. Employee: only those who report to the chosen manager.
			frm.set_query("manager", () => ({
				filters: { name: ["in", MANAGERS.length ? MANAGERS : ["-"]], status: "Active" },
			}));
			frm.set_query("employee", () => ({
				filters: { reports_to: frm.doc.manager || "-", status: "Active" },
			}));
		} catch (e) {
			console.error(e);
		}
		frappe.xcall("kra_kpi.kra.rating_utils.get_managers")
			.then((m) => (MANAGERS = m || []))
			.catch(() => {});
	},

	onload(frm) {
		// the logged-in employee, and their own manager, are the defaults
		if (frm.is_new() && !frm.doc.employee) {
			frappe.db
				.get_value("Employee", { user_id: frappe.session.user, status: "Active" }, ["name", "reports_to"])
				.then((r) => {
					if (r.message && r.message.name) {
						frm.set_value("employee", r.message.name);
						if (r.message.reports_to) {
							frm.set_value("manager", r.message.reports_to);
						}
					}
				});
		}
		set_month(frm);
	},

	rating_month(frm) {
		set_month(frm);
		if (frm.doc.rating_month) {
			const d = frappe.datetime.str_to_obj(frm.doc.rating_month);
			const last = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
			if (d.getDate() !== last) {
				frappe.show_alert({ message: __("Please select the last date of the rating month."), indicator: "red" });
			}
		}
	},

	manager(frm) {
		if (!frm.doc.employee || !frm.doc.manager) {
			return;
		}
		frappe.db.get_value("Employee", frm.doc.employee, "reports_to").then((r) => {
			if (r.message && r.message.reports_to !== frm.doc.manager) {
				frm.set_value("employee", "");
			}
		});
	},
});

function set_month(frm) {
	if (!frm.doc.rating_month) {
		return;
	}
	const d = frappe.datetime.str_to_obj(frm.doc.rating_month);
	frm.doc.rating_month_name = MONTH_NAMES[d.getMonth()];
	frm.doc.rating_year = d.getFullYear();
	frm.refresh_field("rating_month_name");
	frm.refresh_field("rating_year");
}
