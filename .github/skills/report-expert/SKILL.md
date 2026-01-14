---
name: report-expert
description: Expert guidance on Frappe reports including report types, structure, creation workflow, and best practices. Use when creating standard script reports, query reports, understanding report structure, working with columns and filters, or troubleshooting report-related issues.
---

# Frappe Report Expert

This skill provides comprehensive guidance for working with Frappe reports, their structure, creation workflow, and best practices.

## Overview

Frappe provides a powerful reporting framework with multiple report types for different use cases:

- **Report Builder**: Visual report builder without code (uses DocType fields)
- **Query Report**: SQL-based reports with direct database queries
- **Script Report**: Python-based reports with full programmatic control (most flexible)
- **Custom Report**: Customized version of an existing report

This skill focuses primarily on **Script Reports** as they are the most commonly created programmatically and offer the most flexibility.

## Quick Reference

### Report Types Comparison

| Report Type | Code Required | Use Case | Flexibility |
|-------------|---------------|----------|-------------|
| Report Builder | None | Simple reports from DocType fields | Low |
| Query Report | SQL only | Database-driven reports, joins | Medium |
| Script Report | Python + JS | Complex logic, calculations, custom data | High |
| Custom Report | None | Saved customization of existing report | N/A |

### Standard Script Report Structure

Every Script Report consists of three files:

```
{module}/report/{report_name}/
├── __init__.py (empty)
├── {report_name}.json (metadata)
├── {report_name}.py (execute function)
└── {report_name}.js (filters and client-side logic)
```

## Core Concepts

### The Report Metadata (.json file)

Required fields in the JSON file:

```json
{
  "report_name": "My Report",
  "ref_doctype": "DocType Name",
  "report_type": "Script Report",
  "is_standard": "Yes",
  "module": "Module Name",
  "disabled": 0,
  "add_total_row": 0,
  "roles": [
    {"role": "System Manager"}
  ]
}
```

**Key properties:**
- `report_name`: Display name of the report
- `ref_doctype`: The primary DocType this report relates to (required)
- `report_type`: One of "Report Builder", "Query Report", "Script Report", "Custom Report"
- `is_standard`: "Yes" for app-bundled reports, "No" for custom reports
- `module`: The module this report belongs to
- `add_total_row`: Set to 1 to automatically add a total row at the bottom
- `roles`: Array of roles that can access this report

### The Execute Function (.py file)

The Python file must contain an `execute(filters=None)` function:

```python
def execute(filters=None):
    columns, data = [], []
    # Your logic here
    return columns, data
```

**Return value:**
- Returns a tuple: `(columns, data)` or extended `(columns, data, message, chart, report_summary, skip_total_row)`
- `columns`: List of column definitions
- `data`: List of rows (each row is a list or dict)
- `message` (optional): String message to display
- `chart` (optional): Chart configuration dict
- `report_summary` (optional): Summary statistics list
- `skip_total_row` (optional): Boolean to skip total row

### Column Format

Columns can be defined as strings or dictionaries:

**String format (concise):**
```python
columns = [
    "ID:Link/DocType:100",           # Label:Fieldtype/Options:Width
    "Name:Data:150",                  # Label:Fieldtype:Width
    "Amount:Currency:120",            # Label:Fieldtype:Width
    "Date:Date",                      # Label:Fieldtype (default width)
]
```

**Dictionary format (detailed):**
```python
columns = [
    {
        "label": "ID",
        "fieldname": "id",
        "fieldtype": "Link",
        "options": "DocType",
        "width": 100
    },
    {
        "label": "Amount",
        "fieldname": "amount",
        "fieldtype": "Currency",
        "width": 120
    }
]
```

**Common fieldtypes for columns:**
- Data, Text, Int, Float, Currency, Percent
- Date, Datetime, Time
- Link (requires `options`), Dynamic Link
- Check (checkbox)

### Data Format

Data rows can be lists or dictionaries:

**List format (matches column order):**
```python
data = [
    ["ID-001", "John Doe", 1000, "2024-01-01"],
    ["ID-002", "Jane Smith", 2000, "2024-01-02"],
]
```

**Dictionary format (uses fieldnames):**
```python
data = [
    {"id": "ID-001", "name": "John Doe", "amount": 1000, "date": "2024-01-01"},
    {"id": "ID-002", "name": "Jane Smith", "amount": 2000, "date": "2024-01-02"},
]
```

### Filters (.js file)

The JavaScript file defines filters shown to users:

```javascript
frappe.query_reports["Report Name"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_user_default("Company")
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today()
        }
    ]
};
```

**Filter properties:**
- `fieldname`: Internal name (used in Python `filters` dict)
- `label`: Display label
- `fieldtype`: Field type (Link, Date, Select, Check, etc.)
- `options`: For Link/Select fields
- `reqd`: Set to 1 for required filters
- `default`: Default value
- `get_query`: Function to filter Link field options

