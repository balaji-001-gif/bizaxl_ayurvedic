// Token Dashboard — live OPD token queue for the front-desk receptionist
// Auto-refreshes every 15 seconds so the receptionist sees new tokens in real time.

frappe.pages["token-dashboard"].on_page_load = function (wrapper) {
	frappe.call({
		method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.get_dashboard_stats",
		callback(r) {
			wrapper.token_stats = r.message || { total: 0, waiting: 0, in_consultation: 0, completed: 0, called: 0 };
		},
	});

	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Token Dashboard"),
		single_column: true,
	});

	// ── Toolbar: date field + refresh buttons ──
	page.add_field({
		fieldtype: "Date",
		fieldname: "date",
		label: "Date",
		default: frappe.datetime.get_today(),
		change: () => refresh_dashboard(page, page.fields_dict.date.get_value()),
	});

	page.add_inner_button(__("Refresh"), () => {
		refresh_dashboard(page, page.fields_dict.date.get_value());
	}, "Action");

	page.add_inner_button(__("↻ Auto"), () => {
		page.__auto_refresh = !page.__auto_refresh;
		if (page.__auto_refresh) {
			let date_val = page.fields_dict.date.get_value();
			page.__auto_refresh_interval = setInterval(() => {
				refresh_dashboard(page, page.fields_dict.date.get_value(), true);
			}, 15000);
			frappe.show_alert({ message: __("Auto-refresh ON (15s)"), indicator: "green" });
		} else {
			clearInterval(page.__auto_refresh_interval);
			frappe.show_alert({ message: __("Auto-refresh OFF"), indicator: "red" });
		}
	}, "Action");

	// ── Main body container ──
	let $body = $(`<div class="token-dashboard-body">
		<div class="row" id="td-stats-bar"></div>
		<div id="td-queue-container"></div>
	</div>`).appendTo(page.main);
	page.$body = $body;

	// Initial load
	refresh_dashboard(page, page.fields_dict.date.get_value());
};

function refresh_dashboard(page, date, silent) {
	if (!silent) frappe.show_alert({ message: __("Refreshing dashboard…"), indicator: "blue" });

	frappe.call({
		method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.get_today_queue",
		args: { date },
		callback(r) {
			render_dashboard(page, r.message);
		},
	});
}

