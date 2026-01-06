---
description: 'Guide to Frappe permissions flow and extension hooks for implementing custom permission logic'
applyTo: '**/permissions.py, **/has_permission.py, **/*_permission*.py'
---

# Frappe Permissions Flow and Extension Hooks

This document provides a comprehensive guide to understanding and extending Frappe's permission system. It covers the permission evaluation flow, available hooks, and best practices for implementing custom permission logic.

## Overview

Frappe's permission system is multi-layered and evaluates permissions in a specific order:

1. **Administrator Check**: Administrator user bypasses all permission checks
2. **Role-Based Permissions**: DocType permissions configured through Permission Manager
3. **Controller Permissions**: Custom `has_permission` hooks in doctypes
4. **User Permissions**: Document-level restrictions based on user-specific rules
5. **Permission Query Conditions**: SQL-based filters for list views and reports
6. **Share Permissions**: Explicit document sharing between users

## Permission Types

Frappe supports the following permission types (ptypes):

```python
rights = (
    "select",    # View in list (limited fields)
    "read",      # Full read access
    "write",     # Edit existing documents
    "create",    # Create new documents
    "delete",    # Delete documents
    "submit",    # Submit submittable documents
    "cancel",    # Cancel submitted documents
    "amend",     # Amend cancelled documents
    "print",     # Print documents
    "email",     # Email documents
    "report",    # Access reports
    "import",    # Import documents
    "export",    # Export documents
    "share",     # Share documents with others
)
```

## Permission Evaluation Flow

### 1. Basic Permission Check (`has_permission`)

Located in `frappe/permissions.py`, this is the main entry point for permission checks:

```python
frappe.has_permission(
    doctype="DocType Name",
    ptype="read",              # Permission type to check
    doc=None,                  # Optional: specific document instance
    user=None,                 # Optional: defaults to current user
    raise_exception=True,      # Display error message if False
    parent_doctype=None,       # Required for child doctypes
    debug=False,               # Enable debug logging
    ignore_share_permissions=False
)
```

**Evaluation Order:**
1. Check if user is Administrator (always returns True)
2. Check if sharing is disabled (for ptype="share")
3. For child doctypes: delegate to parent permission check
4. Get role permissions from DocPerm/Custom DocPerm
5. Check controller permissions via `has_permission` hook
6. Check user permissions
7. Check share permissions (if not ignored)
8. For read/select with doc: check permission query conditions

### 2. Document-Level Permissions (`get_doc_permissions`)

When checking permissions for a specific document instance:

```python
permissions = get_doc_permissions(doc, user=None, ptype=None, debug=False)
# Returns: {"read": 1, "write": 1, "delete": 0, ...}
```

**Evaluation Order:**
1. Check controller permissions (`has_permission` hook)
2. Get base role permissions
3. Apply "if_owner" permissions if user is document owner
4. Check user permissions
5. Apply owner-only permissions if user permissions restrict access

### 3. Permission Query Conditions

These are SQL conditions applied to database queries for filtering lists and reports, and also checked within `has_permission` for individual document access:

```python
# Applied automatically in DatabaseQuery
conditions = get_permission_query_conditions(user=user, doctype=doctype)
# Returns: SQL WHERE clause string
```

**Used in:**
- List views
- Report generation
- Database queries via `frappe.get_list()` and `frappe.get_all()`
- Link field searches
- **Individual document access** - When `has_permission()` is called with a document for read/select operations, these conditions are checked to validate the specific document

### 4. Write Permission Query Conditions

These are SQL conditions checked after database writes to validate the operation:

```python
# Called automatically after DB write but before commit
check_write_permission_query_conditions(doc, permtype="write", user=None)
# Returns: True if document passes conditions, False otherwise
```

**Checked for:**
- Create operations (`permtype="create"`)
- Update operations (`permtype="write"`)
- Submit operations (`permtype="submit"`)
- Cancel operations (`permtype="cancel"`)
- Delete operations (`permtype="delete"`)

## Child Table Permissions

Child tables (table fields) don't have their own permissions. Instead, permissions are checked on the parent document.

**How it works:**
1. When checking permission on a child table row, the system automatically looks up the parent document
2. Permission is checked on the parent doctype
3. If the child table has a permlevel > 0, the user must have access to that permlevel on the parent

**Example:**
```python
# Checking permission on a child table row
frappe.has_permission(
    doctype="Sales Order Item",  # Child table
    ptype="read",
    doc="SOI-00001",
    parent_doctype="Sales Order"  # Must specify parent
)
# This internally checks: frappe.has_permission("Sales Order", "read", "SO-00001")
```

