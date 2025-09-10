# Celery Integration for Injector

## Overview
This app now supports distributed, background resume processing using Celery and Redis. This enables robust async task queues, scaling, and reliability for high-concurrency workloads.

## How it works
- Resume processing jobs are submitted to Celery workers via Redis.
- Workers process jobs in the background and results can be polled by task ID.
- The UI can submit jobs and poll for status/results, enabling scalable async UX.

## Setup
1. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
2. **Start Redis**
   - Local: `docker run -p 6379:6379 redis`
   - Or use a managed Redis service.
3. **Start Celery worker**
   ```sh
   celery -A celeryconfig.celery_app worker --loglevel=info
   ```
4. **Run the Streamlit app as usual**

## Usage
- Use `ResumeProcessor.process_single_resume_async(file_data)` to submit a job.
- Use `ResumeProcessor.get_async_result(task_id)` to poll for status/result.
- See `tasks.py` for the Celery task definition.

## Notes
- You can scale workers horizontally for high throughput.
- All processing is robustly logged and auditable.
- For production, secure Redis and use a process manager for Celery.
