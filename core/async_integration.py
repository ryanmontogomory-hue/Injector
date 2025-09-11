"""
Integration module for connecting async processing with the main application.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Union
import time

from .async_processor import (
    get_async_doc_processor,
    get_async_file_processor,
    get_background_task_manager,
    async_batch_process
)
from utilities.logger import get_logger
from monitoring.performance_cache import get_cache_manager
from monitoring.performance_monitor import get_performance_monitor

logger = get_logger()
performance_monitor = get_performance_monitor()

def initialize_async_services():
    """Initialize async services when app starts."""
    try:
        # Ensure background task manager is initialized
        background_manager = get_background_task_manager()
        
        # Start cache warmup and memory cleanup background tasks
        background_manager.start_cache_warmup()
        background_manager.start_memory_cleanup()
        
        # Initialize cache manager
        cache_manager = get_cache_manager()
        
        # Initialize async processors
        get_async_doc_processor()
        get_async_file_processor()
        
        # Store task manager in session state for UI access
        if 'background_task_manager' not in st.session_state:
            st.session_state.background_task_manager = background_manager
            
        logger.info("Async services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize async services: {e}")
        return False


def process_documents_async(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process multiple documents asynchronously.
    
    Args:
        documents: List of document data dictionaries
        
    Returns:
        Dictionary with task_ids and initial statuses
    """
    try:
        start_time = time.time()
        processor = get_async_doc_processor()
        
        # Submit batch for processing
        task_ids = processor.process_documents_batch(documents)
        
        # Initialize tracking in session state
        if 'async_tasks' not in st.session_state:
            st.session_state.async_tasks = {}
            
        # Set up initial tracking for each task
        for i, task_id in enumerate(task_ids):
            doc_name = documents[i].get('filename', f'document_{i}')
            st.session_state.async_tasks[task_id] = {
                'type': 'document_processing',
                'status': 'submitted',
                'progress': 0,
                'name': doc_name,
                'submitted_at': time.time()
            }
        
        processing_time = time.time() - start_time
        performance_monitor.record_metric('async_batch_submission_time', processing_time)
        
        logger.info(f"Submitted {len(documents)} documents for async processing in {processing_time:.3f}s")
        
        return {
            'success': True,
            'task_ids': task_ids,
            'message': f"Processing {len(documents)} documents asynchronously"
        }
    except Exception as e:
        logger.error(f"Failed to submit documents for async processing: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': "Failed to submit documents for processing"
        }


def get_async_results(task_ids: List[str], timeout: Optional[float] = 0.01) -> Dict[str, Any]:
    """
    Get results for async tasks, non-blocking.
    
    Args:
        task_ids: List of task IDs to check
        timeout: Maximum time to wait for each task (set low for non-blocking UI)
        
    Returns:
        Dictionary with completed results and status info
    """
    try:
        processor = get_async_doc_processor()
        task_queue = processor.task_queue
        
        results = {}
        completed_tasks = []
        pending_tasks = []
        
        for task_id in task_ids:
            try:
                # Check if result is ready, with minimal wait time
                if task_queue.is_complete(task_id):
                    result = task_queue.get_result(task_id, timeout=timeout)
                    results[task_id] = result
                    completed_tasks.append(task_id)
                    
                    # Update task status in session state
                    if 'async_tasks' in st.session_state and task_id in st.session_state.async_tasks:
                        st.session_state.async_tasks[task_id]['status'] = 'completed'
                        st.session_state.async_tasks[task_id]['progress'] = 100
                        st.session_state.async_tasks[task_id]['completed_at'] = time.time()
                else:
                    pending_tasks.append(task_id)
            except TimeoutError:
                # Task not complete, move on
                pending_tasks.append(task_id)
            except Exception as e:
                # Error retrieving task
                logger.error(f"Error retrieving task {task_id}: {e}")
                results[task_id] = {
                    'success': False,
                    'error': str(e)
                }
                completed_tasks.append(task_id)
        
        return {
            'success': True,
            'completed': completed_tasks,
            'pending': pending_tasks,
            'results': results,
            'all_complete': len(pending_tasks) == 0
        }
    except Exception as e:
        logger.error(f"Failed to get async results: {e}")
        return {
            'success': False,
            'error': str(e),
            'completed': [],
            'pending': task_ids,
            'results': {},
            'all_complete': False
        }


