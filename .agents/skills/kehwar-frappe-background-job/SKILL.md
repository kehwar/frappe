---
name: kehwar-frappe-background-job
description: Expert guidance on using `frappe.enqueue` and `frappe.enqueue_doc` to run background jobs in Frappe. Use when enqueueing functions or document methods as background tasks, choosing queue types, setting job IDs for deduplication, checking job status, using the `@frappe.task` decorator, handling retries, or configuring success/failure callbacks.
---

# Frappe Background Jobs

Use this skill when the task involves running code asynchronously in a Frappe background worker.

## `frappe.enqueue` — Full Signature

```python
frappe.enqueue(
    method: str | Callable,      # dotted string or callable
    queue: str = "default",      # "short" | "default" | "long" | custom
    timeout: int | None = None,  # seconds; defaults to queue timeout
    event=None,                  # used for clearing jobs from queues
    is_async: bool = True,       # False → run immediately (useful in tests)
    job_name: str | None = None, # DEPRECATED — use job_id instead
    now: bool = False,           # True → run via frappe.call() synchronously
    enqueue_after_commit: bool = False,  # queue only after DB commit
    *,
    on_success: Callable | None = None,  # callback(job, connection, result)
    on_failure: Callable | None = None,  # callback(job, connection, type, value, traceback)
    at_front: bool = False,      # True → insert at front of queue (higher priority)
    job_id: str | None = None,   # unique ID for deduplication / status checks
    deduplicate=False,           # True → skip enqueue if job_id already queued
    **kwargs,                    # passed as arguments to the enqueued method
) -> Job | Any
```

Available at `frappe.enqueue` (wrapper around `frappe.utils.background_jobs.enqueue`).

## Queue Types and Timeouts

| Queue     | Default Timeout | Use For                                  |
|-----------|-----------------|------------------------------------------|
| `short`   | 300 s           | Quick tasks (notifications, webhooks)    |
| `default` | 300 s           | Standard background work                 |
| `long`    | 1500 s          | Heavy operations (reports, bulk ops)     |
| custom    | configurable    | Defined in `common_site_config.json`     |

Custom queue timeout in `common_site_config.json`:
```json
{ "workers": { "my_queue": { "timeout": 600 } } }
```

## Basic Usage

```python
# String method reference
frappe.enqueue("myapp.tasks.rebuild_index", queue="long")

# Callable reference with kwargs
frappe.enqueue(rebuild_index, doctype="Item", queue="long", timeout=600)

# Run immediately in tests (bypass Redis entirely)
frappe.enqueue(rebuild_index, now=frappe.flags.in_test)

# Queue after current DB transaction commits
frappe.enqueue(
    "myapp.tasks.notify_users",
    enqueue_after_commit=True,
)

# High-priority: insert at front of queue
frappe.enqueue(urgent_task, at_front=True)
```

## `frappe.enqueue_doc` — Enqueue a Method on a Document

```python
frappe.enqueue_doc(
    doctype,          # DocType name
    name=None,        # Document name
    method=None,      # Method name (string) on the document
    queue="default",
    timeout=300,
    now=False,
    **kwargs,
)
```

Example:
```python
frappe.enqueue_doc("Auto Repeat", doc.name, "make_repeated_entry", queue="long")
```

Internally calls `run_doc_method`, which fetches the document and calls `doc.method(**kwargs)`.

## `@frappe.task` Decorator

Attach `.enqueue()` directly to a function:

```python
@frappe.task(queue="short")
def send_welcome_email(user):
    ...

# Enqueue it later — all @task kwargs are pre-applied
send_welcome_email.enqueue(user="administrator")
```

Additional kwargs passed to `.enqueue()` override the decorator defaults.

## Job Deduplication with `job_id`

```python
JOB_ID = "rebuild_item_index"

# Check before enqueueing (manual approach)
from frappe.utils.background_jobs import is_job_enqueued
if not is_job_enqueued(JOB_ID):
    frappe.enqueue(rebuild_index, job_id=JOB_ID)

# Or let Frappe deduplicate automatically
frappe.enqueue(rebuild_index, job_id=JOB_ID, deduplicate=True)
# Returns None (silently skipped) if the job is already queued/started
```

Job IDs are namespaced to the current site: `{site}::{job_id}`.

## Checking Job Status

```python
from frappe.utils.background_jobs import is_job_enqueued, get_job_status, get_job

# Boolean check — True if QUEUED or STARTED
is_job_enqueued("my_job_id")

# Granular status — returns rq.job.JobStatus or None
status = get_job_status("my_job_id")
# Possible values: QUEUED, STARTED, FINISHED, FAILED, DEFERRED, SCHEDULED, CANCELED

# Full RQ Job object
job = get_job("my_job_id")
if job:
    print(job.result)    # return value on success
    print(job.exc_info)  # traceback on failure
```

Via the `RQ Job` DocType:
```python
rq_job = frappe.get_doc("RQ Job", job_id)
print(rq_job.status, rq_job.exc_info)
```

## Retry Logic

Frappe automatically retries a job up to **5 times** (with `sleep(retry + 1)` back-off) when:
- MySQL deadlock error (1213)
- MySQL lock wait timeout error (1205)
- The job itself raises `frappe.RetryBackgroundJobError`

```python
def my_job():
    if resource_locked():
        raise frappe.RetryBackgroundJobError
    ...
```

## Callbacks

```python
def on_done(job, connection, result):
    frappe.logger().info(f"Job {job.id} finished: {result}")

def on_fail(job, connection, type, value, traceback):
    frappe.logger().error(f"Job {job.id} failed: {value}")

frappe.enqueue(
    my_task,
    on_success=on_done,
    on_failure=on_fail,
)
```

Default failure callback (`truncate_failed_registry`) keeps the failed-jobs registry within the configured `rq_failed_jobs_limit` (default 1000).

## Hooks: `before_job` / `after_job`

Register app-level hooks in `hooks.py` to intercept every job:

```python
before_job = "myapp.jobs.before_job_hook"
after_job  = "myapp.jobs.after_job_hook"
```

Hook signatures:
```python
def before_job_hook(method, kwargs, transaction_type):  ...
def after_job_hook(method, kwargs, result):             ...
```

For per-job after-job callbacks use `frappe.local.job.after_job`:
```python
frappe.local.job.after_job.add(lambda: cleanup())
```

## Key Constants (frappe/utils/background_jobs.py)

```python
RQ_JOB_FAILURE_TTL   = 7 * 24 * 60 * 60  # failed jobs kept 7 days
RQ_FAILED_JOBS_LIMIT = 1000               # max stored failed jobs
RQ_RESULTS_TTL       = 10 * 60           # successful results kept 10 min
MAX_QUEUED_JOBS      = 500               # enqueue raises if queue exceeds this
```

## Implementation Reference

For internals and debugging details, read `references/implementation.md`. It covers:

- `execute_job` source with retry and hook flow
- `enqueue_after_commit` deferred-commit mechanism
- Deduplication logic and edge cases
- Redis connection, queue naming, and worker polling
- `frappe.local.job` context object
- Queue overflow guard (`QueueOverloaded`)
- Failed-job registry pruning
- `CallbackManager` internals
- Error logging during jobs
- `RQ Job` DocType API for stopping/cancelling jobs
- Debugging checklist with common issues and fixes
