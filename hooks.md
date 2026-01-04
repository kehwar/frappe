### List of Hooks

#### Application Name and Details

1. `app_name` - slugified name e.g. "frappe"
1. `app_title` - full title name e.g. "Frappe"
1. `app_publisher`
1. `app_description`
1. `app_version`

#### Install

1. `before_install` - method
1. `after_install` - method


#### Javascript / CSS Builds

1. `app_include_js` - include in "app"
1. `app_include_css` - assets/frappe/css/splash.css

1. `web_include_js` - assets/js/frappe-web.min.js
1. `web_include_css` - assets/css/frappe-web.css

#### Desktop

1. `get_desktop_icons` - method to get list of desktop icons

#### Notifications

1. `notification_config` - method to get notification configuration

#### Permissions

1. `permission_query_conditions:[doctype]` - method to return additional query conditions at time of report / list etc.
1. `has_permission:[doctype]` - method to call permissions to check at individual level
1. `get_write_permission_query_conditions:[doctype]` - method to return query conditions to validate record after write but before commit

##### get_write_permission_query_conditions

This hook is called **after** the database write operation (INSERT or UPDATE) but **before** the transaction commits. It allows you to validate the written record against custom permission conditions and rollback the transaction if validation fails.

**Use Cases:**
- Validate field values that can only be determined after the record is saved
- Check conditions that depend on database state
- Enforce complex business rules that need to verify the actual saved data

**Hook Signature:**
```python
def get_write_permission_query_conditions(user=None, doc=None):
    """
    Returns SQL WHERE conditions to validate the saved record.
    
    Args:
        user: The user for whom to check permissions (defaults to current user)
        doc: The document being saved
    
    Returns:
        str: SQL WHERE clause conditions (without the WHERE keyword)
        
    Example:
        return "`status` = 'Draft' OR `owner` = '{}'".format(frappe.db.escape(user))
    """
```

**Example Implementation:**
```python
# In your doctype's Python file (e.g., event.py)

def get_write_permission_query_conditions(user=None, doc=None):
    """Only allow saving events if user is owner or event is public"""
    if not user:
        user = frappe.session.user
    return f"(`event_type`='Public' OR `owner`={frappe.db.escape(user)})"
```

**Hook Registration in hooks.py:**
```python
get_write_permission_query_conditions = {
    "Event": "myapp.event.event.get_write_permission_query_conditions",
}
```

**Behavior:**
- If the saved record doesn't match the returned conditions, the transaction is rolled back and a PermissionError is raised
- If no hook is defined or the hook returns None/empty string, no validation is performed
- Administrator user bypasses these checks
- The `ignore_permissions` flag bypasses these checks
