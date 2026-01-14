# Column Fieldtypes Reference

Complete reference for all available column fieldtypes in Frappe reports.

## String Format

Columns can be defined using a compact string format:

```
"Label:Fieldtype/Options:Width"
```

Examples:
```python
"Name:Data:150"
"Amount:Currency:120"
"Customer:Link/Customer:200"
"Is Active:Check:80"
```

## Dictionary Format

More detailed format with all options:

```python
{
    "label": "Display Label",
    "fieldname": "field_name",
    "fieldtype": "Data",
    "options": "DocType",  # For Link/Select
    "width": 150,
    "precision": 2,  # For numeric types
    "convertible": "qty"  # For currency conversion
}
```

## Available Fieldtypes

### Text Types

**Data**
- Single-line text
- Default width: 100-150px
- Example: `"Name:Data:150"`
```python
{"label": "Name", "fieldname": "name", "fieldtype": "Data", "width": 150}
```

**Text**
- Multi-line text (shows truncated in report)
- Default width: 200px
- Example: `"Description:Text:200"`
```python
{"label": "Description", "fieldname": "description", "fieldtype": "Text", "width": 200}
```

**Small Text**
- Medium-length text
- Default width: 150px
- Example: `"Notes:Small Text:150"`

**Long Text**
- Long text fields
- Similar to Text in reports
- Example: `"Content:Long Text:200"`

**Text Editor**
- Rich text/HTML content (displays as text in reports)
- Default width: 200px
- Example: `"Description:Text Editor:200"`

**HTML Editor**
- HTML formatted content (displays as text in reports)
- Default width: 200px
- Example: `"Content:HTML Editor:200"`

**Markdown Editor**
- Markdown formatted content (displays as text in reports)
- Default width: 200px
- Example: `"Notes:Markdown Editor:200"`

**Code**
- For code snippets or formatted text
- Displays in monospace font
- Example: `"Script:Code:200"`

**Password**
- Encrypted/masked text field
- Displays as masked in reports
- Example: `"API Key:Password:150"`

**Read Only**
- Display-only computed field
- Example: `"Status:Read Only:100"`

### Numeric Types

**Int**
- Integer numbers
- Right-aligned
- Example: `"Quantity:Int:80"`
```python
{"label": "Quantity", "fieldname": "qty", "fieldtype": "Int", "width": 80}
```

**Long Int**
- Large integer numbers
- Right-aligned
- Example: `"Transaction ID:Long Int:100"`
```python
{"label": "Transaction ID", "fieldname": "transaction_id", "fieldtype": "Long Int", "width": 100}
```

**Float**
- Decimal numbers
- Right-aligned
- Supports precision
- Example: `"Rate:Float:100"`
```python
{
    "label": "Rate",
    "fieldname": "rate",
    "fieldtype": "Float",
    "width": 100,
    "precision": 2  # Decimal places
}
```

**Currency**
- Monetary values
- Formatted with currency symbol
- Right-aligned
- Example: `"Amount:Currency:120"`
```python
{
    "label": "Amount",
    "fieldname": "amount",
    "fieldtype": "Currency",
    "width": 120,
    "convertible": "qty"  # For currency conversion
}
```

**Percent**
- Percentage values
- Displays with % symbol
- Example: `"Discount:Percent:80"`
```python
{"label": "Discount", "fieldname": "discount", "fieldtype": "Percent", "width": 80}
```

### Date and Time Types

**Date**
- Date only (YYYY-MM-DD)
- Formatted based on user settings
- Example: `"Posting Date:Date:100"`
```python
{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100}
```

**Datetime**
- Date and time
- Formatted with time zone
- Example: `"Created On:Datetime:150"`
```python
{"label": "Created On", "fieldname": "creation", "fieldtype": "Datetime", "width": 150}
```

**Time**
- Time only (HH:MM:SS)
- Example: `"Start Time:Time:80"`
```python
{"label": "Start Time", "fieldname": "start_time", "fieldtype": "Time", "width": 80}
```

**Duration**
- Time duration (formatted as HH:MM:SS)
- Example: `"Duration:Duration:100"`
```python
{"label": "Duration", "fieldname": "duration", "fieldtype": "Duration", "width": 100}
```

### Link Types

**Link**
- Reference to another DocType
- Clickable link to document
- Requires `options` parameter
- Example: `"Customer:Link/Customer:150"`
```python
{
    "label": "Customer",
    "fieldname": "customer",
    "fieldtype": "Link",
    "options": "Customer",
    "width": 150
}
```

**Dynamic Link**
- Link determined by another field
- Example: `"Reference:Dynamic Link:150"`
```python
{
    "label": "Reference",
    "fieldname": "reference_name",
    "fieldtype": "Dynamic Link",
    "options": "reference_type",  # Field containing DocType name
    "width": 150
}
```

