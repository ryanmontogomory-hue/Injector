from celery import Celery
import os
import tempfile

# Try Redis first, fallback to filesystem broker
try:
    import redis
    # Test Redis connection
    r = redis.Redis.from_url("redis://localhost:6379/0")
    r.ping()
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    print("✅ Using Redis broker")
except (ImportError, Exception) as e:
    # Fallback to filesystem broker
    temp_dir = tempfile.gettempdir()
    broker_dir = os.path.join(temp_dir, 'celery_broker')
    result_dir = os.path.join(temp_dir, 'celery_results')
    
    os.makedirs(broker_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)
    
    CELERY_BROKER_URL = f"filesystem://"
    CELERY_RESULT_BACKEND = f"file://{result_dir}"
    print(f"⚠️  Redis not available, using filesystem broker: {broker_dir}")

celery_app = Celery(
    'injector',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Configure filesystem broker if being used
if CELERY_BROKER_URL.startswith('filesystem'):
    celery_app.conf.update(
        broker_transport_options={
            'data_folder_in': broker_dir,
            'data_folder_out': broker_dir,
            'data_folder_processed': os.path.join(broker_dir, 'processed')
        }
    )

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    # Task autodiscovery
    # include=['tasks'],  # Include the tasks module
    # imports=['tasks'],  # Alternative way to include tasks
)

# Explicitly import tasks to ensure they're registered
from tasks import process_resume_task
print("✅ Tasks module and process_resume_task imported successfully")


