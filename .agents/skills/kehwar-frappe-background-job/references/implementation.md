# Background Job Implementation Details

Covers internal mechanics of `frappe/utils/background_jobs.py` — useful for debugging
stuck/failed jobs, understanding ordering guarantees, and writing reliable job code.

## Table of Contents

1. [Job Execution Flow (`execute_job`)](#1-job-execution-flow-execute_job)
2. [Retry Logic (Deadlock / Timeout)](#2-retry-logic)
3. [`enqueue_after_commit` — Deferred Queueing](#3-enqueue_after_commit)
4. [Deduplication Internals (`deduplicate`)](#4-deduplication-internals)
5. [Redis Connection & Queue Naming](#5-redis-connection--queue-naming)
6. [Worker Startup & Job Polling](#6-worker-startup--job-polling)
7. [`frappe.local.job` Context Object](#7-frappelocaljob-context-object)
8. [Queue Overflow Guard (`MAX_QUEUED_JOBS`)](#8-queue-overflow-guard)
9. [Failed-Job Registry Pruning](#9-failed-job-registry-pruning)
10. [`CallbackManager` — Deferred Callbacks](#10-callbackmanager)
11. [Error Logging During Jobs](#11-error-logging-during-jobs)
12. [RQ Job DocType — Inspecting Jobs from Python](#12-rq-job-doctype)
13. [Debugging Checklist](#13-debugging-checklist)

---

## 1. Job Execution Flow (`execute_job`)

`execute_job` is the function RQ actually calls inside the worker process.

```python
# frappe/utils/background_jobs.py:193
def execute_job(site, method, event, job_name, kwargs, user=None, is_async=True, retry=0):
    retval = None

    if is_async:
        frappe.init(site=site)   # Boot frappe for this site
        frappe.connect()          # Open DB connection
        if os.environ.get("CI"):
            frappe.flags.in_test = True
        if user:
            frappe.set_user(user)

    if isinstance(method, str):
        method_name = method
        method = frappe.get_attr(method)
    else:
        method_name = f"{method.__module__}.{method.__qualname__}"

    # Set up frappe.local.job (see section 7)
    frappe.local.job = frappe._dict(
        site=site,
        method=method_name,
        job_name=job_name,
        kwargs=kwargs,
        user=user,
        after_job=CallbackManager(),
    )

    # Run before_job hooks
    for task in frappe.get_hooks("before_job"):
        frappe.call(task, method=method_name, kwargs=kwargs, transaction_type="job")

    try:
        retval = method(**kwargs)           # ← actual job runs here

    except (frappe.db.InternalError, frappe.RetryBackgroundJobError) as e:
        frappe.db.rollback()
        # Retry if deadlock / lock timeout / explicit retry request
        if retry < 5 and (...):
            frappe.job.after_job.reset()
            frappe.destroy()
            time.sleep(retry + 1)          # back-off: 1 s, 2 s, 3 s, 4 s, 5 s
            return execute_job(..., retry=retry + 1)
        else:
            frappe.log_error(title=method_name)
            raise

    except Exception:
        frappe.db.rollback()
        frappe.log_error(title=method_name)
        frappe.db.commit()                  # commit the error log
        raise

    else:
        frappe.db.commit()                  # commit job work
        return retval

    finally:
        # Always runs (success or failure)
        for task in frappe.get_hooks("after_job"):
            frappe.call(task, method=method_name, kwargs=kwargs, result=retval)
        frappe.local.job.after_job.run()    # deferred per-job callbacks
        if is_async:
            frappe.destroy()
```

**Key takeaways:**
- Every job gets a fresh DB connection (`frappe.init` + `frappe.connect`).
- `frappe.db.commit()` is called automatically on success; the job code does not need to commit.
- `after_job` hooks and callbacks run even when the job fails (in `finally`).
- Errors are written to the `Error Log` DocType before the exception propagates to RQ.

---

## 2. Retry Logic

Automatic retries (up to 5) happen for:

| Trigger | MySQL errno |
|---|---|
| Deadlock | 1213 |
| Lock wait timeout | 1205 |
| `raise frappe.RetryBackgroundJobError` | — |

Back-off: `time.sleep(retry + 1)` → sleeps 1 s, 2 s, 3 s, 4 s, 5 s between attempts.

On each retry:
1. DB rolled back.
2. `after_job` callbacks cleared (`reset()`).
3. Frappe torn down (`frappe.destroy()`).
4. `execute_job` called recursively with `retry=N+1`.

After 5 failures the exception propagates to RQ and the job lands in the failed registry.

To trigger a manual retry from inside a job:

```python
def my_job():
    if some_transient_condition():
        raise frappe.RetryBackgroundJobError
```

---

## 3. `enqueue_after_commit`

When `enqueue_after_commit=True`, the Redis `LPUSH` is deferred until after the current
database transaction commits.

```python
# frappe/utils/background_jobs.py:168-172
if enqueue_after_commit:
    frappe.db.after_commit.add(enqueue_call)   # registered, NOT yet sent
    return                                      # returns None immediately

return enqueue_call()                           # sent right now
```

`frappe.db.after_commit` is a `CallbackManager` that runs inside `Database.commit()`:

```python
# frappe/database/database.py
def commit(self):
    self.before_commit.run()
    self.sql("commit")
    self.begin()
    self.value_cache.clear()
    self.after_commit.run()    # ← enqueue_call fires here
```

**Use this when:** the job needs data that the current transaction is about to write.
Without it, the worker may start and read stale (uncommitted) data.

**Caveat:** if the transaction is rolled back, `after_commit` never fires — the job is
silently dropped (desired behavior: no job for failed writes).

---

## 4. Deduplication Internals

```python
# frappe/utils/background_jobs.py:93-106
if deduplicate:
    if not job_id:
        frappe.throw(_("`job_id` parameter is required for deduplication."))

    job = get_job(job_id)   # fetch from Redis by site-namespaced ID

    if job and job.get_status() in (JobStatus.QUEUED, JobStatus.STARTED):
        frappe.logger().error(f"Not queueing job {job.id} because it is in queue already")
        return None          # silently skip — caller receives None

    elif job:
        job.delete()         # remove stale finished/failed job object before re-queueing
```

Job IDs are namespaced per site:

```python
# frappe/utils/background_jobs.py:559
def create_job_id(job_id: str) -> str:
    if not job_id:
        job_id = str(uuid4())
    return f"{frappe.local.site}::{job_id}"
```

**Rules:**
- `deduplicate=True` requires an explicit `job_id`.
- Only QUEUED and STARTED statuses block re-enqueueing.
- FINISHED / FAILED jobs are deleted from Redis before the new job is enqueued.
- Returns `None` (not the job) when deduplicated — guard against `NoneType` if you use
  the return value.

---

## 5. Redis Connection & Queue Naming

Queue names include the bench ID to allow multiple benches on the same Redis instance:

```python
def generate_qname(qtype: str) -> str:
    return f"{get_bench_id()}:{qtype}"    # e.g. "frappe-bench:default"
```

Redis connection is obtained via `get_redis_conn()`, which retries up to 5 times on
`BusyLoadingError` or `ConnectionError` (using `tenacity`):

```python
@retry(
    retry=retry_if_exception_type((BusyLoadingError, ConnectionError)),
    stop=stop_after_attempt(5),
    wait=wait_fixed(1),
    reraise=True,
)
def get_redis_conn(username=None, password=None): ...
```

Authentication is controlled by:
- `"use_rq_auth"` in `common_site_config.json` → reads `rq_username` / `rq_password` from
  site config.
- `RQ_ADMIN_PASWORD` env var (note: typo in source) → uses `default` user.
- Otherwise → unauthenticated connection.

---

## 6. Worker Startup & Job Polling

Workers are started via `bench worker` (calls `start_worker`):

```python
# frappe/utils/background_jobs.py:290
def start_worker(queue=None, quiet=False, rq_username=None, rq_password=None,
                 burst=False, strategy=DequeueStrategy.DEFAULT):
    with frappe.init_site():
        redis_connection = get_redis_conn(...)
        queues = get_queue_list(queue, build_queue_name=True)

    worker = Worker(queues, connection=redis_connection)
    worker.work(
        burst=burst,                   # True → exit after queue drains
        dequeue_strategy=strategy,     # DEFAULT (FIFO) or ROUND_ROBIN
    )
```

`FrappeWorker` extends RQ's `Worker` to start the scheduler in a daemon thread:

```python
class FrappeWorker(Worker):
    def work(self, *args, **kwargs):
        self.start_frappe_scheduler()
        return super().work(*args, **kwargs)
```

Internally RQ uses `BLPOP` (blocking pop) on the queue keys — workers sleep cheaply
until a job arrives.

**Dequeue strategies:**
- `DEFAULT` — jobs dequeued FIFO within each queue; queues processed in configured order.
- `ROUND_ROBIN` — rotates across queues so no single queue starves others.

---

## 7. `frappe.local.job` Context Object

Available inside `execute_job` (and therefore inside the job function itself and all hooks):

```python
frappe.local.job = frappe._dict(
    site=site,               # "mysite.localhost"
    method=method_name,      # "myapp.tasks.rebuild_index"
    job_name=job_name,       # display name (may be None)
    kwargs=kwargs,           # dict of args passed to the method
    user=user,               # frappe user running the job
    after_job=CallbackManager(),   # add deferred callbacks here
)
```

**Add a deferred callback from inside a job:**

```python
def my_job():
    frappe.local.job.after_job.add(lambda: send_notification())
    # send_notification() runs after all after_job hooks complete
```

**`frappe.local.job` is NOT available** outside of `execute_job` context (e.g., in regular
HTTP requests). Guard with `hasattr(frappe.local, "job")` if needed.

`frappe.job` is a thread-local proxy alias for `frappe.local.job` (`frappe/__init__.py:179`).
Both forms work identically inside worker context.

---

## 8. Queue Overflow Guard

```python
MAX_QUEUED_JOBS = 500   # module-level default

def _check_queue_size(q: Queue):
    max_jobs = cint(frappe.conf.max_queued_jobs)
    if not max_jobs:
        return                     # guard disabled (0 or unset)
    if cint(q.count) >= max_jobs:
        frappe.throw(..., exc=frappe.QueueOverloaded)
```

This is called at the top of every `enqueue()` call (before pushing to Redis).

**Configure** in `common_site_config.json`:
```json
{ "max_queued_jobs": 1000 }
```

Set to `0` or omit to disable the guard entirely.

**Catch programmatically:**
```python
try:
    frappe.enqueue(my_job)
except frappe.QueueOverloaded:
    # defer or alert
```

---

## 9. Failed-Job Registry Pruning

`truncate_failed_registry` is the default `on_failure` callback for every job:

```python
def truncate_failed_registry(job, connection, type, value, traceback):
    conf = frappe.conf if frappe.conf else frappe.get_conf(site=job.kwargs.get("site"))
    limit = (conf.get("rq_failed_jobs_limit") or RQ_FAILED_JOBS_LIMIT) - 1

    for queue in get_queues(connection=connection):
        fail_registry = queue.failed_job_registry
        excess = fail_registry.get_job_ids()[limit:]      # jobs beyond the limit

        for job_ids in create_batch(excess, 100):         # delete in batches of 100
            for job_obj in Job.fetch_many(job_ids=job_ids, connection=connection):
                job_obj and fail_registry.remove(job_obj, delete_job=True)
```

Default limit: `RQ_FAILED_JOBS_LIMIT = 1000`.
Override per-site: `"rq_failed_jobs_limit": 500` in `site_config.json`.

Failed jobs are also subject to TTL expiry: `RQ_JOB_FAILURE_TTL = 7 * 24 * 60 * 60` (7 days).

---

## 10. `CallbackManager`

Used by both `frappe.db.after_commit` and `frappe.local.job.after_job`:

```python
class CallbackManager:
    def __init__(self):
        self._functions = deque()

    def add(self, func):
        self._functions.append(func)   # FIFO

    def run(self):
        while self._functions:
            self._functions.popleft()()

    def reset(self):
        self._functions.clear()
```

`reset()` is called on retry so callbacks registered before the failed attempt do not
accumulate across retries.

---

## 11. Error Logging During Jobs

On any unhandled exception `execute_job` calls `frappe.log_error(title=method_name)`.
This writes an `Error Log` record with the current traceback.

**Query recent job errors:**

```python
frappe.get_list(
    "Error Log",
    filters={"method": "myapp.tasks.rebuild_index"},
    fields=["name", "error", "creation"],
    order_by="creation desc",
    limit_page_length=10,
)
```

Errors are committed to the DB even when the job transaction is rolled back (separate
`frappe.db.commit()` call after rollback).

---

## 12. RQ Job DocType

`frappe/core/doctype/rq_job/rq_job.py` provides a Desk-facing wrapper over RQ jobs.

**Fetch a job:**
```python
rq_job = frappe.get_doc("RQ Job", "mysite.localhost::my_job_id")
print(rq_job.status)       # queued | started | finished | failed | ...
print(rq_job.exc_info)     # full traceback string (failed jobs)
print(rq_job.arguments)    # JSON-encoded kwargs
print(rq_job.time_taken)   # seconds (finished jobs)
```

**Stop a running job (sends SIGINT to worker):**
```python
rq_job.stop_job()
```

**Cancel a queued job:**
```python
rq_job.cancel()
```

**List jobs by status:**
```python
from frappe.core.doctype.rq_job.rq_job import fetch_job_ids, serialize_job
from frappe.utils.background_jobs import get_queue

q = get_queue("default")
failed_ids = fetch_job_ids(q, "failed")
jobs = [serialize_job(job) for job in Job.fetch_many(job_ids=failed_ids, connection=conn)
        if job]
```

`serialize_job` returns a `frappe._dict` with: `name`, `queue`, `job_name`, `status`,
`started_at`, `ended_at`, `time_taken`, `exc_info`, `arguments`, `timeout`, `owner`.

**Delete all failed jobs for the current site:**
```python
from frappe.core.doctype.rq_job.rq_job import remove_failed_jobs
remove_failed_jobs()   # requires System Manager
```

---

## 13. Debugging Checklist

### Is the job queued / running?

```python
from frappe.utils.background_jobs import is_job_enqueued, get_job_status, get_job

is_job_enqueued("my_job_id")          # True if QUEUED or STARTED
get_job_status("my_job_id")           # JobStatus enum or None
job = get_job("my_job_id")
if job:
    print(job.get_status(), job.exc_info)
```

### Check queue depths

```python
from frappe.utils.background_jobs import get_queues, get_redis_conn

for q in get_queues():
    print(q.name, "queued:", q.count,
          "failed:", q.failed_job_registry.count,
          "started:", q.started_job_registry.count)
```

### Are workers running?

```python
from frappe.utils.background_jobs import get_workers, get_queue

workers = get_workers(queue=get_queue("default"))
for w in workers:
    current = w.get_current_job()
    print(w.name, "→", current.id if current else "idle")
```

### Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `QueueOverloaded` exception | Queue hit `max_queued_jobs` | Wait or increase limit |
| `enqueue` returns `None` | `deduplicate=True` skipped it | Check `is_job_enqueued` first |
| Job never starts | Workers not running or Redis unreachable | `bench worker`, check Redis |
| Job fails immediately | Exception in method; check `Error Log` | `frappe.get_list("Error Log", ...)` |
| Deadlock / lock timeout | Concurrent writes | Auto-retried ×5; check if still failing |
| `after_job` hook not running | Job aborted before `finally` | Unlikely — `finally` always runs |
| `frappe.local.job` missing | Code running outside worker context | Guard with `hasattr(frappe.local, "job")` |
| `enqueue_after_commit` job lost | Outer transaction rolled back | Expected — no job for failed writes |
