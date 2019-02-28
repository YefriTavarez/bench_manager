// frappe.model.get_server_module_name(cur_frm.doctype)

frappe.ui.toolbar.clear_cache = function() {
	frappe.assets.clear_local_storage();

	if (frappe.session.user != "Administrator") {
		return ;
	}

	const callback = response => {
		const { freeze_count } = frappe.dom;

		for (count = 1; count <= flt(freeze_count); count ++) {
			frappe.dom.unfreeze();
		}

		console.log(response.message);

		setTimeout(function() {
			frappe.ui.toolbar._clear_cache();
		}, 1500);

	};

	frappe.call({
		method: "bench_manager.restart",
		args: { },
		callback: callback,
	});


	return false;
};

frappe.ui.toolbar._clear_cache = function() {
	frappe.call({
		method: 'frappe.sessions.clear',
		args: {
			// empty
		},
		callback: function(r, rt) {
			if(!r.exc) {
				frappe.show_alert(r.message);
				location.reload(true);
			}
		}
	});
};
