# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
from unittest.mock import patch

import frappe
from frappe.model.workflow import (
	WorkflowTransitionError,
	apply_workflow,
	get_common_transition_actions,
	get_transitions,
)
from frappe.query_builder import DocType
from frappe.test_runner import make_test_records
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string


class TestWorkflow(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_test_records("User")

	def setUp(self):
		self.patcher = patch("frappe.attach_print", return_value={})
		self.patcher.start()
		frappe.db.delete("Workflow Action")
		self.workflow = create_todo_workflow()

	def tearDown(self):
		frappe.set_user("Administrator")
		self.patcher.stop()
		frappe.delete_doc("Workflow", "Test ToDo")

	def test_default_condition(self):
		"""test default condition is set"""
		todo = create_new_todo()

		# default condition is set
		self.assertEqual(todo.workflow_state, "Pending")

		return todo

	def test_approve(self, doc=None):
		"""test simple workflow"""
		todo = doc or self.test_default_condition()

		apply_workflow(todo, "Approve")
		# default condition is set
		self.assertEqual(todo.workflow_state, "Approved")
		self.assertEqual(todo.status, "Closed")

		return todo

	def test_wrong_action(self):
		"""Check illegal action (approve after reject)"""
		todo = self.test_approve()

		self.assertRaises(WorkflowTransitionError, apply_workflow, todo, "Reject")

	def test_workflow_condition(self):
		"""Test condition in transition"""
		self.workflow.transitions[0].condition = 'doc.status == "Closed"'
		self.workflow.save()

		# only approve if status is closed
		self.assertRaises(WorkflowTransitionError, self.test_approve)

		self.workflow.transitions[0].condition = ""
		self.workflow.save()

	def test_get_common_transition_actions(self):
		todo1 = create_new_todo()
		todo2 = create_new_todo()
		todo3 = create_new_todo()
		todo4 = create_new_todo()

		actions = get_common_transition_actions([todo1, todo2, todo3, todo4], "ToDo")
		self.assertSetEqual(set(actions), {"Approve", "Reject"})

		apply_workflow(todo1, "Reject")
		apply_workflow(todo2, "Reject")
		apply_workflow(todo3, "Approve")

		actions = get_common_transition_actions([todo1, todo2, todo3], "ToDo")
		self.assertListEqual(actions, [])

		actions = get_common_transition_actions([todo1, todo2], "ToDo")
		self.assertListEqual(actions, ["Review"])

	def test_if_workflow_actions_were_processed_using_role(self):
		user = frappe.get_doc("User", "test2@example.com")
		user.add_roles("Test Approver", "System Manager")
		frappe.set_user("test2@example.com")

		doc = self.test_default_condition()
		workflow_actions = frappe.get_all("Workflow Action", fields=["*"])
		self.assertEqual(len(workflow_actions), 1)

		# test if status of workflow actions are updated on approval
		self.test_approve(doc)
		user.remove_roles("Test Approver", "System Manager")
		workflow_actions = frappe.get_all("Workflow Action", fields=["*"])
		self.assertEqual(len(workflow_actions), 1)
		self.assertEqual(workflow_actions[0].status, "Completed")

	def test_if_workflow_actions_were_processed_using_user(self):
		user = frappe.get_doc("User", "test2@example.com")
		user.add_roles("Test Approver", "System Manager")
		frappe.set_user("test2@example.com")

		doc = self.test_default_condition()
		workflow_actions = frappe.get_all("Workflow Action", fields=["*"])
		self.assertEqual(len(workflow_actions), 1)

		# test if status of workflow actions are updated on approval
		WorkflowAction = DocType("Workflow Action")
		WorkflowActionPermittedRole = DocType("Workflow Action Permitted Role")
		frappe.qb.update(WorkflowAction).set(WorkflowAction.user, "test2@example.com").run()
		frappe.qb.update(WorkflowActionPermittedRole).set(WorkflowActionPermittedRole.role, "").run()

		self.test_approve(doc)

		user.remove_roles("Test Approver", "System Manager")
		workflow_actions = frappe.get_all("Workflow Action", fields=["status"])
		self.assertEqual(len(workflow_actions), 1)
		self.assertEqual(workflow_actions[0].status, "Completed")
		frappe.set_user("Administrator")

	def test_if_workflow_set_on_action(self):
		self.workflow._update_state_docstatus = True
		self.workflow.states[1].doc_status = 1
		self.workflow.save()
		todo = create_new_todo()
		self.assertEqual(todo.docstatus, 0)
		todo.submit()
		self.assertEqual(todo.docstatus, 1)
		self.assertEqual(todo.workflow_state, "Approved")

		self.workflow.states[1].doc_status = 0
		self.workflow.save()

	def test_syntax_error_in_transition_rule(self):
		self.workflow.transitions[0].condition = 'doc.status =! "Closed"'

		with self.assertRaises(frappe.ValidationError) as se:
			self.workflow.save()

		self.assertTrue(
			"invalid python code" in str(se.exception).lower(), msg="Python code validation not working"
		)

	def test_workflow_safe_eval_globals_hook(self):
		"""Test that workflow_safe_eval_globals hook can extend globals in workflow conditions"""

		# Create a test hook function
		def test_hook(globals_dict):
			return {"custom_value": "test_value", "custom_function": lambda x: x * 2}

		# Register the hook temporarily
		original_hooks = frappe.get_hooks("workflow_safe_eval_globals")
		frappe.local.conf.setdefault("workflow_safe_eval_globals", [])
		frappe.local.conf["workflow_safe_eval_globals"].append(
			"frappe.workflow.doctype.workflow.test_workflow.test_workflow_safe_eval_globals_hook_fn"
		)

		# Create workflow with condition using custom global
		self.workflow.transitions[0].condition = 'custom_value == "test_value"'
		self.workflow.save()

		# Mock the hook function
		import frappe.workflow.doctype.workflow.test_workflow as test_module

		test_module.test_workflow_safe_eval_globals_hook_fn = test_hook

		try:
			# This should work because custom_value is now available
			todo = create_new_todo()
			transitions = get_transitions(todo)
			# Should have both Approve and Reject transitions since condition is satisfied
			self.assertEqual(len(transitions), 2)
		finally:
			# Cleanup
			self.workflow.transitions[0].condition = ""
			self.workflow.save()
			if hasattr(test_module, "test_workflow_safe_eval_globals_hook_fn"):
				delattr(test_module, "test_workflow_safe_eval_globals_hook_fn")
			frappe.local.conf["workflow_safe_eval_globals"] = original_hooks

	def test_filter_workflow_transitions_hook(self):
		"""Test that filter_workflow_transitions hook can filter transitions"""

		def filter_hook(doc, transitions, workflow):
			# Filter out the "Reject" action
			return [t for t in transitions if t.get("action") != "Reject"]

		# Register the hook temporarily
		original_hooks = frappe.get_hooks("filter_workflow_transitions")
		frappe.local.conf.setdefault("filter_workflow_transitions", [])
		frappe.local.conf["filter_workflow_transitions"].append(
			"frappe.workflow.doctype.workflow.test_workflow.test_filter_workflow_transitions_hook_fn"
		)

		# Mock the hook function
		import frappe.workflow.doctype.workflow.test_workflow as test_module

		test_module.test_filter_workflow_transitions_hook_fn = filter_hook

		try:
			todo = create_new_todo()
			transitions = get_transitions(todo)
			# Should only have Approve transition after filtering
			self.assertEqual(len(transitions), 1)
			self.assertEqual(transitions[0]["action"], "Approve")
		finally:
			# Cleanup
			if hasattr(test_module, "test_filter_workflow_transitions_hook_fn"):
				delattr(test_module, "test_filter_workflow_transitions_hook_fn")
			frappe.local.conf["filter_workflow_transitions"] = original_hooks


def create_todo_workflow():
	from frappe.tests.ui_test_helpers import UI_TEST_USER

	if frappe.db.exists("Workflow", "Test ToDo"):
		frappe.delete_doc("Workflow", "Test ToDo")

	TEST_ROLE = "Test Approver"

	if not frappe.db.exists("Role", TEST_ROLE):
		frappe.get_doc(dict(doctype="Role", role_name=TEST_ROLE)).insert(ignore_if_duplicate=True)
		if frappe.db.exists("User", UI_TEST_USER):
			frappe.get_doc("User", UI_TEST_USER).add_roles(TEST_ROLE)

	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = "Test ToDo"
	workflow.document_type = "ToDo"
	workflow.workflow_state_field = "workflow_state"
	workflow.is_active = 1
	workflow.send_email_alert = 1
	workflow.append("states", dict(state="Pending", allow_edit="All"))
	workflow.append(
		"states",
		dict(state="Approved", allow_edit=TEST_ROLE, update_field="status", update_value="Closed"),
	)
	workflow.append("states", dict(state="Rejected", allow_edit=TEST_ROLE))
	workflow.append(
		"transitions",
		dict(
			state="Pending",
			action="Approve",
			next_state="Approved",
			allowed=TEST_ROLE,
			allow_self_approval=1,
		),
	)
	workflow.append(
		"transitions",
		dict(
			state="Pending",
			action="Reject",
			next_state="Rejected",
			allowed=TEST_ROLE,
			allow_self_approval=1,
		),
	)
	workflow.append(
		"transitions",
		dict(state="Rejected", action="Review", next_state="Pending", allowed="All", allow_self_approval=1),
	)
	workflow.insert(ignore_permissions=True)

	return workflow


def create_new_todo():
	return frappe.get_doc(dict(doctype="ToDo", description="workflow " + random_string(10))).insert()
