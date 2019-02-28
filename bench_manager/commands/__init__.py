# -*- coding: utf-8 -*-
# Copyright (c) 2019, Yefri Tavarez and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import sys
import click
import cProfile
import StringIO
import pstats
import frappe
import frappe.utils
from functools import wraps

from datetime import datetime

from frappe.commands import pass_context, get_site

from frappe.exceptions import DuplicateEntryError

click.disable_unicode_literals_warning = True

pypatch_boilerplate = """# -*- coding: utf-8 -*-
# Copyright (c) {year}, {app_publisher} and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe

def execute():
	pass
"""

@click.command('create-patch')
@click.option('--app-name', required=True, help="Name of the app where the patch is going to be placed")
@click.option('--patch-name', required=True, help="Name of the patch `my_patch_name`")
@click.option('--patch-version', required=False, default="v1", help="Version of the patch `v1`")
def create_patch(app_name, patch_name, patch_version):
	"""Creates a boilerplate for a patch ready to run"""

	# users can change the installation path, the operating
	# user or even have multiple benchs running in the same instance.

	# by default it is located at `/home/frappe/frappe-bench`

	# so, lets make sure we get the right path

	# get the base `frappe-bench` path where the system
	# is installed

	_base_path = frappe.utils.get_bench_path()

	# scrub to remove any trailing spaces or if it is a more complex name
	# by more than one word.
	_app_name = frappe.scrub(app_name)

	# the same things applies to the patch_name
	# we just want to make sure and do anything we can to guess
	# what the user wants and do it right
	_patch_name = frappe.scrub(patch_name)

	# lets bring all the frappe apps installed on this instance
	# and see if the user has a existing one
	_all_apps = open("{0}/sites/apps.txt" \
		.format(_base_path), "r") \
		.read()

	# if the app is not in this file is very likely:
		# -- that it does not exists
		# -- it is not a frappe app
		# -- or maybe is not properly installed

	# anyhow, lets exit the command and let the user know
	if _app_name not in _all_apps:
		print ("App {app} does not exist" \
			.format(app=_app_name))

		sys_exit()

	# the patch_folder is the folder where the python module
	# is going to be placed.

	# have in mind that the application may manage more than one version
	# this is very important to keep the patches organized
	_patches_folder = "apps/{app}/{app}/patches/{patch_version}" \
		.format(app=_app_name, patch_version=patch_version)

	# so, in case the it does not exist, lets create it
	frappe.create_folder("{}/{}" \
		.format(_base_path, _patches_folder), with_init=True)

	# this is the python module that is going to be executed
	# and do the fixes that we need
	_full_pypath = "{base_path}/{patch_folder}/{patch_name}.py" \
		.format(base_path=_base_path, patch_folder=_patches_folder,
			patch_name=_patch_name)

	# import here to show where it is going to be used
	from os.path import exists

	# if the python module exists in the folder
	# we'd better not continue as we might clear the file
	# while creating it. in the frappe framework a patch should (or must)
	# have a unique path and this includes the filename
	if exists(_full_pypath):
		print("Pacth {0} already exists" \
			.format(patch_name))

		sys_exit()

	# if we have make it to here, that means the
	# python module does not exist and it is safe to create it
	# and put some boilerplate content to it
	frappe.utils.touch_file(_full_pypath)

	# we fetch the app_publisher as we are going to be using it in the
	# boilerplate template as well as the year where it is being created

	app_publisher = frappe.get_hooks("app_publisher",
		app_name=_app_name)

	# we use datetime as we don't want to bother frappe
	# initializing an existing site. we believe this way should
	# be a lot of faster and that's what we want

	now_datetime = datetime.now()
	year = now_datetime.year

	# lets dump the new just created python file
	# with the boilerplate with all the fields filled

	with open(_full_pypath, "w") as patch_py:
		patch_py.write(pypatch_boilerplate \
			.format(app_publisher=app_publisher[0] if app_publisher \
				else "Frappe Tecnologies, Inc", year=year))

	# and as soon as we finish creating the module lets
	# update the patches.txt file so that this patch can be
	# executed in the next bench migration

	_patches_txt = "{base_path}/apps/{app}/{app}/patches.txt" \
		.format(base_path=_base_path, app=_app_name)

	# this is just to ensure that the file exist and
	# we don't get any errros because we have already
	# written to the other files

	frappe.utils.touch_file(_patches_txt)

	# put the file content in a temp variable
	# so that we can sanitize the data in the file

	content = []
	with open(_patches_txt, "r") as txt:
		content = txt.readlines()

	# lets sanitize the data that is already in the file
	# we don't want any surprises

	with open(_patches_txt, "w") as txt:

		# add the new patch here so that it can be added
		# with the rest of the patches that were previously in
		# the file before the truncation

		content.append("{app_name}.patches.{patch_version}.{patch_name}" \
			.format(app_name=_app_name, patch_name=_patch_name,
				patch_version=patch_version))

		# filter the lines in the file if they have a value
		# ignore them otherwise. also, lets remove any leading or
		# trailing space in the line

		_lines = set([
			line \
				.replace("\n", "") \
				.replace("\r\n", "") \
				.strip() for line in content \
			if str(line)
		])

		# finally lets reassemble the file as it supposedly
		# was before we opened it. at the end of the day, we
		# just want to ensure the whole process of updating it

		txt.write("\n".join(list(_lines)))

		# add an empty line to meet the standards
		txt.write("\n")

