from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Callable
import threading
import queue
import time

class ThreadManager:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, Any] = {}
        self.task_results: Dict[str, Any] = {}
        self.lock = threading.Lock()
        
    def submit_task(self, task_id: str, func: Callable, *args, priority: int = 0, **kwargs) -> None:
        """Submit a task to the thread pool with priority"""
        self.task_queue.put((priority, task_id, func, args, kwargs))
        self._process_queue()
        
    def _process_queue(self) -> None:
        """Process tasks in the queue based on priority"""
        while not self.task_queue.empty():
            priority, task_id, func, args, kwargs = self.task_queue.get()
            future = self.executor.submit(self._task_wrapper, task_id, func, *args, **kwargs)
            with self.lock:
                self.running_tasks[task_id] = future
                
    def _task_wrapper(self, task_id: str, func: Callable, *args, **kwargs) -> Any:
        """Wrapper for tasks to handle cleanup and result storage"""
        try:
            result = func(*args, **kwargs)
            with self.lock:
                self.task_results[task_id] = result
            return result
        except Exception as e:
            with self.lock:
                self.task_results[task_id] = e
            raise
        finally:
            with self.lock:
                self.running_tasks.pop(task_id, None)
                
    def get_task_result(self, task_id: str, timeout: float = None) -> Any:
        """Get the result of a completed task"""
        with self.lock:
            if task_id in self.task_results:
                result = self.task_results[task_id]
                if isinstance(result, Exception):
                    raise result
                return result
                
        if task_id in self.running_tasks:
            try:
                return self.running_tasks[task_id].result(timeout=timeout)
            except Exception as e:
                raise e
                
        raise KeyError(f"Task {task_id} not found") 