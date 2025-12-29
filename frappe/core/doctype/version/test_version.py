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

		# Store original hooks
		original_hooks = frappe.get_hooks("extend_get_versions")

		try:
			# Add test hooks
			frappe.flags.in_test_hooks = True
			frappe.local.test_objects = {
				"extend_get_versions": {"ToDo": ["test_version.custom_versions_for_todo"], "*": ["test_version.custom_versions_for_all"]}
			}

			# Temporarily override get_hooks to include test hooks
			original_get_hooks = frappe.get_hooks

			def mock_get_hooks(hook=None, default=None, app_name=None):
				if hook == "extend_get_versions":
					return frappe.local.test_objects.get("extend_get_versions", {})
				return original_get_hooks(hook, default, app_name)

			frappe.get_hooks = mock_get_hooks

			# Register the test methods in frappe namespace to make them accessible
			import sys

			test_module = sys.modules[__name__]
			test_module.custom_versions_for_todo = custom_versions_for_todo
			test_module.custom_versions_for_all = custom_versions_for_all

			# Get versions - should include custom entries from hooks
			versions = get_versions(t)

			# Verify that custom versions are included
			version_names = [v.get("name") for v in versions]
			self.assertIn("custom-version-1", version_names, "ToDo-specific hook version should be included")
			self.assertIn("custom-version-wildcard", version_names, "Wildcard hook version should be included")

		finally:
			# Restore original hooks
			frappe.get_hooks = original_get_hooks
			frappe.flags.in_test_hooks = False
			if hasattr(frappe.local, "test_objects"):
				delattr(frappe.local, "test_objects")


def get_fieldnames(change_array):
	return [d[0] for d in change_array]


def get_old_values(change_array):
	return [d[1] for d in change_array]


def get_new_values(change_array):
	return [d[2] for d in change_array]