@click.command('create-module')
@click.option('--app-name', required=True, help="Name of the app where the module is going to be placed")
@click.option('--module-name', required=True, help="Name of the module `my_module`")
@click.option('--site-name', required=False, default="all", help="Name of the site where the module is going to be placed")
def create_module(app_name, module_name, site_name):
	"""Creates an empty frappe module ready to use"""

	# users can change the installation path, the operating
	# user or even have multiple benchs running in the same instance.

	# by default it is located at `/home/frappe/frappe-bench`

	# so, lets make sure we get the right path

	# get the base `frappe-bench` path where the system
	# is installed

	_base_path = frappe.utils.get_bench_path()

	# scrub to remove any trailing spaces or if it is a more complex name
	# by more than one word

	_app_name = frappe.scrub(app_name)

	# the same things applies to the module_name
	# we just want to make sure and do anything we can to guess
	# what the user wants and do it right

	_module_name = frappe.scrub(module_name)

	# the same things applies to the site_name
	# we just want to make sure and do anything we can to guess
	# what the user wants and do it right

	_site_name = frappe.scrub(site_name)

	# lets bring all the frappe apps installed on this instance
	# and see if the user has a existing one

	_all_apps = open("{0}/sites/apps.txt" \
		.format(_base_path), "r") \
		.read()

	# if the app is not in this file is very likely:
		# -- that it does not exists
		# -- it is not a frappe app
		# -- or maybe is not properly installed

	# anyhow, lets exit the command and let the user know

	if _app_name not in _all_apps:
		print ("App {app} does not exist" \
			.format(app=_app_name))

		sys_exit()

	_sites_path = "/".join([_base_path, "sites"])

	# lets bring all the frappe sites setup on this instance

	_all_sites = frappe.utils \
		.get_sites(sites_path=_sites_path)

	# if the site does not exist in this instance
	# exit and let the user know

	if _site_name not in _all_sites \
		and _site_name != "all":
		print ("Site {site} does not exist" \
			.format(site=_site_name))
		sys_exit()

	# folder to be created and the folder that will hold
	# all the ptyhon modules and namespaces

	_module_folder = "apps/{app}/{app}/{module_name}" \
		.format(app=_app_name, module_name=_module_name)

	# so, in case the it does not exist, lets create it

	frappe.create_folder("{}/{}" \
		.format(_base_path, _module_folder), with_init=True)

	if _site_name != "all":
		_all_sites = [_site_name]

	for site in _all_sites:

		# initialize frappe for the current site.
		# reset thread locals `frappe.local`

		frappe.init(site=site, sites_path=_sites_path)

		# connect to site database instance
		# frappe.connect will try to init again
		# this is fine as we don't any other solution by now

		frappe.connect(site=site)

		# we now can import the frappe.db object

		from frappe import db

		# skip if the module already exists in the db. please
		# notice the difference in _module_name and module_name

		if not db.exists("Module Def", {
			"module_name": module_name,
		}) and not db.exists("Module Def", {
			"module_name": _module_name,
		}):

			# the module does not exist in the
			# database, lets create it

			frappe.get_doc({
				"app_name": _app_name,
				"doctype": "Module Def",
				"module_name": module_name,
			}).save(ignore_permissions=True)

		# commit current transaction. calls sql `commit`
		# lets make sure that we save the changes
		# to the database

		frappe.db.commit()

		# lets close the connection and release werkzeug local

		frappe.destroy()

	# and as soon as we finish creating the module lets
	# update the modules.txt file so that this patch can be
	# executed in the next bench migration

	_modules_txt = "{base_path}/apps/{app}/{app}/modules.txt" \
		.format(base_path=_base_path, app=_app_name)

	# this is just to ensure that the file exist and
	# we don't get any errros because we have already
	# written to the other files

	frappe.utils.touch_file(_modules_txt)

	# put the file content in a temp variable
	# so that we can sanitize the data in the file

	content = []
	with open(_modules_txt, "r") as txt:
		content = txt.readlines()

	# lets sanitize the data that is already in the file
	# we don't want any surprises

	with open(_modules_txt, "w") as txt:

		# add the new patch here so that it can be added
		# with the rest of the modules that were previously in
		# the file before the truncation

		content.append(module_name)

		# filter the lines in the file if they have a value
		# ignore them otherwise. also, lets remove any leading or
		# trailing space in the line

		_lines = set([
			line \
				.replace("\n", "") \
				.replace("\r\n", "") \
				.strip() for line in content \
			if str(line)
		])

		# finally lets reassemble the file as it supposedly
		# was before we opened it. at the end of the day, we
		# just want to ensure the whole process of updating it

		txt.write("\n".join(list(_lines)))

		# add an empty line to meet the standards
		txt.write("\n")

