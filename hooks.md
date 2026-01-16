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

#### Safe Execution

1. `safe_exec_globals` - method that returns a dict of additional globals to be made available in `frappe.safe_exec()`. The method receives the current globals dict as an argument and should return a dict of additional globals to add.
1. `safe_eval_globals` - method that returns a dict of additional globals to be made available in `frappe.safe_eval()`. The method receives the current globals dict as an argument and should return a dict of additional globals to add.

#### Workflows

1. `workflow_safe_eval_globals` - method that returns a dict of additional globals to be made available in workflow transition conditions. The method receives the current globals dict as an argument and should return a dict of additional globals to add.
1. `filter_workflow_transitions` - method to filter workflow transitions. The method receives `doc`, `transitions`, and `workflow` as arguments and should return the filtered list of transitions.
1. `has_workflow_action_permission` - method to check if a user has permission to perform a workflow action. The method receives `user`, `transition`, and `doc` as arguments and should return a boolean.
