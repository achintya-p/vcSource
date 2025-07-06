"""
Parallel processing utilities for the VC Sourcing Agent.
"""
import asyncio
import concurrent.futures
from typing import List, Callable, Any, Dict
from functools import partial
import time
from tqdm import tqdm

from utils.logger import get_logger

logger = get_logger(__name__)

class ParallelProcessor:
    """Handle parallel processing of data."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    def process_batch(self, items: List[Any], processor_func: Callable, 
                     batch_size: int = 10, desc: str = "Processing") -> List[Any]:
        """Process items in parallel batches."""
        results = []
        
        # Process in batches to avoid overwhelming resources
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Submit batch to thread pool
            futures = []
            for item in batch:
                future = self.executor.submit(processor_func, item)
                futures.append(future)
            
            # Collect results with progress bar
            batch_results = []
            for future in tqdm(concurrent.futures.as_completed(futures), 
                             total=len(futures), desc=f"{desc} batch {i//batch_size + 1}"):
                try:
                    result = future.result()
                    if result:
                        batch_results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing item: {e}")
            
            results.extend(batch_results)
            
            # Small delay between batches to be respectful
            time.sleep(0.1)
        
        return results
    
    def process_with_semaphore(self, items: List[Any], processor_func: Callable,
                              max_concurrent: int = 5, desc: str = "Processing") -> List[Any]:
        """Process items with controlled concurrency using semaphore."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item):
            async with semaphore:
                return await processor_func(item)
        
        async def process_all():
            tasks = [process_item(item) for item in items]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(process_all())
        finally:
            loop.close()
        
        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]
        return valid_results

class CachingProcessor:
    """Add caching to expensive operations."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour default
    
    def get_cached_result(self, key: str):
        """Get cached result if still valid."""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                del self.cache[key]
        return None
    
    def cache_result(self, key: str, result: Any):
        """Cache a result with timestamp."""
        self.cache[key] = (result, time.time())
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()

class BatchProcessor:
    """Process data in optimized batches."""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
    
    def process_large_dataset(self, items: List[Any], processor_func: Callable,
                            desc: str = "Processing") -> List[Any]:
        """Process large datasets efficiently."""
        results = []
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}/{total_batches}")
            
            batch_results = []
            for item in tqdm(batch, desc=f"Batch {i//self.batch_size + 1}"):
                try:
                    result = processor_func(item)
                    if result:
                        batch_results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing item: {e}")
            
            results.extend(batch_results)
            
            # Yield intermediate results for memory efficiency
            yield batch_results 