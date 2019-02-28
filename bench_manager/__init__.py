# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

import frappe

@frappe.whitelist()
def restart():
	# import sys, imp, importlib

	# if module in sys.modules:
	# 	del sys.modules[module]

	# frappe.clear_cache()

	# _module = importlib.import_module(module)

	# imp.reload(_module)

	import subprocess

	cmd = (
		"sudo",
		"supervisorctl",
		"restart",
		"frappe-bench-web:frappe-bench-frappe-web"
	)

	out = subprocess.check_output(cmd)

	# frappe.errprint(out)
	return out
