"""
Async processing module for Resume Customizer application.
Provides asynchronous processing for I/O-bound operations and background tasks.
"""

import asyncio
import aiofiles
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional, Union, Awaitable
from dataclasses import dataclass
import time
import threading
from queue import Queue
from io import BytesIO
import functools

from utilities.logger import get_logger
from monitoring.performance_cache import get_cache_manager, cache_key_for_file

logger = get_logger()


@dataclass
class AsyncTask:
    """Async task representation."""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


class AsyncTaskQueue:
    """High-performance async task queue with priority support."""
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = Queue()
        self.results = {}
        self.running_tasks = {}
        self._shutdown = False
        
        # Start worker threads
        self.workers = []
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def submit_task(self, task_id: str, func: Callable, *args, priority: int = 0, **kwargs) -> str:
        """Submit a task for async execution."""
        task = AsyncTask(
            id=task_id,
            name=func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        self.tasks.put(task)
        logger.debug(f"Task {task_id} submitted for async execution")
        return task_id
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Get task result, blocking until completion."""
        start_time = time.time()
        
        while task_id not in self.results:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
            time.sleep(0.01)  # Small delay to avoid busy waiting
        
        result = self.results.pop(task_id)
        if isinstance(result, Exception):
            raise result
        return result
    
    def is_complete(self, task_id: str) -> bool:
        """Check if task is complete."""
        return task_id in self.results
    
    def _worker_loop(self):
        """Worker thread loop."""
        while not self._shutdown:
            try:
                task = self.tasks.get(timeout=1.0)
                self.running_tasks[task.id] = task
                
                try:
                    # Execute the task
                    start_time = time.time()
                    result = task.func(*task.args, **task.kwargs)
                    execution_time = time.time() - start_time
                    
                    self.results[task.id] = result
                    logger.debug(f"Task {task.id} completed in {execution_time:.3f}s")
                    
                except Exception as e:
                    self.results[task.id] = e
                    logger.error(f"Task {task.id} failed: {e}")
                
                finally:
                    self.running_tasks.pop(task.id, None)
                    self.tasks.task_done()
                    
            except:
                continue  # Timeout or shutdown
    
    def shutdown(self):
        """Shutdown the task queue."""
        self._shutdown = True
        self.executor.shutdown(wait=True)


class AsyncDocumentProcessor:
    """Async document processing with batch operations."""
    
    def __init__(self):
        self.task_queue = AsyncTaskQueue(max_workers=6)
        self.cache_manager = get_cache_manager()
    
    def process_documents_batch(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Process multiple documents asynchronously."""
        task_ids = []
        
        for i, doc_data in enumerate(documents):
            task_id = f"doc_process_{i}_{int(time.time() * 1000)}"
            
            # Check cache first
            cache_key = self._generate_doc_cache_key(doc_data)
            cached_result = self.cache_manager.get_cache('document').get(cache_key)
            
            if cached_result is not None:
                # Return cached result immediately
                self.task_queue.results[task_id] = cached_result
            else:
                # Submit for async processing
                self.task_queue.submit_task(
                    task_id, 
                    self._process_single_document, 
                    doc_data,
                    cache_key,
                    priority=1
                )
            
            task_ids.append(task_id)
        
        return task_ids
    
    def _process_single_document(self, doc_data: Dict[str, Any], cache_key: str) -> Dict[str, Any]:
        """Process a single document (runs in worker thread)."""
        try:
            from core.document_processor import get_document_processor
            
            processor = get_document_processor()
            result = processor.process_document(doc_data)
            
            # Cache the result
            self.cache_manager.get_cache('document').put(cache_key, result, ttl=1800)
            
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': doc_data.get('filename', 'unknown')
            }
    
    def _generate_doc_cache_key(self, doc_data: Dict[str, Any]) -> str:
        """Generate cache key for document processing."""
        key_parts = [
            doc_data.get('filename', 'unknown'),
            str(hash(doc_data.get('text', ''))),
            str(hash(str(doc_data.get('tech_stacks', {}))))
        ]
        return '|'.join(key_parts)