**Permission Levels:**
- Child tables can have permlevel > 0 set on their field in the parent doctype
- If permlevel > 0, only roles with access to that permlevel can see/edit the child table
- Useful for sensitive information (e.g., pricing details, internal notes)

## Virtual DocTypes

Virtual doctypes don't have database tables and permission query conditions don't apply to them.

**How it works:**
1. Virtual doctypes are identified using `frappe.model.utils.is_virtual_doctype()`
2. Permission query conditions are automatically skipped for virtual doctypes
3. Only `has_permission` hook and role permissions apply

**Example virtual doctype:**
```python
# In your doctype.py
class YourDocType(Document):
    @staticmethod
    def get_list(args):
        """Custom list implementation for virtual doctype."""
        # Your custom logic to return list of documents
        pass
    
    @staticmethod
    def get_count(args):
        """Return count of documents."""
        pass
    
    @staticmethod
    def get_stats(args):
        """Return statistics."""
        pass
```

## Extension Hooks

### Hook 1: `has_permission` - Controller Permission Check

**Purpose**: Implement custom document-level permission logic that cannot be expressed through role permissions or user permissions.

**Location**: In your doctype's `.py` file or registered in `hooks.py`

**Signature**:
```python
def has_permission(doc, ptype=None, user=None, debug=False):
    """
    Custom permission check for individual documents.
    
    Args:
        doc: Document instance or document name (string)
        ptype: Permission type being checked (read, write, create, etc.)
        user: User being checked (defaults to current user)
        debug: Enable debug logging
        
    Returns:
        bool or None: 
            - True: Explicitly grant permission
            - False: Explicitly deny permission
            - None: No opinion, continue with other checks
    """
    pass
```

**Important Notes:**
- Return `None` to defer to other permission checks (recommended default)
- Return `False` to explicitly deny permission (overrides role permissions)
- Return `True` to explicitly grant permission (use with caution)
- Controllers can only deny permissions, not grant new ones that weren't already present via roles

**Example: Allow access only to document owner**
```python
# In your_doctype/your_doctype.py
def has_permission(doc, ptype=None, user=None, debug=False):
    """Only allow owner to access this document."""
    if not user:
        user = frappe.session.user
        
    # Allow if user is the owner
    if doc.owner == user:
        return True
        
    # Deny access to others
    return False
```

**Example: Allow managers to access team documents**
```python
def has_permission(doc, ptype=None, user=None, debug=False):
    """Allow managers to access their team's documents."""
    if not user:
        user = frappe.session.user
    
    # Get user's team
    user_team = frappe.db.get_value("User", user, "team")
    
    # Allow if document belongs to user's team
    if doc.team == user_team:
        return None  # Defer to role permissions
        
    # Check if user is a manager with access to all teams
    if "Team Manager" in frappe.get_roles(user):
        return None  # Defer to role permissions
    
    # Otherwise deny
    return False
```

**Registration in hooks.py:**
```python
has_permission = {
    "Your DocType": "your_app.your_module.your_doctype.has_permission",
    "*": "your_app.permissions.global_permission_check",  # Applied to all doctypes
}
```

### Hook 2: `permission_query_conditions` - List View Filtering and Document Access

**Purpose**: Return SQL WHERE conditions to filter documents in list views, reports, and database queries. These conditions are also checked within `has_permission()` when verifying read/select access to individual documents.

**Location**: In your doctype's `.py` file or registered in `hooks.py`

**Signature**:
```python
def get_permission_query_conditions(user=None, doctype=None):
    """
    Return SQL WHERE conditions to filter queryable documents.
    
    Args:
        user: User being checked (defaults to current user)
        doctype: DocType being queried
        
    Returns:
        str: SQL WHERE clause without the "WHERE" keyword
             Returns empty string "" to allow all documents
             
    Security Note:
        The returned SQL is inserted directly into queries.
        ALWAYS escape user input using frappe.db.escape()
    """
    pass
```

**Important Notes:**
- Return empty string `""` to show all documents (no filtering)
- Always escape dynamic values with `frappe.db.escape()`
- Conditions are combined with AND logic
- Used for **both** list filtering AND individual document access validation
- When `has_permission(doctype, "read", doc)` is called, these conditions are checked against the specific document
- Multiple hooks can be registered and are combined

**Example: Show only documents from user's company**
```python
def get_permission_query_conditions(user=None, doctype=None):
    """Filter documents by user's company.
    
    This will filter list views AND prevent access to individual documents
    from other companies even if user has role permissions.
    """
    if not user:
        user = frappe.session.user
        
    # Administrator sees everything
    if user == "Administrator":
        return ""
    
    # Get user's company
    user_company = frappe.db.get_value("User", user, "company")
    
    if not user_company:
        # No company assigned, show nothing
        return "1=0"
    
    # Escape the company value for SQL safety
    # This condition will be checked both in lists AND when accessing individual docs
    return f"`tabYour DocType`.`company` = {frappe.db.escape(user_company)}"
```