## Creating a New Script Report

### Step 1: Create Report via Desk (Standard Reports)

For standard reports (shipped with apps):

1. Navigate to Report DocType list
2. Create new Report document
3. Set:
   - Report Name: "My Report"
   - Report Type: "Script Report"
   - Ref DocType: Select primary DocType
   - Module: Select module
   - Is Standard: "Yes"
4. Save

The framework automatically creates boilerplate files at:
```
{app}/{module}/report/{report_name}/
├── __init__.py
├── {report_name}.json
├── {report_name}.py
└── {report_name}.js
```

### Step 2: Implement the Execute Function

Edit `{report_name}.py`:

```python
# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        _("ID") + ":Link/DocType:120",
        _("Name") + ":Data:150",
        _("Amount") + ":Currency:120",
        _("Date") + ":Date:100",
    ]

def get_data(filters):
    # Your data fetching logic
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            name,
            title,
            total_amount,
            posting_date
        FROM `tabDocType`
        WHERE docstatus = 1 {conditions}
        ORDER BY posting_date DESC
    """.format(conditions=conditions), filters, as_list=1)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("company"):
        conditions += " AND company = %(company)s"
    
    if filters.get("from_date"):
        conditions += " AND posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND posting_date <= %(to_date)s"
    
    return conditions
```

### Step 3: Define Filters

Edit `{report_name}.js`:

```javascript
// Copyright (c) 2024, Your Company and contributors
// For license information, please see license.txt

frappe.query_reports["My Report"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company")
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        }
    ]
};
```

### Step 4: Test the Report

1. Run `bench migrate` to sync changes
2. Navigate to the report: `/app/query-report/My Report`
3. Apply filters and verify data

## Advanced Features

### Adding Charts

Return a chart configuration as the 4th element:

```python
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    
    return columns, data, None, chart

def get_chart_data(data):
    return {
        "data": {
            "labels": ["Jan", "Feb", "Mar"],
            "datasets": [
                {
                    "name": "Revenue",
                    "values": [100, 200, 300]
                }
            ]
        },
        "type": "line",  # line, bar, pie, percentage
        "height": 300
    }
```

### Adding Report Summary

Show key metrics at the top:

```python
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    # Calculate summary
    total_amount = sum(row[2] for row in data)
    count = len(data)
    
    report_summary = [
        {
            "value": count,
            "label": "Total Records",
            "datatype": "Int"
        },
        {
            "value": total_amount,
            "label": "Total Amount",
            "datatype": "Currency"
        }
    ]
    
    return columns, data, None, None, report_summary
```

### Custom Buttons and Actions

Add custom buttons in the JS file:

```javascript
frappe.query_reports["My Report"] = {
    filters: [...],
    
    onload: function(report) {
        report.page.add_inner_button(__("Export"), function() {
            // Custom export logic
            frappe.call({
                method: "your_app.reports.my_report.export_data",
                args: {
                    filters: report.get_filter_values()
                },
                callback: function(r) {
                    // Handle response
                }
            });
        });
    }
};
```

### Tree Reports

For hierarchical data:

```python
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data, None, None, None, None, True  # Last param enables tree view
```

Data should include `indent` and `parent_account` fields for tree structure.

### Permissions

**Access control:**
```python
def execute(filters=None):
    # Restrict to specific role
    frappe.only_for("System Manager")
    
    # Or check permission
    if not frappe.has_permission("DocType", "read"):
        frappe.throw("Insufficient permissions")
    
    columns, data = get_columns(), get_data(filters)
    return columns, data
```

### Query Optimization

**Best practices:**

1. **Use proper indexing**: Filter on indexed fields
2. **Limit data**: Add LIMIT clause for large datasets
3. **Avoid SELECT ***: Select only needed columns
4. **Use `frappe.get_list()`** for simple queries:
   ```python
   data = frappe.get_list(
       "DocType",
       fields=["name", "title", "amount"],
       filters={"status": "Active"},
       order_by="creation desc"
   )
   ```

5. **Cache expensive operations**:
   ```python
   @frappe.whitelist()
   def get_cached_data():
       return frappe.cache().get_value(
           "my_report_data",
           generator=lambda: fetch_data()
       )
   ```

## Common Patterns

### Pattern 1: Simple List Report

```python
def execute(filters=None):
    return get_columns(), get_data(filters)

def get_columns():
    return [
        "Name:Link/DocType:150",
        "Status:Data:100",
        "Amount:Currency:120"
    ]

def get_data(filters):
    return frappe.get_list(
        "DocType",
        fields=["name", "status", "amount"],
        filters=filters
    )
```

### Pattern 2: Report with Calculations

