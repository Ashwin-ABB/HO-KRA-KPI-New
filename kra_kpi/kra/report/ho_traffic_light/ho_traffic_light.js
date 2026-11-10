const MONTH_NAMES = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
];
const CELL_COLOURS = {
	Green: ["#bbf7d0", "#166534"],
	Yellow: ["#fef08a", "#854d0e"],
	Red: ["#fecaca", "#991b1b"],
	Grey: ["#e5e7eb", "#374151"],
};

frappe.query_reports["HO Traffic Light"] = {
	filters: [
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: MONTH_NAMES.join("\n"),
			default: MONTH_NAMES[new Date().getMonth()],
			reqd: 1,
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Int",
			default: new Date().getFullYear(),
			reqd: 1,
		},
		{
			fieldname: "branch",
			label: __("Branch (optional)"),
			fieldtype: "Link",
			options: "Branch",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		const rating = data && data[column.fieldname + "_rating"];
		if (rating && CELL_COLOURS[rating]) {
			const c = CELL_COLOURS[rating];
			return '<div style="text-align:center;font-weight:600;padding:2px 4px;background:' + c[0] + ";color:" + c[1] + '">' + value + "</div>";
		}
		return value;
	},
};
