import logging
import os

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun
from kombu import Exchange, Queue

logger = logging.getLogger(__name__)

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_recommendation.settings")

app = Celery("movie_recommendation")

# Load configuration from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Define Queues and Exchanges for RabbitMQ
task_exchange = Exchange("tasks", type="topic", durable=True)

app.conf.task_queues = (
    Queue("default", exchange=task_exchange, routing_key="task.default", priority=5),
    Queue("emails", exchange=task_exchange, routing_key="task.emails", priority=10),
    Queue("cache", exchange=task_exchange, routing_key="task.cache", priority=7),
    Queue("api", exchange=task_exchange, routing_key="task.api", priority=6),
    Queue("reports", exchange=task_exchange, routing_key="task.reports", priority=4),
)

app.conf.task_default_queue = "default"
app.conf.task_default_exchange = "tasks"
app.conf.task_default_routing_key = "task.default"

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Celery Signals for Monitoring
@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **extra
):
    """Log when task starts"""
    logger.info(
        "Task %s[%s] started with args=%s, kwargs=%s", task.name, task_id, args, kwargs
    )


@task_postrun.connect
def task_postrun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra
):
    """Log when task completes"""
    logger.info("Task %s[%s] completed successfully", task.name, task_id)


@task_failure.connect
def task_failure_handler(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    **extra,
):
    """Log when task fails"""
    logger.error("Task %s[%s] failed: %s", sender.name, task_id, exception)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery and RabbitMQ connection"""
    print(f"Request: {self.request!r}")
    logger.info("Debug task executed successfully")
    return "Debug task completed"
