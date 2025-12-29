# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import copy

import frappe
from frappe.core.doctype.version.version import get_diff
from frappe.test_runner import make_test_objects
from frappe.tests.utils import FrappeTestCase


class TestVersion(FrappeTestCase):
	def test_get_diff(self):
		frappe.set_user("Administrator")
		test_records = make_test_objects("Event", reset=True)
		old_doc = frappe.get_doc("Event", test_records[0])
		new_doc = copy.deepcopy(old_doc)

		old_doc.color = None
		new_doc.color = "#fafafa"

		diff = get_diff(old_doc, new_doc)["changed"]

		self.assertEqual(get_fieldnames(diff)[0], "color")
		self.assertTrue(get_old_values(diff)[0] is None)
		self.assertEqual(get_new_values(diff)[0], "#fafafa")

		new_doc.starts_on = "2017-07-20"

		diff = get_diff(old_doc, new_doc)["changed"]

		self.assertEqual(get_fieldnames(diff)[1], "starts_on")
		self.assertEqual(get_old_values(diff)[1], "01-01-2014 00:00:00")
		self.assertEqual(get_new_values(diff)[1], "07-20-2017 00:00:00")

	def test_no_version_on_new_doc(self):
		from frappe.desk.form.load import get_versions

		t = frappe.get_doc(doctype="ToDo", description="something")
		t.save(ignore_version=False)

		self.assertFalse(get_versions(t))

		t = frappe.get_doc(t.doctype, t.name)
		t.description = "changed"
		t.save(ignore_version=False)
		self.assertTrue(get_versions(t))

	def test_extend_get_versions_hook(self):
		"""Test that the extend_get_versions hook allows apps to add custom version entries"""
		from frappe.desk.form.load import get_versions
		from frappe.tests.utils import patch_hooks

		# Create a test document
		t = frappe.get_doc(doctype="ToDo", description="test hook")
		t.save(ignore_version=False)

		# Create a test hook method
		def custom_versions_for_todo(doc):
			"""Test hook that adds custom version entries"""
			return [
				{
					"name": "custom-version-1",
					"owner": "test@example.com",
					"creation": "2023-01-01 12:00:00",
					"data": '{"test": "custom version"}',
				}
			]

		def custom_versions_for_all(doc):
			"""Test hook that adds custom version entries for all doctypes"""
			return [
				{
					"name": "custom-version-wildcard",
					"owner": "test@example.com",
					"creation": "2023-01-02 12:00:00",
					"data": '{"test": "wildcard version"}',
				}
			]

		# Register the test methods in the current module
		import sys

		test_module = sys.modules[__name__]
		test_module.custom_versions_for_todo = custom_versions_for_todo
		test_module.custom_versions_for_all = custom_versions_for_all

		# Test with hooks using patch_hooks utility
		with patch_hooks(
			{
				"extend_get_versions": {
					"ToDo": ["frappe.core.doctype.version.test_version.custom_versions_for_todo"],
					"*": ["frappe.core.doctype.version.test_version.custom_versions_for_all"],
				}
			}
		):
			# Get versions - should include custom entries from hooks
			versions = get_versions(t)

			# Verify that custom versions are included
			version_names = [v.get("name") for v in versions]
			self.assertIn("custom-version-1", version_names, "ToDo-specific hook version should be included")
			self.assertIn(
				"custom-version-wildcard", version_names, "Wildcard hook version should be included"
			)

	def test_extend_get_versions_hook_error_handling(self):
		"""Test that errors in hook methods don't break get_versions"""
		from frappe.desk.form.load import get_versions
		from frappe.tests.utils import patch_hooks

		# Create a test document
		t = frappe.get_doc(doctype="ToDo", description="test error handling")
		t.save(ignore_version=False)

		def failing_hook(doc):
			"""Hook that raises an error"""
			raise Exception("Test error in hook")

		def working_hook(doc):
			"""Hook that works correctly"""
			return [
				{
					"name": "working-version",
					"owner": "test@example.com",
					"creation": "2023-01-01 12:00:00",
					"data": '{"test": "working"}',
				}
			]

		# Register the test methods
		import sys

		test_module = sys.modules[__name__]
		test_module.failing_hook = failing_hook
		test_module.working_hook = working_hook

		# Test that get_versions still works even if one hook fails
		with patch_hooks(
			{
				"extend_get_versions": {
					"ToDo": [
						"frappe.core.doctype.version.test_version.failing_hook",
						"frappe.core.doctype.version.test_version.working_hook",
					]
				}
			}
		):
			# Should not raise an exception
			versions = get_versions(t)

			# Working hook should still add its version
			version_names = [v.get("name") for v in versions]
			self.assertIn("working-version", version_names, "Working hook should still add version despite other hook failing")


def get_fieldnames(change_array):
	return [d[0] for d in change_array]


def get_old_values(change_array):
	return [d[1] for d in change_array]


def get_new_values(change_array):
	return [d[2] for d in change_array]
