"""
Gunicorn Multi-Process Load Balancing & Production Concurrency Configuration.
Usage:
    gunicorn -c gunicorn.conf.py "app:create_app()"
"""

import multiprocessing
import os
import sys

# Server Socket Binding
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")
backlog = 2048

# Worker Processes & Concurrency
# Standard formula: (2 x $num_cores) + 1 for I/O and DB bound web apps
cpu_count = multiprocessing.cpu_count()
workers = int(os.getenv("GUNICORN_WORKERS", (cpu_count * 2) + 1))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_connections = 1000

# Worker Lifecycle & Memory Leak Prevention
# Gracefully recycle workers after handling N requests to prevent RAM bloat
max_requests = 1000
max_requests_jitter = 50

# Timeouts & Keep-Alive
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
graceful_timeout = 30
keepalive = 5

# Shared memory directory on Linux to prevent worker heartbeat freezing
if os.path.exists("/dev/shm") and sys.platform.startswith("linux"):
    worker_tmp_dir = "/dev/shm"

# Security & Process Limits
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
accesslog = "-"  # Standard output
errorlog = "-"   # Standard error
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" (%(D)s µs)'

# Process Name
proc_name = "englishmate_gunicorn"

# Server Hooks & Lifecycle Callbacks
def on_starting(server):
    """Callback when master process is starting."""
    server.log.info(
        f"[Gunicorn] Starting EnglishMate server on {bind} with {workers} workers x {threads} threads (CPUs: {cpu_count})"
    )

def post_fork(server, worker):
    """Callback after a worker process is forked."""
    server.log.info(f"[Gunicorn] Worker spawned (PID: {worker.pid})")

def worker_exit(server, worker):
    """Callback when a worker exits."""
    server.log.info(f"[Gunicorn] Worker exited (PID: {worker.pid})")

def worker_abort(worker):
    """Callback when a worker receives SIGABRT."""
    worker.log.warning(f"[Gunicorn] Worker aborted (PID: {worker.pid})")