```python
def execute(filters=None):
    columns = get_columns()
    raw_data = fetch_raw_data(filters)
    data = process_data(raw_data)
    
    return columns, data

def process_data(raw_data):
    processed = []
    for row in raw_data:
        # Calculate additional fields
        total = row.qty * row.rate
        tax = total * 0.18
        grand_total = total + tax
        
        processed.append([
            row.name,
            row.qty,
            row.rate,
            total,
            tax,
            grand_total
        ])
    return processed
```

### Pattern 3: Multi-Level Grouping

```python
def execute(filters=None):
    columns = get_columns()
    data = get_grouped_data(filters)
    
    return columns, data

def get_grouped_data(filters):
    from itertools import groupby
    
    raw_data = fetch_data(filters)
    data = []
    
    for company, company_rows in groupby(raw_data, key=lambda x: x.company):
        # Add company header
        data.append({
            "company": company,
            "indent": 0,
            "is_group": 1
        })
        
        # Add detail rows
        for row in company_rows:
            data.append({
                "item": row.item_name,
                "qty": row.qty,
                "amount": row.amount,
                "indent": 1
            })
    
    return data
```

### Pattern 4: Dynamic Columns

```python
def execute(filters=None):
    columns = get_dynamic_columns(filters)
    data = get_data(filters)
    
    return columns, data

def get_dynamic_columns(filters):
    columns = ["Item:Link/Item:150"]
    
    # Add date columns dynamically
    date_list = get_date_range(filters.from_date, filters.to_date)
    for date in date_list:
        columns.append(f"{date}:Float:100")
    
    return columns
```

## Best Practices

### Code Organization

1. **Separate concerns**: Use helper functions for columns, data, conditions
2. **Use meaningful names**: `get_columns()`, `get_data()`, `get_conditions()`
3. **Add docstrings**: Document complex logic
4. **Handle None filters**: Always check `filters.get(key)` not `filters[key]`

### Performance

1. **Filter early**: Apply filters in SQL WHERE clause, not in Python
2. **Paginate large datasets**: Use LIMIT and OFFSET
3. **Use database efficiently**: Minimize queries, use JOINs appropriately
4. **Cache when possible**: Cache expensive calculations

### User Experience

1. **Provide sensible defaults**: Set default filter values
2. **Add helpful messages**: Use the `message` return value for guidance
3. **Use appropriate column widths**: Make reports readable
4. **Add translations**: Wrap labels in `_()` or `__()`
5. **Sort logically**: Order data in a meaningful way

### Security

1. **Validate permissions**: Check user access with `frappe.only_for()` or `frappe.has_permission()`
2. **Sanitize inputs**: Validate filter values
3. **Use parameterized queries**: Never concatenate user input into SQL
4. **Respect row-level permissions**: Use `frappe.get_list()` which respects permissions

## Troubleshooting

### Report not showing up
- Check if report is disabled
- Verify user has required role
- Check ref_doctype permissions
- Run `bench migrate` to sync

### Data not displaying correctly
- Verify column count matches data row length
- Check fieldtype matches data type
- Ensure fieldnames are correct (for dict format)

### Filter not working
- Check fieldname matches in JS and Python
- Verify filter value is being passed correctly
- Add debug prints: `frappe.log_error(str(filters))`

### Performance issues
- Add LIMIT clause
- Create database indexes
- Use `frappe.db.sql()` with proper WHERE clause
- Profile slow queries

## Reference Files

For more detailed information:

- **[script-report-examples.md](references/script-report-examples.md)** - Complete working examples of script reports
- **[column-fieldtypes.md](references/column-fieldtypes.md)** - All available column fieldtypes and their usage
- **[filter-types.md](references/filter-types.md)** - Complete filter field types and configurations
- **[advanced-features.md](references/advanced-features.md)** - Charts, summaries, custom buttons, and more

## Boilerplate Generation

When you create a standard Script Report via the desk:

1. Report document is saved to database
2. On save, if `is_standard == "Yes"`:
   - Report JSON is exported to: `{app}/{module}/report/{report_name}/{report_name}.json`
   - Boilerplate files are created via `make_boilerplate()`:
     - `{report_name}.py` - From `frappe/core/doctype/report/boilerplate/controller.py`
     - `{report_name}.js` - From `frappe/core/doctype/report/boilerplate/controller.js`

**Boilerplate templates:**

Python template (`controller.py`):
```python
# Copyright (c) {year}, {app_publisher} and contributors
# For license information, please see license.txt

# import frappe

def execute(filters=None):
    columns, data = [], []
    return columns, data
```

JavaScript template (`controller.js`):
```javascript
// Copyright (c) {year}, {app_publisher} and contributors
// For license information, please see license.txt

frappe.query_reports["{name}"] = {
    "filters": []
};
```

The placeholders `{year}`, `{app_publisher}`, and `{name}` are replaced automatically.

## Related Documentation

- Frappe Framework documentation on reports
- Report Builder documentation
- Query Report SQL guidelines
- DocType permissions for report access control
