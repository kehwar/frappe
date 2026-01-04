# get_write_permission_query_conditions Hook - Examples

This document provides practical examples of using the `get_write_permission_query_conditions` hook.

## Overview

The `get_write_permission_query_conditions` hook is called **after** a document is written to the database but **before** the transaction is committed. This allows you to:

1. Validate the actual saved record against complex conditions
2. Check conditions that depend on database state
3. Enforce business rules on the written data
4. Rollback the transaction if validation fails

## How It Works

```
┌─────────────────┐
│  User saves doc │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validate form  │  ← Standard validations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ check_permission│  ← has_permission hook
│   ("write")     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DB INSERT/UPDATE│  ← Data written to DB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Check write    │  ← get_write_permission_query_conditions
│  permission     │     NEW HOOK (this one!)
│  conditions     │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Pass?   │
    └─┬───┬───┘
      │   │
     YES  NO
      │   │
      │   └──► ROLLBACK + PermissionError
      │
      ▼
┌─────────────────┐
│  COMMIT to DB   │
└─────────────────┘
```

## Example 1: Restrict Updates Based on Status

**Scenario:** Users can only update a Task if its status is "Open". Once it's "Completed", only the owner or a manager can modify it.

```python
# In tasks.py

def get_write_permission_query_conditions(user=None, doc=None):
    """
    Allow writes if:
    - Task status is 'Open', OR
    - User is the owner, OR
    - User has 'Task Manager' role
    """
    if not user:
        user = frappe.session.user
    
    # Check if user has manager role
    has_manager_role = "Task Manager" in frappe.get_roles(user)
    
    if has_manager_role:
        # Managers can update any task
        return ""
    
    # Non-managers can only update open tasks or their own tasks
    return f"""(
        `status` = 'Open' 
        OR `owner` = {frappe.db.escape(user)}
    )"""
```

**In hooks.py:**
```python
get_write_permission_query_conditions = {
    "Task": "myapp.tasks.tasks.get_write_permission_query_conditions"
}
```

## Example 2: Validate Amount Limits

**Scenario:** Sales Orders above $10,000 can only be created/updated by users with "Sales Manager" role.

```python
# In sales_order.py

def get_write_permission_query_conditions(user=None, doc=None):
    """
    Restrict high-value orders to managers only
    """
    if not user:
        user = frappe.session.user
    
    # Check if user has manager role
    has_manager_role = "Sales Manager" in frappe.get_roles(user)
    
    if has_manager_role:
        # Managers can create any order
        return ""
    
    # Non-managers can only create orders under $10,000
    return "`grand_total` < 10000"
```

## Example 3: Enforce Data Residency Rules

**Scenario:** Users can only create/update records in their assigned region.

```python
# In customer.py

def get_write_permission_query_conditions(user=None, doc=None):
    """
    Users can only save customers in their assigned region
    """
    if not user:
        user = frappe.session.user
    
    # Get user's allowed regions from User Permissions
    from frappe.core.doctype.user_permission.user_permission import get_user_permissions
    user_perms = get_user_permissions(user)
    
    if not user_perms or "Territory" not in user_perms:
        # No territory restrictions
        return ""
    
    # Get allowed territories
    allowed_territories = [d.doc for d in user_perms.get("Territory", [])]
    
    if not allowed_territories:
        return ""
    
    # Build condition to check territory
    territories_str = ", ".join([frappe.db.escape(t) for t in allowed_territories])
    return f"`territory` IN ({territories_str})"
```

## Example 4: Time-Based Restrictions

**Scenario:** Timesheets can only be edited within 24 hours of creation.

```python
# In timesheet.py

def get_write_permission_query_conditions(user=None, doc=None):
    """
    Allow edits only within 24 hours of creation
    """
    if not user:
        user = frappe.session.user
    
    # Admins can always edit
    if user == "Administrator":
        return ""
    
    # Check if user is the owner and timesheet is within 24 hours
    return f"""(
        `owner` = {frappe.db.escape(user)}
        AND TIMESTAMPDIFF(HOUR, `creation`, NOW()) < 24
    )"""
```

## Example 5: Cross-DocType Validation

**Scenario:** Validate that a document's linked records exist and meet certain criteria.

```python
# In sales_invoice.py

def get_write_permission_query_conditions(user=None, doc=None):
    """
    Only allow invoices if the customer's credit limit is not exceeded
    """
    # This validates the actual saved record
    return """EXISTS (
        SELECT 1 
        FROM `tabCustomer` c
        WHERE c.name = `tabSales Invoice`.customer
        AND (c.credit_limit = 0 OR c.credit_limit >= `tabSales Invoice`.grand_total)
    )"""
```

## Key Differences from has_permission

| Feature | has_permission | get_write_permission_query_conditions |
|---------|---------------|--------------------------------------|
| **When Called** | Before DB write | After DB write, before commit |
| **Purpose** | Check if user can write | Validate what was written |
| **Return Value** | Boolean | SQL WHERE conditions |
| **Access to Data** | Doc in memory | Doc in database |
| **Can Rollback** | No (nothing written yet) | Yes (via transaction rollback) |
| **Use Case** | "Can this user edit?" | "Is this edit allowed?" |

## Best Practices

1. **Keep it Fast**: These checks run on every save, so keep SQL simple
2. **Return Empty for "Allow All"**: Return `""` or `None` when no restrictions apply
3. **Escape User Input**: Always use `frappe.db.escape()` for user-provided values
4. **Don't Rely on doc Parameter**: The doc passed may not reflect the exact DB state for all fields
5. **Use for Post-Save Validation**: Perfect for validating computed/calculated fields that only exist after save

## Testing Your Hook

```python
# In your test file
def test_write_permission_hook():
    # Create document that should pass
    doc1 = frappe.get_doc({
        "doctype": "Task",
        "subject": "Test",
        "status": "Open"
    })
    doc1.insert()
    assert frappe.db.exists("Task", doc1.name)
    
    # Try to save with forbidden status
    doc1.status = "Completed"
    with self.assertRaises(frappe.PermissionError):
        doc1.save()
    
    # Verify rollback worked
    doc1.reload()
    assert doc1.status == "Open"
```

## Debugging

To see why a write permission check failed, check:

1. **Error Message**: Will say "Permission denied. The record does not meet the required write permission conditions."
2. **SQL Query**: Add debug logging in your hook function
3. **Database State**: Check what the actual saved record looks like

```python
def get_write_permission_query_conditions(user=None, doc=None):
    condition = "`status` = 'Open'"
    
    # Debug logging
    frappe.logger().debug(f"Write permission check for {doc.doctype} {doc.name}: {condition}")
    
    return condition
```

## Limitations

1. **Only for Writes**: This hook only applies to INSERT and UPDATE operations
2. **Not for Deletes**: Use `has_permission` with `ptype="delete"` for delete checks
3. **Transaction Required**: Relies on database transaction support (works with MariaDB/MySQL/PostgreSQL)
4. **Single DocType**: Each hook checks only the main document, not child tables (though you can use EXISTS clauses)