@click.command("create-report")
@click.option("--site-name", default="all", help="Site where the record is going to be saved")
@click.option("--module-name", required=True, help="Module where the report is going to be placed")
@click.option("--reference-doctype", required=True, help="Doctype where the Report is going to show from")
@click.option("--report-name", required=True, help="Name of the Report ex. `Sales Register`")
# @click.option("--report-type", help="Report Type", required=True, type=click.Choice(["Script Report"]))
def create_report(site_name, module_name, reference_doctype, report_name):
	# users can change the installation path, the operating
	# user or even have multiple benchs running in the same instance.

	# by default it is located at `/home/frappe/frappe-bench`

	# so, lets make sure we get the right path

	# get the base `frappe-bench` path where the system
	# is installed

	_base_path = frappe.utils.get_bench_path()

	# scrub to remove any trailing spaces or if it is a more complex name
	# by more than one word

	# we just want to make sure and do anything we can to guess
	# what the user wants and do it right

	_module_name = frappe.scrub(module_name)

	# the same things applies to the site_name
	# we just want to make sure and do anything we can to guess
	# what the user wants and do it right

	_site_name = frappe.scrub(site_name)

	_sites_path = "/".join([_base_path, "sites"])

	# lets bring all the frappe sites setup on this instance

	_all_sites = frappe.utils \
		.get_sites(sites_path=_sites_path)

	# if the site does not exist in this instance
	# exit and let the user know

	if _site_name not in _all_sites \
		and _site_name != "all":
		print ("Site {site} does not exist" \
			.format(site=_site_name))
		sys_exit()

	if _site_name != "all":
		_all_sites = [_site_name]

	module_exists = False

	for site in _all_sites:

		# initialize frappe for the current site.
		# reset thread locals `frappe.local`

		frappe.init(site=site, sites_path=_sites_path)

		# connect to site database instance
		# frappe.connect will try to init again
		# this is fine as we don't any other solution by now

		frappe.connect(site=site)

		# we now can import the frappe.db object

		from frappe import db

		# if the report exists in at least one site
		# that could mean we are posibly overriding the content
		# of the controllers

		# so, lets make sure that this never happens
		# if we prove it to be true, we don't want to write to the files
		# this is why we use two loops

		if db.exists("Report", {
			"report_name": report_name,
		}):
			# mark the flag as true

			module_exists = True

			# and skip this round

			break

		frappe.destroy()

	for site in _all_sites:

		# initialize frappe for the current site.
		# reset thread locals `frappe.local`

		frappe.init(site=site, sites_path=_sites_path)

		# connect to site database instance
		# frappe.connect will try to init again
		# this is fine as we don't any other solution by now

		frappe.connect(site=site)

		# we now can import the frappe.db object

		from frappe import db

		# skip if the module already exists in the db. please
		# notice the difference in _module_name and module_name

		report = frappe.get_doc({
			"__islocal": 1,
			"add_total_row": 0,
			"apply_user_permissions": 1,
			"disabled": 0,
			"docstatus": 0,
			"doctype": "Report",
			"is_standard": "Yes",
			"module": module_name,
			"owner": "Administrator",
			"query": "",
			"add_total_row": True,
			"ref_doctype": reference_doctype,
			"report_name": report_name,
			"report_type": "Script Report"
		})

		# try to insert the doc

		try:

			report.insert()
		except DuplicateEntryError:

			# there is not problem if it exists, just ignore it

			pass

		# and try to create the boilerplate

		if not module_exists:

			# this is the safest way to create or override
			# the module content

			report.create_report_py()

		# commit current transaction. calls sql `commit`
		# lets make sure that we save the changes
		# to the database

		frappe.db.commit()

		# lets close the connection and release werkzeug local

		frappe.destroy()