class AsyncFileProcessor:
    """Async file processing for uploads and downloads."""
    
    def __init__(self):
        self.task_queue = AsyncTaskQueue(max_workers=4)
    
    async def read_file_async(self, file_path: str) -> bytes:
        """Read file asynchronously."""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            return content
        except Exception as e:
            logger.error(f"Async file read failed for {file_path}: {e}")
            raise
    
    async def write_file_async(self, file_path: str, content: bytes) -> bool:
        """Write file asynchronously."""
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Async file write failed for {file_path}: {e}")
            return False
    
    def validate_files_batch(self, files: List[Any]) -> List[str]:
        """Validate multiple files asynchronously."""
        task_ids = []
        
        for i, file_obj in enumerate(files):
            task_id = f"file_validate_{i}_{int(time.time() * 1000)}"
            self.task_queue.submit_task(
                task_id,
                self._validate_single_file,
                file_obj,
                priority=2  # Higher priority for validation
            )
            task_ids.append(task_id)
        
        return task_ids
    
    def _validate_single_file(self, file_obj) -> Dict[str, Any]:
        """Validate a single file (runs in worker thread)."""
        try:
            from utilities.validators import FileValidator
            
            validator = FileValidator()
            return validator.validate_file(file_obj)
            
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': [],
                'file_info': {'name': getattr(file_obj, 'name', 'unknown')}
            }


class BackgroundTaskManager:
    """Manages long-running background tasks."""
    
    def __init__(self):
        self.tasks = {}
        self.task_queue = AsyncTaskQueue(max_workers=3)
    
    def start_cache_warmup(self) -> str:
        """Start cache warmup task."""
        task_id = f"cache_warmup_{int(time.time())}"
        self.task_queue.submit_task(task_id, self._warmup_cache, priority=0)
        return task_id
    
    def start_memory_cleanup(self) -> str:
        """Start memory cleanup task."""
        task_id = f"memory_cleanup_{int(time.time())}"
        self.task_queue.submit_task(task_id, self._cleanup_memory, priority=1)
        return task_id
    
    def _warmup_cache(self):
        """Warm up caches with common operations."""
        logger.info("Starting cache warmup...")
        
        # Warmup parsing cache with common tech stacks
        common_tech_stacks = [
            "Python: • Web development • Data analysis",
            "JavaScript: • Frontend development • Node.js",
            "React: • Component development • State management",
            "AWS: • Cloud deployment • EC2 management"
        ]
        
        try:
            from core.text_parser import get_parser
            parser = get_parser()
            
            for tech_stack in common_tech_stacks:
                parser.parse_tech_stacks(tech_stack)
            
            logger.info("Cache warmup completed")
        except Exception as e:
            logger.error(f"Cache warmup failed: {e}")
    
    def _cleanup_memory(self):
        """Clean up memory and optimize performance."""
        logger.info("Starting memory cleanup...")
        
        try:
            import gc
            import psutil
            
            # Get memory info before cleanup
            memory_before = psutil.virtual_memory()
            
            # Force garbage collection
            collected = gc.collect()
            
            # Get memory info after cleanup
            memory_after = psutil.virtual_memory()
            
            memory_freed = memory_before.used - memory_after.used
            
            logger.info(f"Memory cleanup completed: {collected} objects collected, "
                       f"{memory_freed / (1024*1024):.1f}MB freed")
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")


# Global instances
_async_doc_processor = None
_async_file_processor = None
_background_task_manager = None


def get_async_doc_processor() -> AsyncDocumentProcessor:
    """Get singleton async document processor."""
    global _async_doc_processor
    if _async_doc_processor is None:
        _async_doc_processor = AsyncDocumentProcessor()
    return _async_doc_processor


def get_async_file_processor() -> AsyncFileProcessor:
    """Get singleton async file processor."""
    global _async_file_processor
    if _async_file_processor is None:
        _async_file_processor = AsyncFileProcessor()
    return _async_file_processor


def get_background_task_manager() -> BackgroundTaskManager:
    """Get singleton background task manager."""
    global _background_task_manager
    if _background_task_manager is None:
        _background_task_manager = BackgroundTaskManager()
        # Start cache warmup on first access
        _background_task_manager.start_cache_warmup()
    return _background_task_manager


def async_batch_process(items: List[Any], process_func: Callable, 
                       max_concurrent: int = 8, **kwargs) -> List[Any]:
    """Generic async batch processing function."""
    task_queue = AsyncTaskQueue(max_workers=max_concurrent)
    task_ids = []
    
    for i, item in enumerate(items):
        task_id = f"batch_item_{i}_{int(time.time() * 1000)}"
        task_queue.submit_task(task_id, process_func, item, **kwargs)
        task_ids.append(task_id)
    
    # Collect results
    results = []
    for task_id in task_ids:
        try:
            result = task_queue.get_result(task_id, timeout=30)
            results.append(result)
        except TimeoutError:
            logger.warning(f"Task {task_id} timed out")
            results.append(None)
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            results.append(None)
    
    task_queue.shutdown()
    return results


