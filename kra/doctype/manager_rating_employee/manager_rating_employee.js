const MONTH_NAMES = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
];
let MANAGERS = [];

frappe.ui.form.on("Manager Rating Employee", {
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
		// the logged-in manager is the default
		if (frm.is_new() && !frm.doc.manager) {
			frappe.db.get_value("Employee", { user_id: frappe.session.user, status: "Active" }, "name").then((r) => {
				if (r.message && r.message.name) {
					frm.set_value("manager", r.message.name);
				}
			});
		}
		set_month_rated(frm);
	},

	date(frm) {
		set_month_rated(frm);
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

function set_month_rated(frm) {
	if (!frm.doc.date) {
		return;
	}
	const d = frappe.datetime.str_to_obj(frm.doc.date);
	const p = new Date(d.getFullYear(), d.getMonth() - 1, 1);
	frm.doc.rated_month = MONTH_NAMES[p.getMonth()];
	frm.doc.rated_year = p.getFullYear();
	frm.refresh_field("rated_month");
	frm.refresh_field("rated_year");
}
