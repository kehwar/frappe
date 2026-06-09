# Copyright (c) 2019, Frappe Technologies and Contributors
# License: MIT. See LICENSE
import requests

import frappe
from frappe.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
from frappe.frappeclient import FrappeClient, FrappeException
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_site_url

scripts = [
	dict(
		title="test_todo",
		name="test_todo",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "test" in doc.description:
	doc.status = 'Closed'
""",
	),
	dict(
		title="test_todo_validate",
		name="test_todo_validate",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "validate" in doc.description:
	raise frappe.ValidationError
""",
	),
	dict(
		title="test_api",
		name="test_api",
		script_type="API",
		api_method="test_server_script",
		allow_guest=1,
		script="""
frappe.response['message'] = 'hello'
""",
	),
	dict(
		title="test_return_value",
		name="test_return_value",
		script_type="API",
		api_method="test_return_value",
		allow_guest=1,
		script="""
frappe.flags = 'hello'
""",
	),
	dict(
		title="test_permission_query",
		name="test_permission_query",
		script_type="Permission Query",
		reference_doctype="ToDo",
		script="""
conditions = '1 = 1'
""",
	),
	dict(
		title="test_invalid_namespace_method",
		name="test_invalid_namespace_method",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="Note",
		disabled=1,
		script="""
frappe.method_that_doesnt_exist("do some magic")
""",
	),
	dict(
		title="test_todo_commit",
		name="test_todo_commit",
		script_type="DocType Event",
		doctype_event="Before Save",
		reference_doctype="ToDo",
		disabled=1,
		script="""
frappe.db.commit()
""",
	),
	dict(
		title="test_add_index",
		name="test_add_index",
		script_type="DocType Event",
		doctype_event="Before Save",
		reference_doctype="ToDo",
		disabled=1,
		script="""
frappe.db.add_index("Todo", ["color", "date"])
""",
	),
	dict(
		title="test_before_rename",
		name="test_before_rename",
		script_type="DocType Event",
		doctype_event="After Rename",
		reference_doctype="Role",
		script="""
doc.desk_access =0
doc.save()
""",
	),
	dict(
		title="test_after_rename",
		name="test_after_rename",
		script_type="DocType Event",
		doctype_event="After Rename",
		reference_doctype="Role",
		script="""
doc.disabled =1
doc.save()
""",
	),
	dict(
		title="test_before_naming",
		script_type="DocType Event",
		doctype_event="Before Naming",
		reference_doctype="Note",
		script="""
# Set a custom name prefix
doc.flags.custom_naming = True
""",
	),
	dict(
		title="test_on_change",
		script_type="DocType Event",
		doctype_event="After Change",
		reference_doctype="ToDo",
		script="""
# Track that on_change was called
doc.flags.on_change_called = True
""",
	),
	dict(
		title="test_before_change",
		script_type="DocType Event",
		doctype_event="Before Change",
		reference_doctype="ToDo",
		script="""
# Track that before_change was called
doc.flags.before_change_called = True
""",
	),
	dict(
		title="test_before_save",
		script_type="DocType Event",
		doctype_event="After Validate",
		reference_doctype="ToDo",
		script="""
# Track that before_save was called
doc.flags.before_save_called = True
""",
	),
	dict(
		title="test_before_export",
		script_type="DocType Event",
		doctype_event="Before Export",
		reference_doctype="ToDo",
		script="""
# Track that before_export was called
doc.flags.before_export_called = True
""",
	),
	dict(
		title="test_before_import",
		script_type="DocType Event",
		doctype_event="Before Import",
		reference_doctype="ToDo",
		script="""
# Track that before_import was called
doc.flags.before_import_called = True
""",
	),
	dict(
		title="test_before_transition",
		script_type="DocType Event",
		doctype_event="Before Workflow Transition",
		reference_doctype="ToDo",
		script="""
# Track that before_transition was called
doc.flags.before_transition_called = True
""",
	),
	dict(
		title="test_after_transition",
		script_type="DocType Event",
		doctype_event="After Workflow Transition",
		reference_doctype="ToDo",
		script="""
# Track that after_transition was called
doc.flags.after_transition_called = True
""",
	),
]