**Important**: When a user tries to open a specific document (e.g., via URL or direct access), `has_permission()` will validate the document against these conditions. If the document doesn't match (e.g., wrong company), access will be denied even if the user has the correct role permissions.

**Example: Show documents based on role and territory**
```python
def get_permission_query_conditions(user=None, doctype=None):
    """Filter documents by territory based on user role."""
    if not user:
        user = frappe.session.user
        
    if user == "Administrator":
        return ""
    
    roles = frappe.get_roles(user)
    
    # Sales managers see everything
    if "Sales Manager" in roles:
        return ""
    
    # Sales users see only their territory
    if "Sales User" in roles:
        user_territory = frappe.db.get_value("User", user, "territory")
        if user_territory:
            return f"`tabSales Order`.`territory` = {frappe.db.escape(user_territory)}"
    
    # Default: show nothing
    return "1=0"
```

**Example: Complex conditions with multiple criteria**
```python
def get_permission_query_conditions(user=None, doctype=None):
    """Show documents based on status, owner, or team membership."""
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return ""
    
    conditions = []
    
    # Always show published documents
    conditions.append("`tabYour DocType`.`status` = 'Published'")
    
    # Always show own documents
    conditions.append(f"`tabYour DocType`.`owner` = {frappe.db.escape(user)}")
    
    # Show team documents if user has a team
    user_team = frappe.db.get_value("User", user, "team")
    if user_team:
        conditions.append(f"`tabYour DocType`.`team` = {frappe.db.escape(user_team)}")
    
    # Combine with OR logic (at least one condition must be true)
    return "(" + " OR ".join(conditions) + ")"
```

**Registration in hooks.py:**
```python
permission_query_conditions = {
    "Your DocType": "your_app.your_module.your_doctype.get_permission_query_conditions",
    "*": "your_app.permissions.global_query_conditions",  # Applied to all doctypes
}
```

### Hook 3: `write_permission_query_conditions` - Post-Write Validation

**Purpose**: Validate that saved/updated documents satisfy custom conditions before committing to database.

**Location**: In your doctype's `.py` file or registered in `hooks.py`

**Signature**:
```python
def get_write_permission_query_conditions(user=None, doctype=None, permtype="write"):
    """
    Return SQL WHERE conditions to validate written documents.
    
    Args:
        user: User performing the operation
        doctype: DocType being written
        permtype: Type of operation (create, write, submit, cancel, delete)
        
    Returns:
        str: SQL WHERE clause without the "WHERE" keyword
             Returns empty string "" to allow all operations
             
    Security Note:
        Checked AFTER database write but BEFORE commit.
        Used to validate the operation is allowed.
        If validation fails, transaction is rolled back.
    """
    pass
```

**Important Notes:**
- Called after DB write but before commit
- If check fails, transaction is rolled back
- Used for write operations: create, write, submit, cancel, delete
- When checking create/submit/cancel/delete, also checks "write" conditions
- Always escape dynamic values with `frappe.db.escape()`

**Example: Prevent editing documents outside user's region**
```python
def get_write_permission_query_conditions(user=None, doctype=None, permtype="write"):
    """Only allow editing documents from user's region."""
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return ""
    
    # Only apply to write operations
    if permtype not in ("write", "create"):
        return ""
    
    user_region = frappe.db.get_value("User", user, "region")
    if not user_region:
        return "1=0"  # No region assigned, deny all writes
    
    return f"`tabYour DocType`.`region` = {frappe.db.escape(user_region)}"
```

**Example: Prevent deletion of finalized documents**
```python
def get_write_permission_query_conditions(user=None, doctype=None, permtype="write"):
    """Prevent deletion of finalized documents."""
    if not user:
        user = frappe.session.user
    
    if user == "Administrator":
        return ""
    
    # Only restrict delete operations
    if permtype == "delete":
        # Cannot delete finalized documents
        return "`tabYour DocType`.`status` != 'Finalized'"
    
    return ""
```

**Registration in hooks.py:**
```python
write_permission_query_conditions = {
    "Your DocType": "your_app.your_module.your_doctype.get_write_permission_query_conditions",
}
```

### Hook 4: Server Scripts - Permission Query

**Purpose**: Define permission query conditions using Server Scripts (Python code in the UI).

**Location**: Created through Frappe UI at `/app/server-script`

**Script Type**: "Permission Query"

