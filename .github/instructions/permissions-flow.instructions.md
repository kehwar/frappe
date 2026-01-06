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

These are SQL conditions applied to database queries for filtering lists and reports:

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

### Hook 2: `permission_query_conditions` - List View Filtering

**Purpose**: Return SQL WHERE conditions to filter documents in list views, reports, and database queries.

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
- Used for read-only filtering (list views, reports)
- Multiple hooks can be registered and are combined

**Example: Show only documents from user's company**
```python
def get_permission_query_conditions(user=None, doctype=None):
    """Filter documents by user's company."""
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
    return f"`tabYour DocType`.`company` = {frappe.db.escape(user_company)}"
```

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
