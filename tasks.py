from celeryconfig import celery_app
from resume_processor import ResumeProcessor

@celery_app.task(bind=True)
def process_resume_task(self, file_data):
    processor = ResumeProcessor()
    return processor.process_single_resume(file_data)
