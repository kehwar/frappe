# Implementation Summary: get_write_permission_query_conditions Hook

## Overview

This PR implements the `get_write_permission_query_conditions` hook as requested in the issue. The hook addresses the need for permission checks **after** database write operations but **before** the transaction commits.

## Problem Statement

The original issue requested:
- An additional hook called after DB write but before commit
- Use the returned query to check the inserted/updated record
- Rollback and deny operation if check fails

## Solution

### Hook Flow

```
Document.insert() / Document.save()
  ↓
Pre-write checks (has_permission)
  ↓
db_insert() / db_update()  ← Data written to DB
  ↓
check_write_permission_query_conditions()  ← NEW HOOK
  ↓ (if validation passes)
COMMIT
  ↓ (if validation fails)
ROLLBACK + PermissionError
```

### Key Features

1. **Post-Write Validation**: Called after `db_insert()`/`db_update()`, before `run_post_save_methods()`
2. **SQL-Based Checks**: Returns SQL WHERE conditions to validate the saved record
3. **Automatic Rollback**: Rolls back transaction if validation fails
4. **Consistent with Existing Hooks**: Similar signature to `permission_query_conditions`
5. **Administrator Bypass**: Administrator users skip this check
6. **Respects Flags**: Honors `ignore_permissions` flag

## Implementation Details

### 1. Core Function (`frappe/permissions.py`)

```python
def check_write_permission_query_conditions(doc, user=None):
    """Check if document passes write permission query conditions."""
    # Get hooks for this doctype
    hooks = frappe.get_hooks("get_write_permission_query_conditions", {})
    condition_methods = hooks.get(doctype, []) + hooks.get("*", [])
    
    # Call each hook method to get conditions
    conditions = []
    for method in condition_methods:
        if condition := frappe.call(method, user=user, doc=doc):
            conditions.append(f"({condition})")
    
    # Execute query to validate record
    result = frappe.db.sql(
        f"SELECT name FROM `tab{doctype}` WHERE name = %s AND ({conditions})",
        (doc.name,)
    )
    
    return bool(result)
```

### 2. Document Integration (`frappe/model/document.py`)

Added call in two places:

**After insert:**
```python
# children
for d in self.get_all_children():
    d.db_insert()

# Check write permission query conditions after DB write
self.check_write_permission_query_conditions()

self.run_method("after_insert")
```

**After update:**
```python
self.update_children()

# Check write permission query conditions after DB write
self.check_write_permission_query_conditions()

self.run_post_save_methods()
```

### 3. Rollback Logic

```python
def check_write_permission_query_conditions(self):
    if self.flags.ignore_permissions:
        return
    
    if not check_write_permission_query_conditions(self):
        frappe.db.rollback()
        raise frappe.PermissionError(
            "The record does not meet the required write permission conditions."
        )
```

## Usage Example

```python
# In your_doctype.py

def get_write_permission_query_conditions(user=None, doc=None):
    """Only allow saving if status is Draft or user is owner"""
    if not user:
        user = frappe.session.user
    return f"(`status` = 'Draft' OR `owner` = {frappe.db.escape(user)})"
```

**Register in hooks.py:**
```python
get_write_permission_query_conditions = {
    "Your DocType": "your_app.your_module.get_write_permission_query_conditions"
}
```

## Testing

Added comprehensive test in `frappe/tests/test_permissions.py`:

1. **Test successful insert**: Document meeting conditions is saved
2. **Test failed insert with rollback**: Document not meeting conditions is rejected and not saved
3. **Test failed update with rollback**: Update violating conditions is rejected and rolled back

## Documentation

1. **hooks.md**: Updated with hook description and examples
2. **WRITE_PERMISSION_HOOK_EXAMPLE.md**: Created comprehensive guide with:
   - 5 practical use case examples
   - Comparison with `has_permission` hook
   - Best practices and debugging tips
   - Testing guidelines
3. **boilerplate.py**: Updated template with hook example

## Comparison with Existing Hooks

| Hook | When Called | Purpose | Return Type |
|------|-------------|---------|-------------|
| `has_permission` | Before DB write | Check if user can perform action | Boolean |
| `permission_query_conditions` | Query time | Filter list view records | SQL WHERE clause |
| **`get_write_permission_query_conditions`** | **After DB write, before commit** | **Validate saved record** | **SQL WHERE clause** |

## Benefits

1. **Post-Save Validation**: Can validate computed/calculated fields that only exist after save
2. **Database State Checks**: Can check conditions that depend on database state
3. **Transaction Safety**: Automatic rollback ensures data consistency
4. **Flexible**: Can implement complex cross-doctype validation
5. **Backward Compatible**: Optional hook, doesn't affect existing code

## Limitations

1. **Write Operations Only**: Only applies to INSERT and UPDATE, not DELETE
2. **Main Document Only**: Checks parent document, not child tables individually
3. **Transaction Required**: Requires database transaction support
4. **SQL-Based**: Conditions must be expressible as SQL WHERE clauses

## Security Considerations

- Hook methods are trusted code from developers, not user input
- Hook methods must properly escape any user-provided values using `frappe.db.escape()`
- Administrator users bypass this check (same as other permission checks)
- `ignore_permissions` flag bypasses this check (consistent with other checks)

## Files Changed

1. `frappe/permissions.py` - Added core validation function
2. `frappe/model/document.py` - Integrated hook calls
3. `frappe/tests/test_permissions.py` - Added test cases
4. `hooks.md` - Updated documentation
5. `frappe/utils/boilerplate.py` - Updated template
6. `WRITE_PERMISSION_HOOK_EXAMPLE.md` - Created examples guide

## Breaking Changes

None. This is a purely additive change. Existing code is unaffected if the hook is not used.

## Migration Guide

No migration needed. The hook is optional and only applies to doctypes that explicitly register it.

## Future Enhancements

Possible future improvements:
1. Support for child table validation
2. Batch validation for bulk operations
3. Caching of hook results for performance
4. More granular control over when hook is called (insert vs update)