class TestServerScript(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.db.truncate("Server Script")
		frappe.get_doc("User", "Administrator").add_roles("Script Manager")
		for script in scripts:
			script_doc = frappe.get_doc(doctype="Server Script")
			script_doc.update(script)
			script_doc.insert()
		cls.enable_safe_exec()
		frappe.db.commit()
		return super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		frappe.db.commit()
		frappe.db.truncate("Server Script")
		frappe.cache.delete_value("server_script_map")

	def setUp(self):
		frappe.cache.delete_value("server_script_map")

	def test_doctype_event(self):
		todo = frappe.get_doc(dict(doctype="ToDo", description="hello")).insert()
		self.assertEqual(todo.status, "Open")

		todo = frappe.get_doc(dict(doctype="ToDo", description="test todo")).insert()
		self.assertEqual(todo.status, "Closed")

		self.assertRaises(
			frappe.ValidationError, frappe.get_doc(dict(doctype="ToDo", description="validate me")).insert
		)

		role = frappe.get_doc(doctype="Role", role_name="_Test Role 9").insert(ignore_if_duplicate=True)
		role.rename("_Test Role 10")
		role.reload()
		self.assertEqual(role.disabled, 1)
		self.assertEqual(role.desk_access, 0)

	def test_api(self):
		response = requests.post(get_site_url(frappe.local.site) + "/api/method/test_server_script")
		self.assertEqual(response.status_code, 200)
		self.assertEqual("hello", response.json()["message"])

	def test_api_return(self):
		self.assertEqual(frappe.get_doc("Server Script", "test_return_value").execute_method(), "hello")

	def test_permission_query(self):
		if frappe.conf.db_type == "mariadb":
			self.assertTrue("where (1 = 1)" in frappe.db.get_list("ToDo", run=False))
		else:
			self.assertTrue("where (1 = '1')" in frappe.db.get_list("ToDo", run=False))
		self.assertTrue(isinstance(frappe.db.get_list("ToDo"), list))

	def test_attribute_error(self):
		"""Raise AttributeError if method not found in Namespace"""
		script = frappe.get_doc("Server Script", "test_invalid_namespace_method")
		script.disabled = 0
		script.save()
		try:
			note = frappe.get_doc({"doctype": "Note", "title": "Test Note: Server Script"})
			self.assertRaises(AttributeError, note.insert)
		finally:
			script.disabled = 1
			script.save()

	def test_syntax_validation(self):
		server_script = scripts[0]
		server_script["script"] = "js || code.?"

		with self.assertRaises(frappe.ValidationError) as se:
			frappe.get_doc(doctype="Server Script", **server_script).insert()

		self.assertTrue(
			"invalid python code" in str(se.exception).lower(), msg="Python code validation not working"
		)

	def test_commit_in_doctype_event(self):
		server_script = frappe.get_doc("Server Script", "test_todo_commit")
		server_script.disabled = 0
		server_script.save()

		self.assertRaises(AttributeError, frappe.get_doc(dict(doctype="ToDo", description="test me")).insert)

		server_script.disabled = 1
		server_script.save()

	def test_add_index_in_doctype_event(self):
		server_script = frappe.get_doc("Server Script", "test_add_index")
		server_script.disabled = 0
		server_script.save()

		self.assertRaises(AttributeError, frappe.get_doc(dict(doctype="ToDo", description="test me")).insert)

		server_script.disabled = 1
		server_script.save()

	def test_restricted_qb(self):
		todo = frappe.get_doc(doctype="ToDo", description="QbScriptTestNote")
		todo.insert()

		script = frappe.get_doc(
			doctype="Server Script",
			title="test_qb_restrictions",
			name="test_qb_restrictions",
			script_type="API",
			api_method="test_qb_restrictions",
			allow_guest=1,
			# whitelisted update
			script=f"""
frappe.db.set_value("ToDo", "{todo.name}", "description", "safe")
""",
		)
		script.insert()
		script.execute_method()

		todo.reload()
		self.assertEqual(todo.description, "safe")

		# unsafe update
		script.script = f"""
todo = frappe.qb.DocType("ToDo")
frappe.qb.update(todo).set(todo.description, "unsafe").where(todo.name == "{todo.name}").run()
"""
		script.save()
		self.assertRaises(frappe.PermissionError, script.execute_method)
		todo.reload()
		self.assertEqual(todo.description, "safe")

		# safe select
		script.script = f"""
todo = frappe.qb.DocType("ToDo")
frappe.qb.from_(todo).select(todo.name).where(todo.name == "{todo.name}").run()
"""
		script.save()
		script.execute_method()

	def test_scripts_all_the_way_down(self):
		# why not
		script = frappe.get_doc(
			doctype="Server Script",
			title="test_nested_scripts_1",
			name="test_nested_scripts_1",
			script_type="API",
			api_method="test_nested_scripts_1",
			script="""log("nothing")""",
		)
		script.insert()
		script.execute_method()

		script = frappe.get_doc(
			doctype="Server Script",
			title="test_nested_scripts_2",
			name="test_nested_scripts_2",
			script_type="API",
			api_method="test_nested_scripts_2",
			script="""frappe.call("test_nested_scripts_1")""",
		)
		script.insert()
		script.execute_method()

	def test_server_script_rate_limiting(self):
		script1 = frappe.get_doc(
			doctype="Server Script",
			title="rate_limited_server_script",
			name="rate_limited_server_script",
			script_type="API",
			enable_rate_limit=1,
			allow_guest=1,
			rate_limit_count=5,
			api_method="rate_limited_endpoint",
			script="""frappe.flags = {"test": True}""",
		)

		script1.insert()

		script2 = frappe.get_doc(
			doctype="Server Script",
			title="rate_limited_server_script2",
			name="rate_limited_server_script2",
			script_type="API",
			enable_rate_limit=1,
			allow_guest=1,
			rate_limit_count=5,
			api_method="rate_limited_endpoint2",
			script="""frappe.flags = {"test": False}""",
		)

		script2.insert()

		frappe.db.commit()

		site = frappe.utils.get_site_url(frappe.local.site)
		client = FrappeClient(site)

		# Exhaust rate limit
		for _ in range(5):
			client.get_api(script1.api_method)

		self.assertRaises(FrappeException, client.get_api, script1.api_method)

		# Exhaust rate limit
		for _ in range(5):
			client.get_api(script2.api_method)

		self.assertRaises(FrappeException, client.get_api, script2.api_method)

		script1.delete()
		script2.delete()
		frappe.db.commit()

	def test_server_script_scheduled(self):
		scheduled_script = frappe.get_doc(
			doctype="Server Script",
			title="scheduled_script_wo_cron",
			name="scheduled_script_wo_cron",
			script_type="Scheduler Event",
			script="""frappe.flags = {"test": True}""",
			event_frequency="Hourly",
		).insert()

		cron_script = frappe.get_doc(
			doctype="Server Script",
			title="scheduled_script_w_cron",
			name="scheduled_script_w_cron",
			script_type="Scheduler Event",
			script="""frappe.flags = {"test": True}""",
			event_frequency="Cron",
			cron_format="0 0 1 1 *",  # 1st january
		).insert()

		# Ensure that jobs remain in DB after migrate
		sync_jobs()
		self.assertTrue(frappe.db.exists("Scheduled Job Type", {"server_script": scheduled_script.name}))

		cron_job_name = frappe.db.get_value("Scheduled Job Type", {"server_script": cron_script.name})
		self.assertTrue(cron_job_name)

		cron_job = frappe.get_doc("Scheduled Job Type", cron_job_name)
		self.assertEqual(cron_job.next_execution.day, 1)
		self.assertEqual(cron_job.next_execution.month, 1)

		cron_script.cron_format = "0 0 2 1 *"  # 2nd january
		cron_script.save()
		cron_job.reload()
		self.assertEqual(cron_job.next_execution.day, 2)

	def test_before_naming_event(self):
		"""Test that Before Naming event is triggered"""
		note = frappe.get_doc({"doctype": "Note", "title": "Test Naming Script"})
		note.insert()
		# Check that the flag was set by the server script
		self.assertTrue(note.flags.get("custom_naming"))

	def test_on_change_event(self):
		"""Test that After Change event is triggered when document is updated"""
		todo = frappe.get_doc({"doctype": "ToDo", "description": "Original"}).insert()
		# Update the todo to trigger on_change
		todo.description = "Updated"
		todo.save()
		# Check that on_change was called
		self.assertTrue(todo.flags.get("on_change_called"))

	def test_before_change_event(self):
		"""Test that Before Change event is triggered when document is updated via db_set"""
		todo = frappe.get_doc({"doctype": "ToDo", "description": "Original"}).insert()
		# Update the todo via db_set to trigger before_change
		todo.db_set("description", "Updated")
		# Check that before_change was called
		self.assertTrue(todo.flags.get("before_change_called"))

	def test_before_save_event(self):
		"""Test that After Validate (before_save) event is triggered"""
		todo = frappe.get_doc({"doctype": "ToDo", "description": "Test Before Save"})
		todo.insert()
		# Check that before_save was called
		self.assertTrue(todo.flags.get("before_save_called"))