### Boolean Type

**Check**
- Checkbox (0 or 1)
- Shows checkmark icon
- Example: `"Is Active:Check:80"`
```python
{"label": "Is Active", "fieldname": "is_active", "fieldtype": "Check", "width": 80}
```

### Selection Type

**Select**
- Dropdown selection
- Shows selected value
- Example: `"Status:Select:100"`
```python
{
    "label": "Status",
    "fieldname": "status",
    "fieldtype": "Select",
    "options": "Draft\nSubmitted\nCancelled",  # Newline separated
    "width": 100
}
```

### Special Types

**Attach**
- File attachment field
- Shows file link in report
- Example: `"Document:Attach:150"`
```python
{"label": "Document", "fieldname": "attachment", "fieldtype": "Attach", "width": 150}
```

**Attach Image**
- Image attachment with thumbnail
- Shows image preview in report
- Example: `"Photo:Attach Image:100"`
```python
{"label": "Photo", "fieldname": "image", "fieldtype": "Attach Image", "width": 100}
```

**Signature**
- Digital signature field
- Shows signature image in report
- Example: `"Signature:Signature:120"`

**Barcode**
- Barcode value field
- Example: `"Product Code:Barcode:120"`

**Phone**
- Phone number field with formatting
- Example: `"Contact:Phone:120"`

**Geolocation**
- Latitude/longitude coordinates
- Example: `"Location:Geolocation:150"`

**JSON**
- JSON data field
- Displays as formatted JSON in report
- Example: `"Metadata:JSON:200"`

**Autocomplete**
- Text field with autocomplete suggestions
- Example: `"City:Autocomplete:120"`

**Button**
- Custom button in cell
- Requires client-side handler
- Example: `"Actions:Button:80"`
- Note: This is primarily for custom interactive reports

**Image**
- Display image thumbnail
- Shows image from URL or field
- Example: `"Photo:Image:100"`
```python
{"label": "Photo", "fieldname": "image", "fieldtype": "Image", "width": 100}
```

**Icon**
- Display icon
- Example: `"Icon:Icon:50"`

**Color**
- Color picker value
- Shows color block
- Example: `"Color:Color:80"`

**Rating**
- Star rating display
- Example: `"Rating:Rating:100"`

**HTML**
- Raw HTML content for display
- Use with caution (XSS risk)
- Note: Different from HTML Editor fieldtype
- Example: `"Content:HTML:200"`

## Column Width Guidelines

Recommended widths for different content types:

| Content Type | Width (px) | Example |
|--------------|------------|---------|
| ID/Code | 80-120 | Document names, codes |
| Short Text | 100-150 | Status, type, category |
| Medium Text | 150-200 | Names, titles |
| Long Text | 200-300 | Descriptions, addresses |
| Date | 80-100 | Dates without time |
| Datetime | 140-160 | Dates with time |
| Time | 80-100 | Time values |
| Duration | 80-100 | Time durations |
| Currency | 100-120 | Monetary values |
| Quantity | 60-80 | Numbers |
| Percentage | 60-80 | Percentages |
| Check | 40-60 | Checkboxes |
| Link | Same as text | Depends on content |
| Attach/Files | 150-200 | File links |
| Image | 80-120 | Image thumbnails |
| Phone | 120-150 | Phone numbers |
| Barcode | 100-120 | Barcode values |
| Rating | 100-120 | Star ratings |
| Color | 60-80 | Color indicators |
| Icon | 40-60 | Icons |

## Formatting Options

### Precision for Numeric Fields

Control decimal places for Float, Currency, Percent:

```python
{
    "label": "Rate",
    "fieldname": "rate",
    "fieldtype": "Float",
    "precision": 3  # Shows 3 decimal places
}
```

### Currency Conversion

Enable multi-currency conversion:

```python
{
    "label": "Amount",
    "fieldname": "amount",
    "fieldtype": "Currency",
    "options": "currency",  # Field containing currency code
    "convertible": "qty"  # Field to use for conversion
}
```

### Right Alignment

Numeric types are automatically right-aligned:
- Int, Float, Currency, Percent
- Date, Time, Datetime

Text types are left-aligned by default.

## Advanced Column Features

### Conditional Formatting

Use formatter in JS file:

```javascript
formatter: function(value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    
    if (column.fieldname == "status") {
        if (value == "Completed") {
            value = `<span style="color: green;">${value}</span>`;
        } else if (value == "Cancelled") {
            value = `<span style="color: red;">${value}</span>`;
        }
    }
    
    return value;
}
```

### Custom Cell Rendering

