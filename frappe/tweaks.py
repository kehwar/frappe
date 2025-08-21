import functools

import frappe


def wrap_with_hook(hook_name):
    """
    Decorator to postprocess a function call with the last hook found for `hook_name`.
    The hook will receive (args, kwargs, result) and its return value will be used.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            hooks = frappe.get_hooks(hook_name)
            meta = frappe._dict({"result": result})
            if hooks:
                last_hook = hooks[-1]
                if isinstance(last_hook, str):
                    last_hook = frappe.get_attr(last_hook)
                kwargs["_hook"] = meta
                return last_hook(*args, **kwargs)
            return result

        return wrapper

    return decorator


def wrap_with_hooks(hook_name):
    """
    Decorator to postprocess a function call with the hooks found for `hook_name`.
    The hook will receive (args, kwargs, result) and the last result value will be used.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            hooks = frappe.get_hooks(hook_name)
            meta = frappe._dict({"result": result})
            if hooks:
                for hook in hooks:
                    if isinstance(hook, str):
                        hook = frappe.get_attr(hook)
                    kwargs["_hook"] = meta
                    result = hook(*args, **kwargs)
            return result

        return wrapper

    return decorator