function render_dashboard(page, data) {
	if (!data) return;

	let $body = page.$body;

	// ── Stats bar ──
	let total = data.total_tokens || 0;
	let all_tokens = [];
	(data.practitioners || []).forEach((p) => {
		all_tokens = all_tokens.concat(p.tokens);
	});
	let waiting = all_tokens.filter((t) => (t.status || "Waiting") === "Waiting").length;
	let in_consult = all_tokens.filter((t) => (t.status || "") === "In Consultation").length;
	let completed = all_tokens.filter((t) => (t.status || "") === "Completed").length;
	let called = all_tokens.filter((t) => (t.status || "") === "Called").length;

	$body.find("#td-stats-bar").html(`
		<div class="col-sm-3">
			<div class="panel panel-default" style="border-left:4px solid #6c757d;">
				<div class="panel-body text-center">
					<h3>${total}</h3>
					<small class="text-muted">Total Tokens</small>
				</div>
			</div>
		</div>
		<div class="col-sm-3">
			<div class="panel panel-default" style="border-left:4px solid #ffc107;">
				<div class="panel-body text-center">
					<h3 style="color:#856404;">${waiting}</h3>
					<small class="text-muted">Waiting</small>
				</div>
			</div>
		</div>
		<div class="col-sm-3">
			<div class="panel panel-default" style="border-left:4px solid #17a2b8;">
				<div class="panel-body text-center">
					<h3 style="color:#0c5460;">${in_consult}</h3>
					<small class="text-muted">In Consultation</small>
				</div>
			</div>
		</div>
		<div class="col-sm-3">
			<div class="panel panel-default" style="border-left:4px solid #28a745;">
				<div class="panel-body text-center">
					<h3 style="color:#155724;">${completed}</h3>
					<small class="text-muted">Completed</small>
				</div>
			</div>
		</div>
	`);

	// ── Queue tables per practitioner ──
	let html = "";
	(data.practitioners || []).forEach((p) => {
		html += `<div class="panel panel-default" style="margin-top:20px;">
			<div class="panel-heading" style="display:flex;justify-content:space-between;align-items:center;">
				<h4 style="margin:0;">
					<i class="fa fa-user-md" style="margin-right:8px;"></i>
					${frappe.utils.escape_html(p.practitioner_name || p.practitioner)}
					<span class="badge" style="margin-left:10px;">${p.tokens.length}</span>
				</h4>
				<div>
					<span class="label label-warning" style="margin-right:6px;">Waiting: ${p.stats.waiting}</span>
					<span class="label label-info" style="margin-right:6px;">In: ${p.stats.in_consultation}</span>
					<span class="label label-success">Done: ${p.stats.completed}</span>
				</div>
			</div>
			<div class="panel-body" style="padding:0;">
				<table class="table table-bordered table-hover" style="margin:0;">
					<thead>
						<tr>
							<th style="width:70px;">Token</th>
							<th>Patient</th>
							<th style="width:140px;">Mobile</th>
							<th style="width:130px;">Status</th>
							<th style="width:200px;">Actions</th>
						</tr>
					</thead>
					<tbody>`;

		p.tokens.forEach((t) => {
			let status = t.status || "Waiting";
			let status_color = { Waiting: "warning", "In Consultation": "info", Completed: "success", Called: "default" };
			let label = status_color[status] || "default";
			let row_class = status === "Waiting" && p.tokens.indexOf(t) === 0 ? "ba-current" : "";

			html += `<tr class="${row_class}" data-token="${frappe.utils.escape_html(t.name)}">
				<td style="font-size:18px;font-weight:700;text-align:center;">${t.last_token}</td>
				<td><strong>${frappe.utils.escape_html(t.patient_name || "-")}</strong></td>
				<td>${frappe.utils.escape_html(t.patient_mobile || "-")}</td>
				<td><span class="label label-${label}" style="font-size:12px;">${status}</span></td>
				<td>
					<div class="btn-group btn-group-xs">
						<button class="btn btn-default btn-call" data-token="${frappe.utils.escape_html(t.name)}"
							${status !== "Waiting" ? "disabled" : ""}>
							<i class="fa fa-phone"></i> Call
						</button>
						<button class="btn btn-info btn-consult" data-token="${frappe.utils.escape_html(t.name)}"
							${status !== "Waiting" && status !== "Called" ? "disabled" : ""}>
							<i class="fa fa-stethoscope"></i> Consult
						</button>
						<button class="btn btn-success btn-done" data-token="${frappe.utils.escape_html(t.name)}"
							${status === "Completed" ? "disabled" : ""}>
							<i class="fa fa-check"></i> Done
						</button>
					</div>
				</td>
			</tr>`;
		});

		html += `</tbody></table></div></div>`;
	});

	if (!data.practitioners || data.practitioners.length === 0) {
		html = `<div class="alert alert-info" style="margin-top:20px;">
			<i class="fa fa-info-circle"></i>
			No tokens found for <strong>${frappe.utils.escape_html(data.date)}</strong>.
		</div>`;
	}

	$body.find("#td-queue-container").html(html);

	// ── Bind action buttons ──
	$body.find(".btn-call").on("click", function () {
		let token = $(this).data("token");
		$(this).prop("disabled", true).html('<i class="fa fa-spinner fa-spin"></i>');
		frappe.call({
			method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.call_patient",
			args: { token_name: token },
			callback(r) {
				if (r.message) {
					let mobile = r.message.patient_mobile;
					let msg = `Called: ${frappe.utils.escape_html(r.message.patient_name)}`;
					if (mobile) msg += ` — <a href="tel:${mobile}" style="font-weight:700;">📞 ${mobile}</a>`;
					frappe.show_alert({ message: msg, indicator: "green" });
					refresh_dashboard(page, data.date, true);
				}
			},
		});
	});

	$body.find(".btn-consult").on("click", function () {
		let token = $(this).data("token");
		frappe.call({
			method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.update_status",
			args: { token_name: token, status: "In Consultation" },
			callback() {
				frappe.show_alert({ message: __("Patient moved to Consultation"), indicator: "blue" });
				refresh_dashboard(page, data.date, true);
			},
		});
	});

	$body.find(".btn-done").on("click", function () {
		let token = $(this).data("token");
		frappe.call({
			method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.token_counter.token_counter.update_status",
			args: { token_name: token, status: "Completed" },
			callback() {
				frappe.show_alert({ message: __("Token completed!"), indicator: "green" });
				refresh_dashboard(page, data.date, true);
			},
		});
	});
}