**Example Server Script:**
```python
# Server Script Name: Your DocType Permission Query
# Script Type: Permission Query
# DocType: Your DocType

# The script should return a SQL WHERE condition
conditions = []

# Show documents from user's department
user_dept = frappe.db.get_value("User", user, "department")
if user_dept:
    conditions.append(f"`tabYour DocType`.`department` = {frappe.db.escape(user_dept)}")

# Managers see all departments
if "Manager" in frappe.get_roles(user):
    return ""  # Empty condition = show all

# Return combined conditions
return " AND ".join(conditions) if conditions else "1=0"
```

**Notes:**
- Available variables: `user`, `doctype`
- Must return a string with SQL WHERE condition
- Automatically integrated with permission query flow
- Useful for rapid prototyping before moving to code

### Hook 5: `has_website_permission` - Website/Portal Access

**Purpose**: Control access to documents on the website/portal (not desk).

**Location**: In your doctype's `.py` file or registered in `hooks.py`

**Signature**:
```python
def has_website_permission(doc, ptype="read", user=None):
    """
    Check if a website/portal user can access this document.
    
    Args:
        doc: Document instance
        ptype: Permission type (usually "read" for portal)
        user: User being checked (portal user)
        
    Returns:
        bool: True if user can access, False otherwise
    """
    pass
```

**Example: Allow customers to view their own orders**
```python
def has_website_permission(doc, ptype="read", user=None):
    """Allow customers to view only their own orders on portal."""
    if not user:
        user = frappe.session.user
    
    # Get the customer linked to this user
    customer = frappe.db.get_value("Contact", {"user": user}, "parent_name")
    
    # Allow if this order belongs to the customer
    return doc.customer == customer
```

**Example: Allow access based on document status**
```python
def has_website_permission(doc, ptype="read", user=None):
    """Only show published content on website."""
    return doc.published == 1
```

**Registration in hooks.py:**
```python
has_website_permission = {
    "Your DocType": "your_app.your_module.your_doctype.has_website_permission"
}
```

**Notes:**
- Only applies to website/portal access, not desk
- Website users are typically customers, suppliers, or other external users
- Use this for portal pages where documents are displayed to external users

## User Permissions

User Permissions restrict access to specific document values for link fields.

**Creating User Permissions programmatically:**
```python
from frappe.permissions import add_user_permission

add_user_permission(
    doctype="Company",           # DocType to restrict
    name="Company A",            # Specific document
    user="user@example.com",     # User to apply restriction to
    applicable_for="Sales Order", # Optional: Apply only to this doctype
    is_default=1,                # Optional: Make this the default value
    hide_descendants=0,          # Optional: For tree doctypes
    ignore_permissions=True      # Optional: Bypass permission checks
)
```

**How User Permissions Work:**
1. Checked after role permissions but before share permissions
2. Applied to the document itself if doctype matches
3. Applied to all link fields pointing to restricted doctypes
4. If `apply_strict_user_permissions` is enabled, even empty link fields are checked
5. "if_owner" permissions take precedence when user is the document owner

**Example Use Cases:**
- Restrict sales users to their own territory
- Limit employees to their branch/department
- Restrict warehouse access by location
- Multi-company access control

## Share Permissions

Documents can be explicitly shared with specific users:

```python
# Share a document
frappe.share.add(
    doctype="Sales Order",
    name="SO-0001",
    user="user@example.com",
    read=1,
    write=1,
    share=0,
    submit=0,
    notify=1
)

# Check if shared
is_shared = frappe.share.get_shared(
    doctype="Sales Order",
    user="user@example.com",
    rights=["read"],
    filters=[["share_name", "=", "SO-0001"]]
)
```

**Notes:**
- Can be disabled globally via System Settings
- Only applicable for: read, write, share, submit, email, print
- Checked after role and user permissions
- Share permission is managed via "DocShare" doctype

## Permission Levels

Permission levels provide field-level access control within a document.

**How it works:**
1. Each field can have a permlevel (0, 1, 2, etc.)
2. Users must have role permission with that permlevel to see/edit the field
3. Permlevel 0 is default and always checked
4. Higher permlevels are for sensitive fields (e.g., pricing, margins, internal notes)

**Example DocType with Permission Levels:**
```python
# Sales Order has fields with different permlevels:
# - customer, items, delivery_date = permlevel 0 (everyone can see)
# - discount_percentage = permlevel 1 (only sales managers)
# - internal_notes = permlevel 2 (only directors)
```

**Checking Permission Level Access:**
```python
# Get which permlevels a user can access
meta = frappe.get_meta("Sales Order")
accessible_permlevels = meta.get_permlevel_access("read", user="user@example.com")
# Returns: [0, 1]  (user can access permlevel 0 and 1, but not 2)
```

**Use Cases:**
- Hide pricing from warehouse staff
- Hide internal notes from customers on portal
- Restrict cost fields to finance team
- Show different fields based on role hierarchy

