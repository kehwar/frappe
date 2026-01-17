# Other Hooks

Additional hooks for various extension points.

## Override Hooks

### override_whitelisted_methods

Override or redirect API methods.

```python
override_whitelisted_methods = {
    "frappe.desk.form.save.savedocs": "my_app.overrides.custom_save",
    "frappe.client.get": "my_app.api.custom_get"
}
```

**Example:**
```python
@frappe.whitelist()
def custom_save(doc, action):
    # Custom save logic
    doc = frappe.get_doc(json.loads(doc))
    
    # Add validation
    validate_document(doc)
    
    # Call original or custom save
    doc.save()
    return doc
```

### override_doctype_class

Replace DocType controller class.

```python
override_doctype_class = {
    "ToDo": "my_app.overrides.CustomToDo"
}
```

**Example:**
```python
# my_app/overrides.py
from frappe.desk.doctype.todo.todo import ToDo

class CustomToDo(ToDo):
    def validate(self):
        super().validate()
        # Custom validation
        if not self.priority:
            self.priority = "Medium"
```

### override_doctype_dashboards

Customize DocType dashboards.

```python
override_doctype_dashboards = {
    "Customer": "my_app.dashboard.get_customer_dashboard"
}
```

**Example:**
```python
def get_customer_dashboard(data):
    # Add custom dashboard data
    data['transactions'].append({
        'label': 'Custom Transactions',
        'items': ['Custom DocType']
    })
    return data
```

## Session Hooks

### on_session_creation

Runs when user session is created.

```python
on_session_creation = [
    "my_app.auth.on_session_creation"
]
```

**Example:**
```python
def on_session_creation(login_manager):
    import frappe
    
    # Log login
    frappe.get_doc({
        "doctype": "Login Log",
        "user": frappe.session.user,
        "timestamp": frappe.utils.now()
    }).insert(ignore_permissions=True)
```

### on_login

Runs after successful login.

```python
on_login = "my_app.auth.on_login"
```

**Example:**
```python
def on_login(login_manager):
    import frappe
    
    # Update last login
    frappe.db.set_value("User", frappe.session.user, 
        "last_login", frappe.utils.now())
    
    # Show welcome message
    frappe.msgprint(f"Welcome, {frappe.session.user}!")
```

### on_logout

Runs when user logs out.

```python
on_logout = "my_app.auth.on_logout"
```

**Example:**
```python
def on_logout(login_manager):
    import frappe
    
    # Cleanup user session data
    cleanup_session_files(frappe.session.user)
```

### auth_hooks

Custom authentication validation.

```python
auth_hooks = [
    "my_app.auth.validate_auth"
]
```

**Example:**
```python
def validate_auth(user, password):
    # Custom authentication logic
    if not is_valid_password_format(password):
        frappe.throw("Password format invalid")
```

## Notification Hook

### notification_config

Configuration for notifications.

```python
notification_config = "my_app.notifications.get_notification_config"
```

**Example:**
```python
def get_notification_config():
    return {
        "for_doctype": {
            "Task": {"status": "Open"},
            "Issue": {"status": "Open"}
        }
    }
```

## Search Hooks

### standard_queries

Custom search queries for link fields.

```python
standard_queries = {
    "Customer": "my_app.queries.customer_query"
}
```

**Example:**
```python
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def customer_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, customer_name, territory
        FROM `tabCustomer`
        WHERE customer_name LIKE %(txt)s
        ORDER BY name
        LIMIT %(start)s, %(page_len)s
    """, {
        'txt': f"%{txt}%",
        'start': start,
        'page_len': page_len
    })
```

### global_search_doctypes

Configure which doctypes appear in global search.

```python
global_search_doctypes = {
    "Sales": [
        {"doctype": "Sales Order"},
        {"doctype": "Customer"}
    ],
    "HR": [
        {"doctype": "Employee"},
        {"doctype": "Leave Application"}
    ]
}
```

## Data Management Hooks

### user_data_fields

Configure GDPR data protection.

```python
user_data_fields = [
    {
        "doctype": "Comment",
        "filter_by": "owner",
        "redact_fields": ["content"]
    },
    {
        "doctype": "Customer",
        "filter_by": "email_id",
        "redact_fields": ["customer_name", "phone"],
        "rename": True
    }
]
```

### ignore_links_on_delete

Skip link validation when deleting.

```python
ignore_links_on_delete = [
    "Comment",
    "Activity Log",
    "Version"
]
```

### auto_cancel_exempted_doctypes

Exempt from automatic cancellation.

```python
auto_cancel_exempted_doctypes = [
    "Auto Repeat",
    "Scheduled Job"
]
```

## Website Hooks

### update_website_context

Add data to website page context.

```python
update_website_context = [
    "my_app.website.update_context"
]
```

**Example:**
```python
def update_context(context):
    # Add custom data to all website pages
    context['custom_footer'] = get_custom_footer()
    context['social_links'] = get_social_links()
```

## Log Management

### default_log_clearing_doctypes

Auto-cleanup old logs.

```python
default_log_clearing_doctypes = {
    "Custom Log": 30,  # Delete after 30 days
    "API Log": 7       # Delete after 7 days
}
```

## PDF Hooks

### pdf_header_html / pdf_footer_html / pdf_body_html

Customize PDF generation.

```python
pdf_header_html = "my_app.utils.pdf.get_header"
pdf_footer_html = "my_app.utils.pdf.get_footer"
```

**Example:**
```python
def get_header(html, kwargs):
    return f"<div class='header'>{kwargs.get('company', '')}</div>"

def get_footer(html, kwargs):
    return f"<div class='footer'>Page {kwargs.get('page', '')}</div>"
```

## Fixture Hook

### fixtures

Export/import data during migrations.

```python
fixtures = [
    "Custom Field",
    "Role",
    {
        "doctype": "Custom Field",
        "filters": [["module", "=", "My App"]]
    }
]
```

Data exported to `fixtures/` directory during `bench export-fixtures`.

## Telemetry Hook

### get_changelog_feed

Provide changelog feed.

```python
get_changelog_feed = "my_app.utils.get_changelog"
```

## Notes

- Most hooks require bench restart
- Override hooks can break core functionality
- Test overrides thoroughly
- Document custom hooks well
- Use sparingly to maintain compatibility
