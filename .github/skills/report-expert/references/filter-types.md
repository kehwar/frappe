# Filter Types Reference

Complete guide to all filter types available in Frappe reports.

## Basic Filter Structure

Filters are defined in the JavaScript file:

```javascript
frappe.query_reports["Report Name"] = {
    filters: [
        {
            fieldname: "filter_name",
            label: __("Display Label"),
            fieldtype: "FieldType",
            options: "Options",  // If applicable
            default: "default_value",
            reqd: 1  // 1 for required, 0 for optional
        }
    ]
};
```

## Common Filter Properties

| Property | Description | Required |
|----------|-------------|----------|
| `fieldname` | Internal name used in Python | Yes |
| `label` | Display label (use `__()` for translation) | Yes |
| `fieldtype` | Type of filter field | Yes |
| `options` | Options for Link/Select fields | Conditional |
| `default` | Default value | No |
| `reqd` | 1 for required, 0 for optional | No |
| `depends_on` | Show filter conditionally | No |
| `get_query` | Function to filter Link options | No |
| `on_change` | Function called when value changes | No |

## Filter Fieldtypes

### Text Filters

**Data**
Single-line text input
```javascript
{
    fieldname: "search",
    label: __("Search"),
    fieldtype: "Data"
}
```

**Text**
Multi-line text input
```javascript
{
    fieldname: "description",
    label: __("Description"),
    fieldtype: "Text"
}
```

### Numeric Filters

**Int**
Integer number input
```javascript
{
    fieldname: "quantity",
    label: __("Minimum Quantity"),
    fieldtype: "Int",
    default: 0
}
```

**Float**
Decimal number input
```javascript
{
    fieldname: "rate",
    label: __("Minimum Rate"),
    fieldtype: "Float"
}
```

**Currency**
Currency input (formatted with currency symbol)
```javascript
{
    fieldname: "amount",
    label: __("Minimum Amount"),
    fieldtype: "Currency"
}
```

### Date Filters

**Date**
Date picker
```javascript
{
    fieldname: "from_date",
    label: __("From Date"),
    fieldtype: "Date",
    default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
    reqd: 1
}
```

**Datetime**
Date and time picker
```javascript
{
    fieldname: "created_on",
    label: __("Created On"),
    fieldtype: "Datetime",
    default: frappe.datetime.now_datetime()
}
```

**Time**
Time picker
```javascript
{
    fieldname: "start_time",
    label: __("Start Time"),
    fieldtype: "Time"
}
```

### Selection Filters

**Select**
Dropdown with predefined options
```javascript
{
    fieldname: "status",
    label: __("Status"),
    fieldtype: "Select",
    options: ["", "Draft", "Submitted", "Cancelled"],
    default: ""
}
```

With dynamic options:
```javascript
{
    fieldname: "priority",
    label: __("Priority"),
    fieldtype: "Select",
    options: "\nLow\nMedium\nHigh",  // Newline-separated string
    default: ""
}
```

### Link Filters

**Link**
Dropdown linked to a DocType
```javascript
{
    fieldname: "customer",
    label: __("Customer"),
    fieldtype: "Link",
    options: "Customer",
    default: frappe.defaults.get_user_default("Customer")
}
```

With filtered options:
```javascript
{
    fieldname: "warehouse",
    label: __("Warehouse"),
    fieldtype: "Link",
    options: "Warehouse",
    get_query: function() {
        return {
            filters: {
                "is_group": 0,
                "company": frappe.query_report.get_filter_value("company")
            }
        };
    }
}
```

**Dynamic Link**
Link field where options depend on another field
```javascript
{
    fieldname: "reference_type",
    label: __("Reference Type"),
    fieldtype: "Link",
    options: "DocType"
},
{
    fieldname: "reference_name",
    label: __("Reference Name"),
    fieldtype: "Dynamic Link",
    get_options: function() {
        let reference_type = frappe.query_report.get_filter_value("reference_type");
        if (!reference_type) {
            frappe.throw(__("Please select Reference Type first"));
        }
        return reference_type;
    }
}
```

### Boolean Filter

**Check**
Checkbox filter
```javascript
{
    fieldname: "include_cancelled",
    label: __("Include Cancelled"),
    fieldtype: "Check",
    default: 0
}
```

### Multi-Select Filter

**MultiSelect**
Select multiple values from a list
```javascript
{
    fieldname: "warehouses",
    label: __("Warehouses"),
    fieldtype: "MultiSelect",
    options: "Warehouse",
    get_data: function(txt) {
        return frappe.db.get_link_options("Warehouse", txt);
    }
}
```

**MultiSelectList**
Enhanced multi-select with checkboxes
```javascript
{
    fieldname: "companies",
    label: __("Companies"),
    fieldtype: "MultiSelectList",
    get_data: function(txt) {
        return frappe.db.get_link_options("Company", txt, {
            "enabled": 1
        });
    }
}
```