## Best Practices

### Security

1. **Always Escape User Input**: When building SQL conditions, use `frappe.db.escape()`
   ```python
   # WRONG - SQL injection vulnerability
   return f"`tabDoc`.`owner` = '{user}'"
   
   # CORRECT - Properly escaped
   return f"`tabDoc`.`owner` = {frappe.db.escape(user)}"
   ```

2. **Fail Secure**: Default to denying access when in doubt
   ```python
   # If no conditions match, deny access
   return "1=0"  # SQL condition that's always false
   ```

3. **Validate Hook Returns**: Ensure hooks return expected types
   ```python
   # has_permission should return bool or None
   # permission_query_conditions should return string
   ```

4. **Test Permission Boundaries**: Test with users having minimal permissions

5. **Avoid Side Effects**: Permission checks should be read-only, no database modifications

### Performance

1. **Optimize SQL Conditions**: Use indexed columns in WHERE clauses
   ```python
   # Better - uses indexed field
   return f"`tabDoc`.`company` = {frappe.db.escape(company)}"
   
   # Slower - function on indexed field
   return f"DATE(`tabDoc`.`creation`) = CURDATE()"
   ```

2. **Cache User Data**: Cache frequently accessed user properties
   ```python
   @frappe.whitelist()
   def get_permission_query_conditions(user=None):
       # Cache user's company
       user_company = frappe.cache.hget("user_companies", user, 
           lambda: frappe.db.get_value("User", user, "company"))
       return f"`tabDoc`.`company` = {frappe.db.escape(user_company)}"
   ```

3. **Minimize Hook Complexity**: Keep permission logic simple and fast

4. **Use Appropriate Hooks**: 
   - Use `permission_query_conditions` for list filtering
   - Use `has_permission` for complex document-specific logic

### Maintainability

1. **Document Permission Logic**: Add docstrings explaining the rules
   ```python
   def has_permission(doc, ptype, user):
       """
       Permission Rules:
       - Owners can always read/write their documents
       - Managers can read all documents in their department
       - Directors can read/write all documents
       """
       pass
   ```

2. **Separate Concerns**: Keep permission logic separate from business logic

3. **Use Constants**: Define permission-related constants
   ```python
   MANAGER_ROLES = ["Sales Manager", "Purchase Manager"]
   READONLY_STATUSES = ["Approved", "Finalized"]
   ```

4. **Consistent Return Values**: Be explicit about what you're returning
   ```python
   # Clear intent
   if is_manager:
       return None  # Defer to role permissions
   else:
       return False  # Explicitly deny
   ```

5. **Version Control**: Track permission changes in git with clear commit messages

## Debugging Permissions

### Enable Debug Mode

```python
# In Python
result = frappe.has_permission("DocType", "read", doc, debug=True)
# Logs will show the permission evaluation flow

# Or enable globally
frappe.conf.developer_mode = 1
```

### Check Permission Debug Logs

```python
# After permission check with debug=True
logs = frappe.local.permission_debug_log
for log in logs:
    print(log)
```

### Test Permissions as Different User

```python
# Temporarily switch user
frappe.set_user("test@example.com")
try:
    has_perm = frappe.has_permission("Sales Order", "read", doc)
    print(f"Has permission: {has_perm}")
finally:
    frappe.set_user("Administrator")
```

### Inspect Role Permissions

```python
# Get role permissions for a doctype
from frappe.permissions import get_role_permissions
perms = get_role_permissions("Sales Order", user="test@example.com")
print(perms)  # {"read": 1, "write": 0, ...}
```

### Check Permission Query Conditions

```python
# See what SQL conditions are applied
from frappe.model.db_query import DatabaseQuery
query = DatabaseQuery("Sales Order")
conditions = query.get_permission_query_conditions()
print(f"SQL conditions: {conditions}")
```

## Common Issues and Solutions

### Issue 1: User Can't See Documents in List View

**Symptoms:** User has role permission but list view is empty or missing documents

**Possible Causes:**
1. Permission query conditions are too restrictive
2. User permissions are blocking access
3. Share-only access (user can only see explicitly shared documents)

**Solutions:**
```python
# Debug: Check what conditions are being applied
from frappe.model.db_query import DatabaseQuery
query = DatabaseQuery("Your DocType", user="user@example.com")
conditions = query.get_permission_query_conditions()
print(f"Applied conditions: {conditions}")

# Debug: Check user permissions
from frappe.permissions import get_user_permissions
user_perms = get_user_permissions("user@example.com")
print(f"User permissions: {user_perms}")

# Fix: Review and adjust permission_query_conditions hook
# Fix: Clear unnecessary user permissions
from frappe.permissions import clear_user_permissions_for_doctype
clear_user_permissions_for_doctype("Your DocType", "user@example.com")
```

