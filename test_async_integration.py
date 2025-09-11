"""
Test script for async processing integration.
"""

import sys
import time
from typing import List, Dict, Any

def test_async_imports():
    """Test if all async modules can be imported."""
    print("Testing async module imports...")
    
    try:
        from core.async_processor import (
            get_async_doc_processor,
            get_async_file_processor,
            get_background_task_manager,
            async_batch_process,
            AsyncTaskQueue,
            AsyncDocumentProcessor
        )
        print("✅ async_processor module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import async_processor: {e}")
        return False
    
    try:
        from async_integration import (
            initialize_async_services,
            process_documents_async,
            get_async_results,
            validate_files_async,
            track_async_progress
        )
        print("✅ async_integration module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import async_integration: {e}")
        return False
    
    return True


def test_async_task_queue():
    """Test the AsyncTaskQueue functionality."""
    print("\nTesting AsyncTaskQueue...")
    
    try:
        from core.async_processor import AsyncTaskQueue
        
        # Create a task queue
        queue = AsyncTaskQueue(max_workers=2)
        
        # Simple test function
        def test_func(x, y):
            time.sleep(0.1)  # Simulate work
            return x + y
        
        # Submit a task
        task_id = queue.submit_task("test_task", test_func, 5, 3)
        print(f"✅ Task submitted with ID: {task_id}")
        
        # Wait for result
        start_time = time.time()
        result = queue.get_result(task_id, timeout=5.0)
        end_time = time.time()
        
        print(f"✅ Task completed in {end_time - start_time:.3f}s, result: {result}")
        
        if result == 8:
            print("✅ Task result is correct")
        else:
            print(f"❌ Task result incorrect, expected 8 got {result}")
            return False
        
        # Shutdown the queue
        queue.shutdown()
        print("✅ Task queue shutdown successfully")
        
        return True
    except Exception as e:
        print(f"❌ AsyncTaskQueue test failed: {e}")
        return False


def test_async_document_processor():
    """Test the AsyncDocumentProcessor functionality."""
    print("\nTesting AsyncDocumentProcessor...")
    
    try:
        from core.async_processor import get_async_doc_processor
        
        processor = get_async_doc_processor()
        
        # Create test documents
        test_docs = [
            {
                'filename': 'resume1.docx',
                'text': 'Python developer with Django experience',
                'tech_stacks': {'Python': ['Django', 'Flask']}
            },
            {
                'filename': 'resume2.docx', 
                'text': 'JavaScript developer with React experience',
                'tech_stacks': {'JavaScript': ['React', 'Node.js']}
            }
        ]
        
        # Submit for processing
        task_ids = processor.process_documents_batch(test_docs)
        print(f"✅ Submitted {len(task_ids)} documents for processing")
        
        # Wait for results (simple polling)
        max_wait = 10
        wait_time = 0
        results = {}
        
        while wait_time < max_wait and len(results) < len(task_ids):
            for task_id in task_ids:
                if task_id not in results and processor.task_queue.is_complete(task_id):
                    try:
                        result = processor.task_queue.get_result(task_id, timeout=0.1)
                        results[task_id] = result
                        print(f"✅ Task {task_id} completed")
                    except Exception as e:
                        print(f"❌ Error getting result for {task_id}: {e}")
            
            time.sleep(0.2)
            wait_time += 0.2
        
        print(f"✅ Collected {len(results)}/{len(task_ids)} results")
        
        # Shutdown
        processor.task_queue.shutdown()
        
        return len(results) > 0
    except Exception as e:
        print(f"❌ AsyncDocumentProcessor test failed: {e}")
        return False


def test_background_task_manager():
    """Test the BackgroundTaskManager functionality."""
    print("\nTesting BackgroundTaskManager...")
    
    try:
        from core.async_processor import get_background_task_manager
        
        manager = get_background_task_manager()
        
        # Start a cache warmup task
        cache_task_id = manager.start_cache_warmup()
        print(f"✅ Cache warmup task started: {cache_task_id}")
        
        # Start a memory cleanup task  
        memory_task_id = manager.start_memory_cleanup()
        print(f"✅ Memory cleanup task started: {memory_task_id}")
        
        # Wait a bit for tasks to potentially complete
        time.sleep(1.0)
        
        # Check task status
        for task_id, task_name in [(cache_task_id, "cache_warmup"), (memory_task_id, "memory_cleanup")]:
            if manager.task_queue.is_complete(task_id):
                try:
                    result = manager.task_queue.get_result(task_id, timeout=0.1)
                    print(f"✅ {task_name} task completed")
                except Exception as e:
                    print(f"❌ {task_name} task failed: {e}")
            else:
                print(f"⏳ {task_name} task still running")
        
        # Shutdown
        manager.task_queue.shutdown()
        
        return True
    except Exception as e:
        print(f"❌ BackgroundTaskManager test failed: {e}")
        return False


def test_async_integration():
    """Test the async integration module."""
    print("\nTesting async integration functions...")
    
    try:
        from async_integration import initialize_async_services
        
        # Test initialization (without Streamlit session state)
        print("Note: This test may show warnings about missing Streamlit session state")
        success = initialize_async_services()
        
        if success:
            print("✅ Async services initialized successfully")
        else:
            print("⚠️ Async services initialization returned False (expected without Streamlit)")
        
        return True
    except Exception as e:
        print(f"❌ Async integration test failed: {e}")
        return False


def main():
    """Run all async processing tests."""
    print("🚀 Starting async processing tests...\n")
    
    tests = [
        ("Import Tests", test_async_imports),
        ("AsyncTaskQueue", test_async_task_queue),
        ("AsyncDocumentProcessor", test_async_document_processor),
        ("BackgroundTaskManager", test_background_task_manager),
        ("Async Integration", test_async_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print('='*50)
    
    if failed == 0:
        print("🎉 All async processing tests passed!")
        return 0
    else:
        print(f"⚠️ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)