@click.command("create-report-files")
@click.option("--site-name", help="Site where the record is going to be fetched from")
@click.option("--report-name", required=True, help="Name of the Report ex. `Sales Register`")
def create_report_files(site_name, report_name):
	# users can change the installation path, the operating
	# user or even have multiple benchs running in the same instance.

	# by default it is located at `/home/frappe/frappe-bench`

	# so, lets make sure we get the right path

	# get the base `frappe-bench` path where the system
	# is installed

	_base_path = frappe.utils.get_bench_path()

	# scrub to remove any trailing spaces or if it is a more complex name
	# by more than one word

	# we just want to make sure and do anything we can to guess
	# what the user wants and do it right

	_site_name = frappe.scrub(site_name)

	_sites_path = "/".join([_base_path, "sites"])

	# lets bring all the frappe sites setup on this instance

	_all_sites = frappe.utils \
		.get_sites(sites_path=_sites_path)

	# if the site does not exist in this instance
	# exit and let the user know

	if _site_name not in _all_sites:
		print ("Site {site} does not exist" \
			.format(site=_site_name))
		sys_exit()

	if _site_name != "all":
		_all_sites = [_site_name]

	module_exists = False

	for site in _all_sites:

		# initialize frappe for the current site.
		# reset thread locals `frappe.local`

		frappe.init(site=site, sites_path=_sites_path)

		# connect to site database instance
		# frappe.connect will try to init again
		# this is fine as we don't any other solution by now

		frappe.connect(site=site)

		# we now can import the frappe.db object

		from frappe import db

		# if the report exists in at least one site
		# that could mean we are posibly overriding the content
		# of the controllers

		# so, lets make sure that this never happens
		# if we prove it to be true, we don't want to write to the files
		# this is why we use two loops

		if not db.exists("Report", {
			"report_name": report_name,
		}):
			# mark the flag as true

			module_exists = True

			# and skip this round

		report = frappe.get_doc("Report", report_name)

		report_path = frappe.get_module_path(report.module,
			"report", report_name)

		frappe.create_folder(report_path, with_init=True)

		report.create_report_py()

		# lets close the connection and release werkzeug local

		frappe.destroy()

def sys_exit():
	"""Exits the whole thead"""
	import sys

	# this is just to make it simpler when
	# the script needs to stop
	sys.exit(1)

def get_commands():
	"""Return all the bench_manager commands"""

	# this should return a list of commands
	# that they can be integrated to the whole framework
	return [
		create_patch,
		create_module,
		create_report,
		create_report_files,
	]

# lets import the commands list from frappe
# and append our newly created commands

from frappe.commands import commands

# we basically update the frappe.commands on the fly
# so that they're included in the frappe group just as
# if they were part of the frappe app

for cmd in get_commands():
	commands.append(cmd)
