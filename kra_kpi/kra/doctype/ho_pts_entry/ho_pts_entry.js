const STATUS = ["", "Y", "N", "L", "H", "NA"];
const COUNTED = ["Y", "H", "NA"];
const STATUS_STYLE = {
	Y: ["#bbf7d0", "#166534"],
	N: ["#fecaca", "#991b1b"],
	L: ["#fef08a", "#854d0e"],
	H: ["#bfdbfe", "#1e40af"],
	NA: ["#bfdbfe", "#1e40af"],
};
const SECTIONS = [
	{ key: "daily", table: "daily_entries", child: "HO PTS Daily Entry", prefix: "d", title: "DAILY", label: "Daily Task" },
	{ key: "weekly", table: "weekly_entries", child: "HO PTS Weekly Entry", prefix: "w", title: "WEEKLY", label: "Weekly Task" },
	{ key: "monthly", table: "monthly_entries", child: "HO PTS Monthly Entry", prefix: "", title: "MONTHLY", label: "Monthly Task" },
];
const HR_ROLES = ["HR Manager", "System Manager"];

frappe.ui.form.on("HO PTS Entry", {
	onload(frm) {
		// a normal user always works on their own record
		if (!HR_ROLES.some((r) => frappe.user.has_role(r))) {
			frm.set_df_property("employee", "read_only", frm.is_new() ? 0 : 1);
		}
		if (frm.is_new() && !frm.doc.employee) {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then((r) => {
				if (r.message && r.message.name) {
					frm.set_value("employee", r.message.name);
				}
			});
		}
	},

	refresh(frm) {
		set_days(frm);
		render_sheet(frm);
	},

	employee(frm) {
		load_checklist(frm);
	},

	posting_date(frm) {
		set_days(frm);
		render_sheet(frm);
	},
});

function set_days(frm) {
	const d = frm.doc.posting_date ? frappe.datetime.str_to_obj(frm.doc.posting_date) : new Date();
	frm.doc.days_in_month = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
}

function field_names(frm, sec) {
	const days = frm.doc.days_in_month || 31;
	const n = sec.key === "daily" ? days : sec.key === "weekly" ? Math.ceil(days / 7) : 0;
	if (sec.key === "monthly") {
		return ["status"];
	}
	const out = [];
	for (let i = 1; i <= n; i++) {
		out.push(sec.prefix + i);
	}
	return out;
}

function load_checklist(frm) {
	if (!frm.doc.employee || !frm.is_new()) {
		return;
	}
	frappe.call({
		method: "kra_kpi.kra.doctype.ho_pts_entry.ho_pts_entry.get_checklist",
		args: { employee: frm.doc.employee },
		freeze: true,
		callback(r) {
			const m = r.message;
			if (!m) {
				return;
			}
			SECTIONS.forEach((sec) => {
				frm.clear_table(sec.table);
				(m[sec.key] || []).forEach((t) => frm.add_child(sec.table, t));
				frm.refresh_field(sec.table);
			});
			frm.set_value({
				daily_weightage: m.weightage.daily,
				weekly_weightage: m.weightage.weekly,
				monthly_weightage: m.weightage.monthly,
			});
			render_sheet(frm);
		},
	});
}

function paint($el, value) {
	const c = STATUS_STYLE[value];
	$el.css({ background: c ? c[0] : "", color: c ? c[1] : "" });
}

function select_html(fn, value, editable, narrow) {
	const c = STATUS_STYLE[value];
	const style = "font-weight:600;" + (narrow ? "min-width:54px;padding:2px;" : "") + (c ? "background:" + c[0] + ";color:" + c[1] + ";" : "");
	let h = '<select class="form-control input-sm pts-sel" style="' + style + '" data-field="' + fn + '"' + (editable ? "" : " disabled") + ">";
	STATUS.forEach((s) => {
		h += '<option value="' + s + '"' + (s === (value || "") ? " selected" : "") + ">" + s + "</option>";
	});
	return h + "</select>";
}

