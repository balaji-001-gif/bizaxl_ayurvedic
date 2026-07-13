// Follow-Up Calendar — view all pending follow-up visits grouped by date
// Accessible at /app/follow-up-calendar

frappe.pages["follow-up-calendar"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Follow-Up Calendar"),
		single_column: true,
	});

	// ── Toolbar: date range + refresh ──
	let today = frappe.datetime.get_today();
	let week_later = frappe.datetime.add_days(today, 30);

	page.add_field({
		fieldtype: "Date",
		fieldname: "from_date",
		label: __("From Date"),
		default: today,
		change: () => refresh_calendar(page),
	});

	page.add_field({
		fieldtype: "Date",
		fieldname: "to_date",
		label: __("To Date"),
		default: week_later,
		change: () => refresh_calendar(page),
	});

	page.add_inner_button(__("Refresh"), () => {
		refresh_calendar(page);
	}, "Action");

	page.add_inner_button(__("⬅ Past 7 Days"), () => {
		let to = frappe.datetime.get_today();
		let from = frappe.datetime.add_days(to, -7);
		page.fields_dict.from_date.set_value(from);
		page.fields_dict.to_date.set_value(to);
		refresh_calendar(page);
	}, "Quick Range");

	page.add_inner_button(__("➡ Next 30 Days"), () => {
		let from = frappe.datetime.get_today();
		let to = frappe.datetime.add_days(from, 30);
		page.fields_dict.from_date.set_value(from);
		page.fields_dict.to_date.set_value(to);
		refresh_calendar(page);
	}, "Quick Range");

	page.add_inner_button(__("All Pending"), () => {
		page.fields_dict.from_date.set_value("");
		page.fields_dict.to_date.set_value("");
		refresh_calendar(page);
	}, "Quick Range");

	// ── Main body container ──
	let $body = $(`<div class="fu-calendar-body">
		<div class="row" id="fuc-stats-bar"></div>
		<div id="fuc-filter-bar" style="margin:16px 0;"></div>
		<div id="fuc-visits-container"></div>
	</div>`).appendTo(page.main);
	page.$body = $body;

	// Initial load
	refresh_calendar(page);
};

function refresh_calendar(page) {
	let from_date = page.fields_dict.from_date.get_value() || "";
	let to_date = page.fields_dict.to_date.get_value() || "";
	let $body = page.$body;

	$body.find("#fuc-visits-container").html(`
		<div class="text-center" style="padding:40px;">
			<i class="fa fa-spinner fa-spin fa-2x text-muted"></i>
			<p class="text-muted" style="margin-top:10px;">Loading visits...</p>
		</div>
	`);

	frappe.call({
		method: "bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.treatment_follow_up.treatment_follow_up.get_pending_visits",
		args: { from_date, to_date },
		callback(r) {
			render_calendar(page, r.message);
		},
	});
}

function render_calendar(page, data) {
	if (!data) return;
	let $body = page.$body;
	let today = frappe.datetime.get_today();

	// ── Stats bar ──
	$body.find("#fuc-stats-bar").html(`
		<div class="col-sm-3">
			<div class="panel panel-default fu-stats-card" style="border-left:4px solid #17a2b8;">
				<div class="panel-body text-center">
					<h3 style="color:#0c5460;">${data.total_patients}</h3>
					<small class="text-muted">Patients</small>
				</div>
			</div>
		</div>
		<div class="col-sm-3">
			<div class="panel panel-default fu-stats-card" style="border-left:4px solid #ffc107;">
				<div class="panel-body text-center">
					<h3 style="color:#856404;">${data.total_pending}</h3>
					<small class="text-muted">Pending Visits</small>
				</div>
			</div>
		</div>
		<div class="col-sm-3">
			<div class="panel panel-default fu-stats-card" style="border-left:4px solid #dc3545;">
				<div class="panel-body text-center">
					<h3 style="color:#721c24;">${data.overdue}</h3>
					<small class="text-muted">Overdue</small>
				</div>
			</div>
		</div>
		<div class="col-sm-3">
			<div class="panel panel-default fu-stats-card" style="border-left:4px solid #28a745;">
				<div class="panel-body text-center">
					<h3 style="color:#155724;">${data.this_week}</h3>
					<small class="text-muted">This Week</small>
				</div>
			</div>
		</div>
	`);

	// ── Visits grouped by date ──
	let html = "";
	let visits = data.visits || [];

	if (visits.length === 0) {
		html = `<div class="fu-empty">
			<i class="fa fa-calendar-check-o"></i>
			<h4>All caught up!</h4>
			<p>No pending follow-up visits found in the selected date range.</p>
		</div>`;
		$body.find("#fuc-visits-container").html(html);
		return;
	}

	// Group by date
	let grouped = {};
	visits.forEach((v) => {
		let d = v.visit_date || "No Date";
		if (!grouped[d]) grouped[d] = [];
		grouped[d].push(v);
	});

	// Sort dates
	let sorted_dates = Object.keys(grouped).sort();

	sorted_dates.forEach((date) => {
		let items = grouped[date];
		let is_overdue = date < today;
		let is_today = date === today;
		let day_label = frappe.datetime.global_date_format(date);

		if (is_today) day_label = `📅 Today — ${day_label}`;
		else if (is_overdue) day_label = `⚠️ Overdue — ${day_label}`;

		let header_class = is_overdue ? "text-danger" : is_today ? "text-warning" : "";

		html += `<div class="fu-date-header ${header_class}">
			${day_label}
			<small>${items.length} visit${items.length > 1 ? "s" : ""}</small>
		</div>`;

		items.forEach((v) => {
			let card_class = "fu-visit-card";
			if (is_overdue) card_class += " fu-overdue";
			else if (is_today) card_class += " fu-today";
			else card_class += " fu-upcoming";

			let status_badge = v.status === "Pending"
				? `<span class="label label-warning">Pending</span>`
				: `<span class="label label-${v.status === "Completed" ? "success" : "danger"}">${frappe.utils.escape_html(v.status || "Pending")}</span>`;

			let fu_name = v.parent || "";
			let patient_name = frappe.utils.escape_html(v.patient_name || "Unknown");
			let fu_type = frappe.utils.escape_html(v.follow_up_type || "-");
			let fu_days = frappe.utils.escape_html(v.follow_up_days || "-");

			html += `<div class="${card_class}" onclick="frappe.set_route('Form', 'Treatment Follow-Up', '${fu_name}')">
				<div class="card-body">
					<div class="row">
						<div class="col-sm-8">
							<div class="patient-name">
								<i class="fa fa-user" style="margin-right:6px;color:#003960;"></i>
								${patient_name}
							</div>
							<div class="visit-meta">
								<span><i class="fa fa-tag"></i>${fu_type}</span>
								<span><i class="fa fa-clock-o"></i>Every ${fu_days} days</span>
								<span><i class="fa fa-file-text-o"></i>${fu_name}</span>
							</div>
						</div>
						<div class="col-sm-4 text-right">
							<div style="margin-bottom:6px;">${status_badge}</div>
							<small class="text-muted">
								${is_overdue
									? `<span class="text-danger"><i class="fa fa-exclamation-circle"></i> Overdue by ${frappe.datetime.get_diff(today, date)} day(s)</span>`
									: is_today
									? `<span style="color:#856404;"><i class="fa fa-bell"></i> Due Today</span>`
									: `<span><i class="fa fa-hourglass-end"></i> ${frappe.datetime.get_diff(date, today)} day(s) away</span>`
								}
							</small>
						</div>
					</div>
				</div>
			</div>`;
		});
	});

	$body.find("#fuc-visits-container").html(html);
}
