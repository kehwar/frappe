Custom Workflow master for a particular DocType

## Workflow Hooks

Frappe provides several hooks to extend and customize workflow behavior:

### 1. workflow_safe_eval_globals

Extend the globals available in workflow transition conditions.

**Usage in hooks.py:**
```python
workflow_safe_eval_globals = [
    "myapp.workflows.get_custom_globals"
]
```

**Implementation:**
```python
# myapp/workflows.py
def get_custom_globals(globals_dict):
    """Add custom globals for workflow conditions
    
    Args:
        globals_dict: Current globals dictionary
        
    Returns:
        dict: Additional globals to add
    """
    return {
        "custom_value": "test_value",
        "custom_function": lambda x: x * 2,
        "get_balance": get_customer_balance,
    }
```

**Example workflow condition:**
```python
# In Workflow Transition condition field:
custom_value == "test_value" and get_balance(doc.customer) > 10000
```

### 2. filter_workflow_transitions

Filter the list of available transitions for a document.

**Usage in hooks.py:**
```python
filter_workflow_transitions = [
    "myapp.workflows.filter_transitions"
]
```

**Implementation:**
```python
# myapp/workflows.py
def filter_transitions(doc, transitions, workflow):
    """Filter workflow transitions based on custom logic
    
    Args:
        doc: The document
        transitions: List of available transitions
        workflow: The workflow document
        
    Returns:
        list: Filtered list of transitions
    """
    # Example: Only allow "Approve" if amount is less than 100000
    if hasattr(doc, "amount") and doc.amount > 100000:
        return [t for t in transitions if t.get("action") != "Approve"]
    return transitions
```

### 3. has_workflow_action_permission

Check if a user has permission to perform a workflow action.

**Usage in hooks.py:**
```python
has_workflow_action_permission = [
    "myapp.workflows.check_workflow_permission"
]
```

**Implementation:**
```python
# myapp/workflows.py
def check_workflow_permission(user, transition, doc):
    """Check if user has permission for workflow action
    
    Args:
        user: User email
        transition: Transition dict
        doc: The document
        
    Returns:
        bool: True if user has permission
    """
    # Example: Only managers can approve amounts over 50000
    if transition.get("action") == "Approve":
        if hasattr(doc, "amount") and doc.amount > 50000:
            return user in get_managers()
    return True
```

## Safe Execution Hooks

### safe_exec_globals

Extend the globals available in `frappe.safe_exec()` (Server Scripts).

**Usage in hooks.py:**
```python
safe_exec_globals = [
    "myapp.utils.get_safe_exec_globals"
]
```

**Implementation:**
```python
# myapp/utils.py
def get_safe_exec_globals(globals_dict):
    """Add custom globals for safe_exec
    
    Args:
        globals_dict: Current globals dictionary
        
    Returns:
        dict: Additional globals to add
    """
    return {
        "my_custom_function": my_custom_function,
        "MY_CONSTANT": 42,
    }
```

### safe_eval_globals

Extend the globals available in `frappe.safe_eval()`.

**Usage in hooks.py:**
```python
safe_eval_globals = [
    "myapp.utils.get_safe_eval_globals"
]
```

**Implementation:**
```python
# myapp/utils.py
def get_safe_eval_globals(globals_dict):
    """Add custom globals for safe_eval
    
    Args:
        globals_dict: Current globals dictionary
        
    Returns:
        dict: Additional globals to add
    """
    return {
        "custom_eval_func": lambda x: x * 2,
        "MULTIPLIER": 100,
    }
```