## Advanced Filter Features

### Default Values

**Static defaults:**
```javascript
{
    fieldname: "company",
    label: __("Company"),
    fieldtype: "Link",
    options: "Company",
    default: "My Company"
}
```

**Dynamic defaults:**
```javascript
{
    fieldname: "from_date",
    label: __("From Date"),
    fieldtype: "Date",
    default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
}

{
    fieldname: "to_date",
    label: __("To Date"),
    fieldtype: "Date",
    default: frappe.datetime.get_today()
}

{
    fieldname: "fiscal_year",
    label: __("Fiscal Year"),
    fieldtype: "Link",
    options: "Fiscal Year",
    default: frappe.sys_defaults.fiscal_year
}

{
    fieldname: "company",
    label: __("Company"),
    fieldtype: "Link",
    options: "Company",
    default: frappe.defaults.get_user_default("Company")
}
```

### Dependent Filters

Show filter based on another filter's value:

```javascript
{
    fieldname: "report_type",
    label: __("Report Type"),
    fieldtype: "Select",
    options: ["Summary", "Detailed"]
},
{
    fieldname: "group_by",
    label: __("Group By"),
    fieldtype: "Select",
    options: ["Customer", "Item", "Territory"],
    depends_on: "eval:doc.report_type=='Summary'"
}
```

### Conditional Options

Filter Link options based on another filter:

```javascript
{
    fieldname: "company",
    label: __("Company"),
    fieldtype: "Link",
    options: "Company",
    reqd: 1
},
{
    fieldname: "cost_center",
    label: __("Cost Center"),
    fieldtype: "Link",
    options: "Cost Center",
    get_query: function() {
        let company = frappe.query_report.get_filter_value("company");
        return {
            filters: {
                "company": company,
                "is_group": 0
            }
        };
    }
}
```

### On Change Events

Execute code when filter value changes:

```javascript
{
    fieldname: "company",
    label: __("Company"),
    fieldtype: "Link",
    options: "Company",
    on_change: function() {
        // Reset dependent filters
        frappe.query_report.set_filter_value("cost_center", "");
        frappe.query_report.set_filter_value("warehouse", "");
    }
}
```

### Custom Query for Link Fields

Filter Link field options with custom query:

```javascript
{
    fieldname: "customer",
    label: __("Customer"),
    fieldtype: "Link",
    options: "Customer",
    get_query: function() {
        return {
            query: "your_app.queries.get_active_customers",
            filters: {
                "status": "Active"
            }
        };
    }
}
```

Server-side query function:
```python
# In your_app/queries.py
import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_active_customers(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, customer_name
        FROM `tabCustomer`
        WHERE status = 'Active'
            AND ({key} LIKE %(txt)s OR customer_name LIKE %(txt)s)
        ORDER BY
            CASE WHEN name LIKE %(txt)s THEN 0 ELSE 1 END,
            name
        LIMIT %(start)s, %(page_len)s
    """.format(key=searchfield), {
        "txt": "%" + txt + "%",
        "start": start,
        "page_len": page_len
    })
```

## Common Filter Patterns

### Date Range Filters

```javascript
filters: [
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
```

### Company-Based Filters

```javascript
filters: [
    {
        fieldname: "company",
        label: __("Company"),
        fieldtype: "Link",
        options: "Company",
        default: frappe.defaults.get_user_default("Company"),
        reqd: 1
    },
    {
        fieldname: "fiscal_year",
        label: __("Fiscal Year"),
        fieldtype: "Link",
        options: "Fiscal Year",
        default: frappe.sys_defaults.fiscal_year
    }
]
```

### Hierarchical Filters

```javascript
filters: [
    {
        fieldname: "company",
        label: __("Company"),
        fieldtype: "Link",
        options: "Company",
        reqd: 1
    },
    {
        fieldname: "cost_center",
        label: __("Cost Center"),
        fieldtype: "Link",
        options: "Cost Center",
        get_query: function() {
            return {
                filters: {
                    "company": frappe.query_report.get_filter_value("company")
                }
            };
        }
    },
    {
        fieldname: "account",
        label: __("Account"),
        fieldtype: "Link",
        options: "Account",
        get_query: function() {
            return {
                filters: {
                    "company": frappe.query_report.get_filter_value("company")
                }
            };
        }
    }
]
```

### Status Filters

```javascript
filters: [
    {
        fieldname: "status",
        label: __("Status"),
        fieldtype: "Select",
        options: [
            "",
            "Draft",
            "Submitted",
            "Completed",
            "Cancelled"
        ],
        default: ""
    }
]
```

### Multi-Company Filters