### Issue 2: Can See Document in List but Can't Open

**Symptoms:** Document appears in list view but "You don't have permission" error when opening

**Possible Causes:**
1. Has "select" permission but not "read"
2. `has_permission` hook is denying access
3. Permission query conditions don't match when checking individual document

**Solutions:**
```python
# Debug: Check document permissions
doc = frappe.get_doc("Your DocType", "DOC-001")
perms = frappe.permissions.get_doc_permissions(doc, user="user@example.com")
print(f"Document permissions: {perms}")

# Debug: Enable detailed permission logging
result = frappe.has_permission("Your DocType", "read", doc, 
                                user="user@example.com", debug=True)
# Check logs for details

# Fix: Ensure role has "read" permission, not just "select"
# Fix: Review has_permission hook logic
```

### Issue 3: Permission Query Hook Not Working

**Symptoms:** Hook is registered but documents are still not filtered correctly

**Possible Causes:**
1. Hook not properly registered in hooks.py
2. Syntax error in SQL condition
3. Cache not cleared after hook changes
4. Hook returning None instead of empty string

**Solutions:**
```python
# Verify hook registration
hooks = frappe.get_hooks("permission_query_conditions")
print(f"Registered hooks: {hooks}")

# Test hook directly
from your_app.your_module.your_doctype import get_permission_query_conditions
condition = get_permission_query_conditions(user="user@example.com")
print(f"Returned condition: {condition}")

# Clear cache
frappe.clear_cache()

# Correct hook return value
def get_permission_query_conditions(user):
    # WRONG: returns None
    if some_condition:
        return None
    
    # CORRECT: returns empty string for no restrictions
    if some_condition:
        return ""
    
    return "your_condition"
```

### Issue 4: Write Operations Fail Silently

**Symptoms:** Document saves without error but changes aren't persisted

**Possible Causes:**
1. `write_permission_query_conditions` is failing validation
2. Transaction rollback due to permission check
3. `before_save` hook blocking changes

**Solutions:**
```python
# Debug: Check write permission conditions
from frappe.permissions import check_write_permission_query_conditions
can_write = check_write_permission_query_conditions(doc, permtype="write")
print(f"Can write: {can_write}")

# Enable transaction debugging
frappe.db.rollback()  # Check if this is called unexpectedly

# Fix: Review write_permission_query_conditions hook
# Fix: Ensure conditions match the current state of document
```

### Issue 5: Virtual DocType Permission Issues

**Symptoms:** Permission errors or incorrect filtering on virtual doctypes

**Possible Causes:**
1. Trying to use permission_query_conditions on virtual doctype
2. Custom get_list not implementing permission checks

**Solutions:**
```python
# Virtual doctypes need custom permission handling
class YourVirtualDocType(Document):
    @staticmethod
    def get_list(args):
        # Manually check permissions
        user = frappe.session.user
        if user == "Administrator":
            # Return all documents
            pass
        else:
            # Filter based on custom logic
            pass
        
        return filtered_list
    
    def has_permission(self, ptype="read", user=None):
        # Implement custom permission check
        return True  # or custom logic
```

### Issue 6: Share Permissions Not Working

**Symptoms:** Shared documents not accessible to users

**Possible Causes:**
1. Document sharing disabled in System Settings
2. Wrong permission type specified when sharing
3. User doesn't have System User role

**Solutions:**
```python
# Check if sharing is enabled
sharing_enabled = not frappe.get_system_settings("disable_document_sharing")
print(f"Sharing enabled: {sharing_enabled}")

# Verify share exists
shares = frappe.get_all("DocShare", filters={
    "share_doctype": "Your DocType",
    "share_name": "DOC-001",
    "user": "user@example.com"
})
print(f"Shares: {shares}")

# Check user has System User role
is_system_user = frappe.permissions.is_system_user("user@example.com")
print(f"Is system user: {is_system_user}")
```

### Issue 7: Administrator Not Seeing All Documents

**Symptoms:** Even Administrator can't see certain documents