```javascript
formatter: function(value, row, column, data, default_formatter) {
    if (column.fieldname == "custom_column") {
        // Custom HTML
        return `<button onclick="myFunction('${data.name}')">Click</button>`;
    }
    
    return default_formatter(value, row, column, data);
}
```

### Totals Row

For numeric columns, totals are automatically calculated if `add_total_row: 1` in report JSON.

Exclude specific columns from totals:

```python
{
    "label": "ID",
    "fieldname": "id",
    "fieldtype": "Int",
    "width": 80,
    "no_total": 1  # Exclude from totals
}
```

## Common Patterns

### Standard Columns

```python
# Document link
"Name:Link/DocType:120"

# Status with color
"Status:Data:100"  # Format with JS formatter

# Date columns
"Date:Date:100"
"Created:Datetime:150"

# Amounts
"Amount:Currency:120"
"Quantity:Int:80"
"Discount:Percent:80"

# User/Owner
"Created By:Link/User:150"
"Modified By:Link/User:150"
```

### Multi-Currency Report

```python
columns = [
    "Invoice:Link/Sales Invoice:150",
    {
        "label": "Currency",
        "fieldname": "currency",
        "fieldtype": "Link",
        "options": "Currency",
        "width": 80
    },
    {
        "label": "Amount",
        "fieldname": "amount",
        "fieldtype": "Currency",
        "options": "currency",
        "width": 120
    },
    {
        "label": "Amount (Base)",
        "fieldname": "base_amount",
        "fieldtype": "Currency",
        "width": 120
    }
]
```

### Time-Based Report

```python
columns = [
    "Task:Link/Task:150",
    "Start:Datetime:150",
    "End:Datetime:150",
    "Duration:Duration:100",
    "Completed:Check:80"
]
```

### Reference/Link Columns

```python
columns = [
    "ID:Link/Main DocType:120",
    {
        "label": "Reference Type",
        "fieldname": "reference_type",
        "fieldtype": "Link",
        "options": "DocType",
        "width": 150
    },
    {
        "label": "Reference",
        "fieldname": "reference_name",
        "fieldtype": "Dynamic Link",
        "options": "reference_type",
        "width": 150
    }
]
```

### Document Management Report

```python
columns = [
    "Document:Link/File:150",
    "Attachment:Attach:150",
    "Image:Attach Image:100",
    "Barcode:Barcode:120",
    "Status:Select:100",
    "Created:Datetime:150"
]
```

### Contact Information Report

```python
columns = [
    "Name:Data:150",
    "Phone:Phone:120",
    "Email:Data:150",
    "Location:Geolocation:150",
    "Rating:Rating:100",
    "Active:Check:60"
]
```

## Best Practices

1. **Use appropriate width**: Don't make columns too wide or too narrow
2. **Consistent types**: Use same fieldtype for similar data across reports
3. **Link liberally**: Make document references clickable with Link fieldtype
4. **Use currency for money**: Always use Currency type for monetary values
5. **Sensible precision**: Don't show unnecessary decimal places
6. **Translated labels**: Wrap labels in `_()` for translation support
7. **Meaningful fieldnames**: Use descriptive fieldnames for dict format
8. **Consider mobile**: Wider columns may not fit on mobile screens

## Translation

Always wrap column labels in translation function:

```python
from frappe import _

columns = [
    _("Name") + ":Data:150",
    _("Amount") + ":Currency:120"
]

# Or for dict format
columns = [
    {
        "label": _("Name"),
        "fieldname": "name",
        "fieldtype": "Data",
        "width": 150
    }
]
```

## Examples by Use Case

### Financial Report
```python
[
    _("Account") + ":Link/Account:200",
    _("Debit") + ":Currency:120",
    _("Credit") + ":Currency:120",
    _("Balance") + ":Currency:120"
]
```

### Inventory Report
```python
[
    _("Item") + ":Link/Item:200",
    _("Warehouse") + ":Link/Warehouse:150",
    _("Quantity") + ":Float:100",
    _("Value") + ":Currency:120",
    _("Last Updated") + ":Datetime:150"
]
```

### User Activity Report
```python
[
    _("User") + ":Link/User:150",
    _("Document") + ":Data:150",
    _("Action") + ":Data:100",
    _("Timestamp") + ":Datetime:150",
    _("IP Address") + ":Data:120"
]
```

### Sales Report
```python
[
    _("Customer") + ":Link/Customer:200",
    _("Order") + ":Link/Sales Order:150",
    _("Date") + ":Date:100",
    _("Qty") + ":Float:80",
    _("Rate") + ":Currency:100",
    _("Amount") + ":Currency:120",
    _("Status") + ":Data:100"
]
```