```javascript
filters: [
    {
        fieldname: "companies",
        label: __("Companies"),
        fieldtype: "MultiSelectList",
        get_data: function(txt) {
            return frappe.db.get_link_options("Company", txt);
        }
    }
]
```

## Accessing Filter Values

### In Python (execute function)

Filters are passed as a dictionary:

```python
def execute(filters=None):
    # Access filter values
    company = filters.get("company")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    # Check if filter is set
    if filters.get("customer"):
        # Customer filter was provided
        pass
    
    # Use in SQL
    data = frappe.db.sql("""
        SELECT *
        FROM `tabSales Order`
        WHERE company = %(company)s
            AND transaction_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters, as_dict=1)
```

### In JavaScript

```javascript
frappe.query_reports["My Report"] = {
    filters: [...],
    
    onload: function(report) {
        // Get filter value
        let company = frappe.query_report.get_filter_value("company");
        
        // Set filter value
        frappe.query_report.set_filter_value("status", "Active");
        
        // Get all filter values
        let all_filters = report.get_filter_values();
    }
};
```

## Filter Validation

### Client-Side Validation

```javascript
{
    fieldname: "from_date",
    label: __("From Date"),
    fieldtype: "Date",
    reqd: 1,
    on_change: function() {
        let from_date = frappe.query_report.get_filter_value("from_date");
        let to_date = frappe.query_report.get_filter_value("to_date");
        
        if (from_date && to_date && from_date > to_date) {
            frappe.throw(__("From Date cannot be greater than To Date"));
        }
    }
}
```

### Server-Side Validation

```python
def execute(filters=None):
    # Validate required filters
    if not filters.get("company"):
        frappe.throw(_("Company is required"))
    
    # Validate date range
    if filters.get("from_date") and filters.get("to_date"):
        if getdate(filters.from_date) > getdate(filters.to_date):
            frappe.throw(_("From Date cannot be greater than To Date"))
    
    columns, data = get_columns(), get_data(filters)
    return columns, data
```

## Best Practices

1. **Use meaningful fieldnames**: Choose clear, descriptive names
2. **Provide defaults**: Set sensible default values for better UX
3. **Mark required filters**: Use `reqd: 1` for essential filters
4. **Order logically**: Place most important filters first
5. **Use dependent filters**: Hide irrelevant filters based on context
6. **Validate input**: Validate on both client and server side
7. **Filter Link options**: Use `get_query` to show only relevant options
8. **Translate labels**: Always use `__()` for labels
9. **Handle empty filters**: Check `filters.get()` not `filters[]` in Python
10. **Document complex filters**: Add tooltips or help text if needed

## Translation

Always wrap filter labels for translation support:

```javascript
{
    fieldname: "customer",
    label: __("Customer"),  // Translated
    fieldtype: "Link",
    options: "Customer"
}
```

For dynamic text:
```javascript
frappe.throw(__("Please select {0} first", [__("Company")]));
```

## Examples by Report Type

### Financial Report Filters
```javascript
filters: [
    {
        fieldname: "company",
        label: __("Company"),
        fieldtype: "Link",
        options: "Company",
        reqd: 1
    },
    {
        fieldname: "fiscal_year",
        label: __("Fiscal Year"),
        fieldtype: "Link",
        options: "Fiscal Year",
        reqd: 1
    },
    {
        fieldname: "from_date",
        label: __("From Date"),
        fieldtype: "Date",
        reqd: 1
    },
    {
        fieldname: "to_date",
        label: __("To Date"),
        fieldtype: "Date",
        reqd: 1
    },
    {
        fieldname: "cost_center",
        label: __("Cost Center"),
        fieldtype: "Link",
        options: "Cost Center"
    }
]
```

### Inventory Report Filters
```javascript
filters: [
    {
        fieldname: "company",
        label: __("Company"),
        fieldtype: "Link",
        options: "Company",
        default: frappe.defaults.get_user_default("Company")
    },
    {
        fieldname: "warehouse",
        label: __("Warehouse"),
        fieldtype: "Link",
        options: "Warehouse"
    },
    {
        fieldname: "item_group",
        label: __("Item Group"),
        fieldtype: "Link",
        options: "Item Group"
    },
    {
        fieldname: "include_zero_stock",
        label: __("Include Zero Stock"),
        fieldtype: "Check",
        default: 0
    }
]
```

### Sales Report Filters
```javascript
filters: [
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
    },
    {
        fieldname: "customer",
        label: __("Customer"),
        fieldtype: "Link",
        options: "Customer"
    },
    {
        fieldname: "territory",
        label: __("Territory"),
        fieldtype: "Link",
        options: "Territory"
    },
    {
        fieldname: "sales_person",
        label: __("Sales Person"),
        fieldtype: "Link",
        options: "Sales Person"
    }
]
```