function section_html(frm, sec, editable) {
	const esc = frappe.utils.escape_html;
	const fields = field_names(frm, sec);
	const rows = frm.doc[sec.table] || [];
	let h = '<div style="background:#c94f70;color:#fff;font-weight:700;padding:6px 10px;margin-top:14px">' + sec.title + "</div>";
	h += '<div style="overflow-x:auto"><table class="table table-bordered" style="min-width:900px;font-size:12px"><thead><tr>';
	h += '<th style="background:#ffc000">Main Task</th><th style="background:#ffc000">Expected Outcome</th>';
	h += '<th style="background:#ffc000">Time Line</th><th style="background:#ffc000">Data</th>';
	fields.forEach((fn, i) => {
		const head = sec.key === "monthly" ? "Status" : sec.key === "weekly" ? "Week " + (i + 1) : i + 1;
		h += '<th style="background:#ffc000;text-align:center">' + head + "</th>";
	});
	h += "</tr></thead><tbody>";
	if (sec.key === "daily" && editable && rows.length) {
		h += '<tr><td colspan="4" style="text-align:right"><i>Set the whole day</i></td>';
		fields.forEach((fn) => {
			h += '<td><select class="form-control input-sm pts-all" style="min-width:54px;padding:2px" data-sec="daily" data-field="' + fn + '">';
			STATUS.forEach((s) => (h += '<option value="' + s + '">' + s + "</option>"));
			h += "</select></td>";
		});
		h += "</tr>";
	}
	rows.forEach((row) => {
		h += '<tr data-sec="' + sec.key + '" data-name="' + row.name + '">';
		h += "<td>" + esc(row.main_task || "") + "</td><td>" + esc(row.expected_outcome || "") + "</td>";
		h += "<td>" + esc(row.time_line || "") + "</td><td>" + (row.data == null ? "" : row.data) + "</td>";
		fields.forEach((fn) => {
			h += "<td>" + select_html(fn, row[fn], editable, sec.key === "daily") + "</td>";
		});
		h += "</tr>";
	});
	return h + "</tbody></table></div>";
}

function render_sheet(frm) {
	const $w = frm.fields_dict.entry_sheet.$wrapper;
	const esc = frappe.utils.escape_html;
	const editable = frm.is_new() || !!(frm.perm && frm.perm[0] && frm.perm[0].write);
	let html = "";
	if (frm.doc.employee_name) {
		html += '<div style="background:#22c5d8;font-weight:700;font-size:16px;text-align:center;padding:8px">' +
			esc(frm.doc.employee_name) + " " + esc(frm.doc.designation || "") + "</div>";
	}
	SECTIONS.forEach((sec) => (html += section_html(frm, sec, editable)));
	html += '<div class="pts-summary"></div>';
	$w.html(html);

	$w.off("change").on("change", ".pts-sel", function () {
		const $s = $(this);
		const $tr = $s.closest("tr");
		const sec = SECTIONS.find((x) => x.key === $tr.data("sec"));
		paint($s, $s.val());
		frappe.model.set_value(sec.child, $tr.data("name"), $s.data("field"), $s.val());
		update_summary(frm);
	});
	$w.on("change", ".pts-all", function () {
		const $a = $(this);
		const fn = $a.data("field");
		const v = $a.val();
		if (v === "") {
			return;
		}
		$w.find('tr[data-sec="daily"][data-name]').each(function () {
			const $s = $(this).find('select[data-field="' + fn + '"]');
			$s.val(v);
			paint($s, v);
			frappe.model.set_value("HO PTS Daily Entry", $(this).data("name"), fn, v);
		});
		$a.val("");
		update_summary(frm);
	});
	update_summary(frm);
}

function update_summary(frm) {
	const $w = frm.fields_dict.entry_sheet.$wrapper;
	let totalWeight = 0;
	let totalScore = 0;
	let body = "";
	SECTIONS.forEach((sec) => {
		const fields = field_names(frm, sec);
		const $rows = $w.find('tr[data-sec="' + sec.key + '"][data-name]');
		let achieved = 0;
		$rows.each(function () {
			fields.forEach((fn) => {
				if (COUNTED.indexOf($(this).find('select[data-field="' + fn + '"]').val()) >= 0) {
					achieved += 1;
				}
			});
		});
		const target = $rows.length * fields.length;
		const weight = flt(frm.doc[sec.key + "_weightage"]);
		const score = target ? Math.round((achieved / target) * weight) : 0;
		totalWeight += weight;
		totalScore += score;
		body += "<tr><td>" + sec.label + "</td><td style='text-align:center'>" + weight + "</td><td style='text-align:center'>" +
			target + "</td><td style='text-align:center'>" + achieved + "</td><td style='text-align:center'><b>" + score + "</b></td></tr>";
	});
	const html =
		'<div style="margin-top:16px;overflow-x:auto"><table class="table table-bordered" style="max-width:760px">' +
		'<thead><tr style="background:#ffc000"><th>TASK</th><th>WEIGHTAGE</th><th>TARGET</th><th>ACHIEVED</th><th>SCORE</th></tr></thead><tbody>' +
		body +
		'<tr style="background:#22c5d8"><td><b>Total</b></td><td style="text-align:center"><b>' + totalWeight +
		'</b></td><td></td><td></td><td style="text-align:center"><b>' + totalScore + "</b></td></tr></tbody></table>" +
		'<div class="text-muted" style="font-size:12px">Y - Task Completed. H (Holiday) and NA (On duty) - task score counted. ' +
		"N (No) and L (Leave) - task not completed. Score = achieved / target x weightage.</div></div>";
	$w.find(".pts-summary").html(html);
}