def validate_files_async(files: List[Any]) -> Dict[str, Any]:
    """
    Validate multiple files asynchronously.
    
    Args:
        files: List of file objects
        
    Returns:
        Dictionary with task_ids and initial statuses
    """
    try:
        start_time = time.time()
        processor = get_async_file_processor()
        
        # Submit batch for validation
        task_ids = processor.validate_files_batch(files)
        
        # Initialize tracking in session state
        if 'async_tasks' not in st.session_state:
            st.session_state.async_tasks = {}
            
        # Set up initial tracking for each task
        for i, task_id in enumerate(task_ids):
            file_name = getattr(files[i], 'name', f'file_{i}')
            st.session_state.async_tasks[task_id] = {
                'type': 'file_validation',
                'status': 'submitted',
                'progress': 0,
                'name': file_name,
                'submitted_at': time.time()
            }
        
        processing_time = time.time() - start_time
        performance_monitor.record_metric('async_validation_submission_time', processing_time)
        
        logger.info(f"Submitted {len(files)} files for async validation in {processing_time:.3f}s")
        
        return {
            'success': True,
            'task_ids': task_ids,
            'message': f"Validating {len(files)} files asynchronously"
        }
    except Exception as e:
        logger.error(f"Failed to submit files for async validation: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': "Failed to submit files for validation"
        }


def track_async_progress():
    """
    Render a progress tracker for async tasks in the sidebar.
    """
    if 'async_tasks' not in st.session_state or not st.session_state.async_tasks:
        return
    
    with st.sidebar:
        st.markdown("### 🔄 Background Tasks")
        
        active_tasks = {tid: task for tid, task in st.session_state.async_tasks.items() 
                       if task['status'] not in ['completed', 'failed']}
        
        if not active_tasks:
            st.info("No active background tasks")
            
            # Show option to clear completed tasks history
            completed_tasks = {tid: task for tid, task in st.session_state.async_tasks.items() 
                             if task['status'] in ['completed', 'failed']}
            
            if completed_tasks and st.button("Clear Task History"):
                st.session_state.async_tasks = {}
                st.experimental_rerun()
            
            return
        
        # Update progress for active tasks
        for task_id, task_info in active_tasks.items():
            # Auto-increment progress for long-running tasks to show activity
            if task_info['progress'] < 90:
                elapsed = time.time() - task_info['submitted_at']
                if elapsed > 0.5:  # Only update after half a second
                    # Increment progress based on elapsed time
                    increment = min(5, max(1, int(elapsed / 2)))
                    task_info['progress'] += increment
            
            # Display progress bar
            task_name = task_info['name']
            if len(task_name) > 25:
                task_name = task_name[:22] + "..."
                
            st.progress(task_info['progress'] / 100, 
                      text=f"{task_name} ({task_info['progress']}%)")
        
        # Check for results and update
        processor = get_async_doc_processor()
        
        for task_id in list(active_tasks.keys()):
            if processor.task_queue.is_complete(task_id):
                try:
                    # Non-blocking check
                    result = processor.task_queue.get_result(task_id, timeout=0.01)
                    
                    # Update task status
                    st.session_state.async_tasks[task_id]['status'] = 'completed'
                    st.session_state.async_tasks[task_id]['progress'] = 100
                    st.session_state.async_tasks[task_id]['completed_at'] = time.time()
                    
                    # Trigger rerun to update UI
                    time.sleep(0.1)  # Small delay to prevent UI flicker
                    st.experimental_rerun()
                    
                except TimeoutError:
                    # Still not ready
                    pass
                except Exception as e:
                    # Error retrieving task
                    st.session_state.async_tasks[task_id]['status'] = 'failed'
                    st.session_state.async_tasks[task_id]['error'] = str(e)
        
        # Auto-refresh for active tasks
        if active_tasks:
            time.sleep(0.5)  # Short delay
            st.experimental_rerun()


