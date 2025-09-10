import psutil
import os
import time
from celeryconfig import celery_app

def get_resource_stats():
    """Return current CPU, memory, and queue stats."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    # Celery queue length (Redis)
    try:
        import redis
        r = redis.Redis.from_url(os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"))
        qlen = r.llen('celery')
    except Exception:
        qlen = None
    return {
        'cpu_percent': cpu,
        'mem_percent': mem,
        'celery_queue_length': qlen
    }

def monitor_loop(interval=10):
    """Print resource stats every interval seconds."""
    while True:
        stats = get_resource_stats()
        print(f"[MONITOR] CPU: {stats['cpu_percent']}% | MEM: {stats['mem_percent']}% | Celery Q: {stats['celery_queue_length']}")
        time.sleep(interval)