**Possible Causes:**
1. Filters or conditions applied regardless of user
2. Virtual doctype with custom filtering
3. Data permission errors (documents don't exist)

**Solutions:**
```python
# Verify Administrator check is first in hook
def has_permission(doc, ptype, user):
    # ALWAYS check Administrator first
    if user == "Administrator":
        return True
    
    # Your custom logic
    pass

# Check if documents actually exist
exists = frappe.db.exists("Your DocType", "DOC-001")
print(f"Document exists: {exists}")
```

## Common Patterns

### Pattern 1: Owner-Only Access

```python
def has_permission(doc, ptype, user):
    """Only document owner can access."""
    return doc.owner == user
```

### Pattern 2: Role-Based Region Filtering

```python
def get_permission_query_conditions(user):
    """Filter by user's region unless user is a manager."""
    if "Regional Manager" in frappe.get_roles(user):
        return ""  # See all regions
    
    user_region = frappe.db.get_value("User", user, "region")
    return f"`tabDoc`.`region` = {frappe.db.escape(user_region)}"
```

### Pattern 3: Hierarchical Access (Team/Department)

```python
def has_permission(doc, ptype, user):
    """Allow access to documents in user's team hierarchy."""
    user_teams = get_user_team_hierarchy(user)
    return doc.team in user_teams
```

### Pattern 4: Status-Based Restrictions

```python
def has_permission(doc, ptype, user):
    """Restrict write access to draft documents."""
    if ptype in ("write", "delete") and doc.status != "Draft":
        # Only admins can modify non-draft documents
        return user == "Administrator"
    return None
```

### Pattern 5: Time-Based Access

```python
def get_permission_query_conditions(user):
    """Show only documents from current fiscal year."""
    from frappe.utils import get_fiscal_year
    
    fy = get_fiscal_year(frappe.utils.today())[0]
    fy_start, fy_end = frappe.db.get_value(
        "Fiscal Year", fy, ["year_start_date", "year_end_date"]
    )
    
    return f"`tabDoc`.`posting_date` BETWEEN {frappe.db.escape(fy_start)} AND {frappe.db.escape(fy_end)}"
```

### Pattern 6: Multi-Tenant Access

```python
def get_permission_query_conditions(user):
    """Multi-company access control."""
    allowed_companies = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Company"},
        pluck="for_value"
    )
    
    if not allowed_companies:
        return "1=0"  # No companies assigned
    
    companies_str = ", ".join([frappe.db.escape(c) for c in allowed_companies])
    return f"`tabDoc`.`company` IN ({companies_str})"
```

### Pattern 7: Permission Level Filtering

```python
def has_permission(doc, ptype, user):
    """Restrict edit access to sensitive fields based on role."""
    if ptype in ("write", "submit"):
        # Check if user has access to permlevel 1 (pricing fields)
        meta = frappe.get_meta(doc.doctype)
        accessible_permlevels = meta.get_permlevel_access(ptype, user=user)
        
        # If pricing fields were modified, check access
        if doc.has_value_changed("discount_percentage"):
            if 1 not in accessible_permlevels:
                frappe.throw("You don't have permission to modify pricing")
    
    return None
```

### Pattern 8: Child Table Permissions

```python
# In parent doctype
def has_permission(doc, ptype, user):
    """Control access to sensitive child tables."""
    if ptype == "write":
        # Check if user can edit the cost details child table
        meta = frappe.get_meta(doc.doctype)
        cost_field = meta.get_field("cost_details")
        
        if cost_field.permlevel > 0:
            accessible_permlevels = meta.get_permlevel_access("write", user=user)
            if cost_field.permlevel not in accessible_permlevels:
                # User can edit document but not cost details
                doc.flags.ignore_children_type = ["Cost Details"]
    
    return None
```

### Pattern 9: Conditional Field Visibility

```python
def has_permission(doc, ptype, user):
    """Hide certain fields based on document status and user role."""
    if ptype == "read":
        roles = frappe.get_roles(user)
        
        # Hide internal comments from external users
        if "Customer" in roles and doc.status != "Completed":
            doc.internal_comments = None
        
        # Hide cost fields from non-finance users
        if "Accounts User" not in roles:
            doc.total_cost = None
            doc.profit_margin = None
    
    return None
```

### Pattern 10: Combined Role and Territory Access

```python
def get_permission_query_conditions(user):
    """Complex filtering based on role hierarchy and territory."""
    roles = frappe.get_roles(user)
    
    # Sales Directors see everything
    if "Sales Director" in roles:
        return ""
    
    conditions = []
    
    # Sales Managers see their region
    if "Sales Manager" in roles:
        user_region = frappe.db.get_value("User", user, "region")
        if user_region:
            conditions.append(f"`tabSales Order`.`region` = {frappe.db.escape(user_region)}")
    
    # Sales Users see only their territory within their region
    if "Sales User" in roles:
        user_territory = frappe.db.get_value("User", user, "territory")
        if user_territory:
            conditions.append(f"`tabSales Order`.`territory` = {frappe.db.escape(user_territory)}")
    
    # Always show own documents
    conditions.append(f"`tabSales Order`.`owner` = {frappe.db.escape(user)}")
    
    # Combine with OR logic
    return "(" + " OR ".join(conditions) + ")" if conditions else "1=0"
```

## Testing Permission Hooks

### Unit Tests for Permissions

```python
# In test_your_doctype.py
from frappe.tests.utils import FrappeTestCase
from frappe.permissions import add_user_permission, clear_user_permissions_for_doctype

class TestYourDocTypePermissions(FrappeTestCase):
    def setUp(self):
        # Create test users and assign roles
        self.test_user = "test@example.com"
        if not frappe.db.exists("User", self.test_user):
            user = frappe.get_doc({
                "doctype": "User",
                "email": self.test_user,
                "first_name": "Test"
            })
            user.add_roles("Sales User")
            user.insert(ignore_permissions=True)
    
    def tearDown(self):
        # Clean up user permissions
        clear_user_permissions_for_doctype("Company", self.test_user)
    
    def test_user_can_access_own_company_documents(self):
        """Test user can access documents from their company."""
        # Add user permission for Company A
        add_user_permission("Company", "Company A", self.test_user)
        
        # Create test document
        doc = frappe.get_doc({
            "doctype": "Your DocType",
            "company": "Company A",
            "title": "Test Doc"
        })
        doc.insert(ignore_permissions=True)
        
        # Check permission
        frappe.set_user(self.test_user)
        self.assertTrue(frappe.has_permission("Your DocType", "read", doc))
        frappe.set_user("Administrator")
    
    def test_user_cannot_access_other_company_documents(self):
        """Test user cannot access documents from other companies."""
        add_user_permission("Company", "Company A", self.test_user)
        
        doc = frappe.get_doc({
            "doctype": "Your DocType",
            "company": "Company B",  # Different company
            "title": "Test Doc"
        })
        doc.insert(ignore_permissions=True)
        
        frappe.set_user(self.test_user)
        self.assertFalse(frappe.has_permission("Your DocType", "read", doc))
        frappe.set_user("Administrator")
    
    def test_permission_query_conditions(self):
        """Test permission query conditions filter list views."""
        add_user_permission("Company", "Company A", self.test_user)
        
        # Create documents in different companies
        for company in ["Company A", "Company B"]:
            frappe.get_doc({
                "doctype": "Your DocType",
                "company": company,
                "title": f"Doc in {company}"
            }).insert(ignore_permissions=True)
        
        # Check filtered list
        frappe.set_user(self.test_user)
        docs = frappe.get_all("Your DocType", fields=["company"])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].company, "Company A")
        frappe.set_user("Administrator")
```

## Migration Guide: Adding Permissions to Existing DocTypes

### Step 1: Plan Permission Rules

Document your permission requirements:
- Who should access what documents?
- Are there different levels of access (read vs write)?
- Should access be based on role, user, or document fields?
- Are there any time-based or status-based restrictions?

### Step 2: Implement Permission Hooks

Choose the appropriate hook(s):

```python
# For list view filtering
def get_permission_query_conditions(user=None, doctype=None):
    # Return SQL WHERE conditions
    pass

# For document-level checks
def has_permission(doc, ptype=None, user=None, debug=False):
    # Return bool or None
    pass
```

### Step 3: Register Hooks

Add to `hooks.py`:

```python
permission_query_conditions = {
    "Your DocType": "your_app.your_module.your_doctype.get_permission_query_conditions"
}

has_permission = {
    "Your DocType": "your_app.your_module.your_doctype.has_permission"
}
```

### Step 4: Test Thoroughly

- Test with different roles
- Test with user permissions
- Test list views and individual document access
- Test write operations
- Test edge cases (empty values, special users)

### Step 5: Document Changes

- Update developer documentation
- Add comments to permission functions
- Create user-facing documentation if needed

## References

### Core Files
- `/frappe/permissions.py` - Main permission system
- `/frappe/model/db_query.py` - Permission query integration
- `/frappe/model/document.py` - Document lifecycle and permission checks
- `/frappe/core/doctype/user_permission/` - User permission management

### Example Implementations
- `/frappe/core/doctype/file/file.py` - File access permissions
- `/frappe/core/doctype/communication/communication.py` - Communication permissions
- `/frappe/desk/doctype/event/event.py` - Event sharing and ownership
- `/frappe/contacts/address_and_contact.py` - Contact permissions

### Testing
- `/frappe/tests/test_permissions.py` - Permission system tests
- `/frappe/core/doctype/user_permission/test_user_permission.py` - User permission tests

## Additional Resources

- [Frappe Permissions Documentation](https://frappeframework.com/docs/user/en/api/permissions)
- [DocType Permission Manager](https://frappeframework.com/docs/user/en/basics/users-and-permissions)
- [User Permissions Guide](https://frappeframework.com/docs/user/en/basics/users-and-permissions/user-permissions)
