"""
Performance benchmark comparing synchronous vs asynchronous processing.
"""

import time
import sys
from typing import List, Dict, Any
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor


def create_mock_documents(count: int) -> List[Dict[str, Any]]:
    """Create mock documents for testing."""
    documents = []
    
    tech_stacks = [
        {"Python": ["Django", "Flask", "FastAPI"], "JavaScript": ["React", "Vue"]},
        {"Java": ["Spring Boot", "Hibernate"], "SQL": ["PostgreSQL", "MySQL"]},
        {"C++": ["Qt", "Boost"], "Python": ["NumPy", "Pandas"]},
        {"Go": ["Gin", "Echo"], "Docker": ["Kubernetes", "Swarm"]},
        {"Rust": ["Tokio", "Serde"], "WebAssembly": ["wasm-pack"]},
    ]
    
    for i in range(count):
        tech_stack = tech_stacks[i % len(tech_stacks)]
        documents.append({
            'filename': f'resume_{i+1}.docx',
            'text': f'Software engineer with {i+1} years of experience in various technologies.',
            'tech_stacks': tech_stack,
            'user_data': {
                'requirements': f'Job requirement {i+1}',
                'email': f'user{i+1}@example.com'
            }
        })
    
    return documents


def simulate_document_processing(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate document processing with realistic delay."""
    # Simulate processing time (text parsing, document modification, etc.)
    time.sleep(0.1 + (len(doc['text']) / 10000))  # Variable processing time
    
    return {
        'success': True,
        'filename': doc['filename'],
        'processed_text': f"Processed: {doc['text']}",
        'tech_stacks_added': len(doc['tech_stacks']),
        'processing_time': 0.1
    }


def benchmark_sync_processing(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Benchmark synchronous processing."""
    print(f"🔄 Running synchronous processing for {len(documents)} documents...")
    
    start_time = time.time()
    results = []
    
    for i, doc in enumerate(documents):
        result = simulate_document_processing(doc)
        results.append(result)
        print(f"  Processed document {i+1}/{len(documents)}: {doc['filename']}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return {
        'type': 'synchronous',
        'total_time': total_time,
        'results': results,
        'documents_per_second': len(documents) / total_time,
        'average_time_per_doc': total_time / len(documents)
    }


def benchmark_async_processing(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Benchmark asynchronous processing using ThreadPoolExecutor."""
    print(f"⚡ Running asynchronous processing for {len(documents)} documents...")
    
    start_time = time.time()
    results = []
    
    # Use ThreadPoolExecutor to simulate our async processing
    max_workers = min(8, len(documents))  # Match our AsyncTaskQueue default
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_doc = {
            executor.submit(simulate_document_processing, doc): doc 
            for doc in documents
        }
        
        # Collect results as they complete
        completed = 0
        for future in future_to_doc:
            result = future.result()
            results.append(result)
            completed += 1
            doc = future_to_doc[future]
            print(f"  Processed document {completed}/{len(documents)}: {doc['filename']}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return {
        'type': 'asynchronous',
        'total_time': total_time,
        'results': results,
        'documents_per_second': len(documents) / total_time,
        'average_time_per_doc': total_time / len(documents),
        'max_workers': max_workers
    }


def benchmark_async_task_queue(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Benchmark using our custom AsyncTaskQueue."""
    print(f"🚀 Running AsyncTaskQueue processing for {len(documents)} documents...")
    
    try:
        from async_processor import AsyncTaskQueue
        
        start_time = time.time()
        task_queue = AsyncTaskQueue(max_workers=6)
        
        # Submit all tasks
        task_ids = []
        for i, doc in enumerate(documents):
            task_id = f"benchmark_doc_{i}"
            task_queue.submit_task(task_id, simulate_document_processing, doc)
            task_ids.append(task_id)
        
        # Collect results
        results = []
        for i, task_id in enumerate(task_ids):
            result = task_queue.get_result(task_id, timeout=30)
            results.append(result)
            print(f"  Processed document {i+1}/{len(documents)}: {result['filename']}")
        
        # Shutdown queue
        task_queue.shutdown()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return {
            'type': 'AsyncTaskQueue',
            'total_time': total_time,
            'results': results,
            'documents_per_second': len(documents) / total_time,
            'average_time_per_doc': total_time / len(documents),
            'max_workers': 6
        }
    
    except Exception as e:
        print(f"❌ AsyncTaskQueue benchmark failed: {e}")
        return None


def run_benchmarks(document_counts: List[int]):
    """Run benchmarks for different document counts."""
    print("🏁 Starting Performance Benchmarks")
    print("="*60)
    
    all_results = []
    
    for count in document_counts:
        print(f"\n📊 Benchmarking with {count} documents:")
        print("-" * 40)
        
        # Create test documents
        documents = create_mock_documents(count)
        
        # Run sync benchmark
        sync_result = benchmark_sync_processing(documents)
        
        # Run async benchmark (ThreadPoolExecutor)
        async_result = benchmark_async_processing(documents)
        
        # Run AsyncTaskQueue benchmark
        queue_result = benchmark_async_task_queue(documents)
        
        # Store results
        benchmark_result = {
            'document_count': count,
            'sync': sync_result,
            'async': async_result,
            'queue': queue_result
        }
        all_results.append(benchmark_result)
        
        # Display comparison
        print(f"\n📈 Results for {count} documents:")
        print(f"  Synchronous:     {sync_result['total_time']:.2f}s ({sync_result['documents_per_second']:.2f} docs/sec)")
        print(f"  Async (threads): {async_result['total_time']:.2f}s ({async_result['documents_per_second']:.2f} docs/sec)")
        if queue_result:
            print(f"  AsyncTaskQueue:  {queue_result['total_time']:.2f}s ({queue_result['documents_per_second']:.2f} docs/sec)")
        
        # Calculate speedup
        sync_speedup = sync_result['total_time'] / async_result['total_time']
        print(f"  💨 Async speedup: {sync_speedup:.2f}x faster")
        
        if queue_result:
            queue_speedup = sync_result['total_time'] / queue_result['total_time']
            print(f"  🚀 Queue speedup: {queue_speedup:.2f}x faster")
    
    return all_results


def display_summary(all_results: List[Dict[str, Any]]):
    """Display benchmark summary."""
    print(f"\n{'='*60}")
    print("📊 PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    
    print(f"{'Documents':<12} {'Sync(s)':<10} {'Async(s)':<10} {'Queue(s)':<10} {'Speedup':<10}")
    print("-" * 60)
    
    total_sync_time = 0
    total_async_time = 0
    total_queue_time = 0
    
    for result in all_results:
        count = result['document_count']
        sync_time = result['sync']['total_time']
        async_time = result['async']['total_time']
        queue_time = result['queue']['total_time'] if result['queue'] else 0
        
        speedup = sync_time / async_time
        
        total_sync_time += sync_time
        total_async_time += async_time
        total_queue_time += queue_time
        
        queue_str = f"{queue_time:.2f}" if queue_time > 0 else "N/A"
        
        print(f"{count:<12} {sync_time:<10.2f} {async_time:<10.2f} {queue_str:<10} {speedup:<10.2f}x")
    
    overall_speedup = total_sync_time / total_async_time
    queue_speedup = total_sync_time / total_queue_time if total_queue_time > 0 else 0
    
    print("-" * 60)
    print(f"{'TOTAL':<12} {total_sync_time:<10.2f} {total_async_time:<10.2f} {total_queue_time:<10.2f} {overall_speedup:<10.2f}x")
    
    print(f"\n🎯 KEY INSIGHTS:")
    print(f"   • Async processing is {overall_speedup:.1f}x faster on average")
    if queue_speedup > 0:
        print(f"   • AsyncTaskQueue is {queue_speedup:.1f}x faster than synchronous")
    print(f"   • Processing {sum(r['document_count'] for r in all_results)} total documents")
    print(f"   • Time saved: {total_sync_time - total_async_time:.1f} seconds")
    
    print(f"\n💡 RECOMMENDATION:")
    if overall_speedup > 3:
        print("   Async processing provides EXCELLENT performance improvements!")
        print("   Users will experience significantly faster resume processing.")
    elif overall_speedup > 2:
        print("   Async processing provides GOOD performance improvements!")
        print("   Users will notice faster processing times.")
    else:
        print("   Async processing provides MODERATE performance improvements.")
        print("   Benefits increase with larger document counts.")


def main():
    """Main benchmark execution."""
    print("🚀 Resume Customizer - Async Performance Benchmark")
    print("="*60)
    
    # Test with different document counts
    document_counts = [1, 3, 5, 10, 15]
    
    try:
        # Run the benchmarks
        results = run_benchmarks(document_counts)
        
        # Display summary
        display_summary(results)
        
        print(f"\n✅ Benchmark completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
