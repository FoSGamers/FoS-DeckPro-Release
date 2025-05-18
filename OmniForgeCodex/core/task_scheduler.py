from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
import threading
import time
import logging
import json
from pathlib import Path
import schedule
import croniter
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from collections import defaultdict

class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class TaskStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskType(Enum):
    ONE_TIME = "one_time"
    PERIODIC = "periodic"
    CRON = "cron"
    INTERVAL = "interval"
    EVENT_DRIVEN = "event_driven"

@dataclass
class TaskStatistics:
    execution_times: List[float]
    success_count: int
    failure_count: int

    def record(self, duration: float, success: bool):
        self.execution_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def average_time(self) -> float:
        return sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0.0

    def total_runs(self) -> int:
        return self.success_count + self.failure_count

@dataclass
class TaskInfo:
    id: str
    name: str
    type: TaskType
    status: TaskStatus
    priority: TaskPriority
    schedule: str  # cron expression or interval
    start_time: datetime
    end_time: Optional[datetime]
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    max_retries: int
    retry_count: int
    timeout: int
    handler: Callable
    args: Tuple
    kwargs: Dict[str, Any]
    result: Any
    error_message: Optional[str] = None
    dependencies: List[str] = None  # List of task IDs this task depends on
    group: Optional[str] = None     # Group name
    statistics: TaskStatistics = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.statistics is None:
            self.statistics = TaskStatistics([], 0, 0)

class TaskScheduler(QObject):
    task_scheduled = Signal(TaskInfo)  # task_info
    task_started = Signal(TaskInfo)  # task_info
    task_completed = Signal(TaskInfo)  # task_info
    task_failed = Signal(TaskInfo)  # task_info
    task_cancelled = Signal(TaskInfo)  # task_info
    
    def __init__(self):
        super().__init__()
        self.tasks_dir = Path("tasks")
        self.config_dir = Path("config") / "tasks"
        
        # Task tracking
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, threading.Thread] = {}
        
        # Task settings
        self.max_concurrent_tasks = 5
        self.default_timeout = 300  # 5 minutes
        self.default_max_retries = 3
        self.cleanup_interval = 3600  # 1 hour
        
        # Task groups
        self.task_groups: Dict[str, List[str]] = defaultdict(list)  # group_name -> [task_id]
        
        # Setup
        self._setup_logging()
        self._setup_directories()
        self._load_tasks()
        self._start_scheduler()
        self._start_cleanup()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("scheduler")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = Path("logs") / "scheduler.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.tasks_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
    def _load_tasks(self):
        """Load saved tasks"""
        try:
            # Load task configurations
            for config_file in self.config_dir.glob("*.json"):
                with open(config_file, 'r') as f:
                    task_data = json.load(f)
                    task_info = self._create_task_info(task_data)
                    self.tasks[task_info.id] = task_info
                    
            # Schedule loaded tasks
            for task_info in self.tasks.values():
                if task_info.status == TaskStatus.SCHEDULED:
                    self._schedule_task(task_info)
                    
        except Exception as e:
            self.logger.error(f"Error loading tasks: {e}")
            
    def _start_scheduler(self):
        """Start task scheduler"""
        def run_scheduler():
            while True:
                try:
                    # Check for tasks to run
                    now = datetime.now()
                    for task_info in self.tasks.values():
                        if (task_info.status == TaskStatus.SCHEDULED and
                            task_info.next_run and
                            task_info.next_run <= now):
                            self._run_task(task_info)
                            
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error in scheduler: {e}")
                    
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
    def _start_cleanup(self):
        """Start task cleanup"""
        def cleanup():
            while True:
                try:
                    self._cleanup_tasks()
                    time.sleep(self.cleanup_interval)
                except Exception as e:
                    self.logger.error(f"Error in cleanup: {e}")
                    
        self.cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_thread.start()
        
    def _validate_dependencies(self, task_id: str, dependencies: List[str]) -> bool:
        """Validate task dependencies and check for cycles"""
        try:
            # Check if all dependencies exist
            for dep_id in dependencies:
                if dep_id not in self.tasks:
                    self.logger.error(f"Dependency task not found: {dep_id}")
                    return False
                    
            # Check for cycles using DFS
            visited = set()
            path = set()
            
            def has_cycle(current_id: str) -> bool:
                if current_id in path:
                    return True
                if current_id in visited:
                    return False
                    
                visited.add(current_id)
                path.add(current_id)
                
                for dep_id in self.tasks[current_id].dependencies:
                    if has_cycle(dep_id):
                        return True
                        
                path.remove(current_id)
                return False
                
            # Check for cycles starting from the new task
            if has_cycle(task_id):
                self.logger.error(f"Circular dependency detected for task: {task_id}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating dependencies: {e}")
            return False

    def schedule_task(self, name: str, handler: Callable, task_type: TaskType,
                     schedule: str, priority: TaskPriority = TaskPriority.NORMAL,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     max_retries: Optional[int] = None,
                     timeout: Optional[int] = None,
                     dependencies: Optional[List[str]] = None,
                     group: Optional[str] = None,
                     *args, **kwargs) -> Optional[TaskInfo]:
        """Schedule a new task"""
        try:
            # Create task info
            task_id = str(uuid.uuid4())
            
            # Validate dependencies before creating task
            if dependencies and not self._validate_dependencies(task_id, dependencies):
                return None
            
            task_info = TaskInfo(
                id=task_id,
                name=name,
                type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                schedule=schedule,
                start_time=start_time or datetime.now(),
                end_time=end_time,
                last_run=None,
                next_run=None,
                max_retries=max_retries or self.default_max_retries,
                retry_count=0,
                timeout=timeout or self.default_timeout,
                handler=handler,
                args=args,
                kwargs=kwargs,
                result=None,
                error_message=None,
                dependencies=dependencies or [],
                group=group,
                statistics=TaskStatistics([], 0, 0)
            )
            
            # Add to tasks
            self.tasks[task_id] = task_info
            
            # Save configuration
            self._save_task_config(task_info)
            
            # Schedule task
            self._schedule_task(task_info)
            
            # Emit signal
            self.task_scheduled.emit(task_info)
            
            if group:
                self.task_groups[group].append(task_id)
            
            return task_info
            
        except Exception as e:
            self.logger.error(f"Error scheduling task: {e}")
            return None
            
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        try:
            if task_id not in self.tasks:
                raise KeyError(f"Task not found: {task_id}")
                
            task_info = self.tasks[task_id]
            if task_info.status not in [TaskStatus.PENDING, TaskStatus.SCHEDULED]:
                raise ValueError(f"Task cannot be cancelled: {task_id}")
                
            # Update status
            task_info.status = TaskStatus.CANCELLED
            self._save_task_config(task_info)
            
            # Emit signal
            self.task_cancelled.emit(task_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling task: {e}")
            return False
            
    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        try:
            if task_id not in self.tasks:
                raise KeyError(f"Task not found: {task_id}")
                
            task_info = self.tasks[task_id]
            if task_info.status != TaskStatus.SCHEDULED:
                raise ValueError(f"Task cannot be paused: {task_id}")
                
            # Update status
            task_info.status = TaskStatus.PAUSED
            self._save_task_config(task_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing task: {e}")
            return False
            
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        try:
            if task_id not in self.tasks:
                raise KeyError(f"Task not found: {task_id}")
                
            task_info = self.tasks[task_id]
            if task_info.status != TaskStatus.PAUSED:
                raise ValueError(f"Task cannot be resumed: {task_id}")
                
            # Update status
            task_info.status = TaskStatus.SCHEDULED
            self._save_task_config(task_info)
            
            # Reschedule task
            self._schedule_task(task_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming task: {e}")
            return False
            
    def _schedule_task(self, task_info: TaskInfo):
        """Schedule a task based on its type"""
        try:
            if task_info.type == TaskType.ONE_TIME:
                # Schedule one-time task
                if task_info.start_time > datetime.now():
                    task_info.next_run = task_info.start_time
                    task_info.status = TaskStatus.SCHEDULED
                    
            elif task_info.type == TaskType.PERIODIC:
                # Schedule periodic task
                schedule.every().day.at(task_info.schedule).do(
                    self._run_task, task_info
                )
                task_info.next_run = datetime.now() + timedelta(days=1)
                task_info.status = TaskStatus.SCHEDULED
                
            elif task_info.type == TaskType.CRON:
                # Schedule cron task
                cron = croniter.croniter(task_info.schedule, datetime.now())
                task_info.next_run = cron.get_next(datetime)
                task_info.status = TaskStatus.SCHEDULED
                
            elif task_info.type == TaskType.INTERVAL:
                # Schedule interval task
                interval = int(task_info.schedule)
                task_info.next_run = datetime.now() + timedelta(seconds=interval)
                task_info.status = TaskStatus.SCHEDULED
                
            # Save configuration
            self._save_task_config(task_info)
            
        except Exception as e:
            self.logger.error(f"Error scheduling task: {e}")
            task_info.status = TaskStatus.FAILED
            task_info.error_message = str(e)
            self._save_task_config(task_info)
            
    def _run_task(self, task_info: TaskInfo):
        """Run a task"""
        try:
            # Check if task should run
            if task_info.status != TaskStatus.SCHEDULED:
                return
                
            # Check if task has ended
            if task_info.end_time and datetime.now() > task_info.end_time:
                task_info.status = TaskStatus.COMPLETED
                self._save_task_config(task_info)
                return
                
            # Check if all dependencies are completed
            for dep_id in task_info.dependencies:
                dep_task = self.tasks.get(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    task_info.next_run = datetime.now() + timedelta(seconds=10)
                    self._save_task_config(task_info)
                    return
                
            # Update status
            task_info.status = TaskStatus.RUNNING
            task_info.last_run = datetime.now()
            self._save_task_config(task_info)
            
            # Emit signal
            self.task_started.emit(task_info)
            
            # Run task
            def run():
                start_time = time.time()
                try:
                    result = task_info.handler(*task_info.args, **task_info.kwargs)
                    task_info.result = result
                    task_info.status = TaskStatus.COMPLETED
                    duration = time.time() - start_time
                    task_info.statistics.record(duration, True)
                except Exception as e:
                    task_info.error_message = str(e)
                    duration = time.time() - start_time
                    task_info.statistics.record(duration, False)
                    if task_info.retry_count < task_info.max_retries:
                        task_info.retry_count += 1
                        task_info.status = TaskStatus.SCHEDULED
                        self._schedule_task(task_info)
                    else:
                        task_info.status = TaskStatus.FAILED
                        self.task_failed.emit(task_info)
                        
                finally:
                    self._save_task_config(task_info)
                    if task_info.status == TaskStatus.COMPLETED:
                        self.task_completed.emit(task_info)
                        
            # Start task thread
            thread = threading.Thread(target=run)
            thread.start()
            self.running_tasks[task_info.id] = thread
            
        except Exception as e:
            self.logger.error(f"Error running task: {e}")
            task_info.status = TaskStatus.FAILED
            task_info.error_message = str(e)
            self._save_task_config(task_info)
            self.task_failed.emit(task_info)
            
    def _cleanup_tasks(self):
        """Cleanup completed and failed tasks"""
        try:
            # Remove old completed tasks
            cutoff_date = datetime.now() - timedelta(days=7)
            for task_id, task_info in list(self.tasks.items()):
                if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and
                    task_info.last_run and
                    task_info.last_run < cutoff_date):
                    self._remove_task(task_id)
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up tasks: {e}")
            
    def _remove_task(self, task_id: str):
        """Remove a task"""
        try:
            task_info = self.tasks[task_id]
            
            # Remove configuration
            config_file = self.config_dir / f"{task_id}.json"
            if config_file.exists():
                config_file.unlink()
                
            # Remove from tasks
            del self.tasks[task_id]
            
        except Exception as e:
            self.logger.error(f"Error removing task: {e}")
            
    def _create_task_info(self, task_data: Dict[str, Any]) -> TaskInfo:
        """Create task info from data"""
        # Create statistics object
        stats_data = task_data.get("statistics", {})
        statistics = TaskStatistics(
            execution_times=stats_data.get("execution_times", []),
            success_count=stats_data.get("success_count", 0),
            failure_count=stats_data.get("failure_count", 0)
        )
        
        return TaskInfo(
            id=task_data["id"],
            name=task_data["name"],
            type=TaskType(task_data["type"]),
            status=TaskStatus(task_data["status"]),
            priority=TaskPriority(task_data["priority"]),
            schedule=task_data["schedule"],
            start_time=datetime.fromisoformat(task_data["start_time"]),
            end_time=datetime.fromisoformat(task_data["end_time"]) if task_data.get("end_time") else None,
            last_run=datetime.fromisoformat(task_data["last_run"]) if task_data.get("last_run") else None,
            next_run=datetime.fromisoformat(task_data["next_run"]) if task_data.get("next_run") else None,
            max_retries=task_data["max_retries"],
            retry_count=task_data["retry_count"],
            timeout=task_data["timeout"],
            handler=eval(task_data["handler"]),  # Note: This is a security risk, should use proper serialization
            args=tuple(task_data["args"]),
            kwargs=task_data["kwargs"],
            result=task_data.get("result"),
            error_message=task_data.get("error_message"),
            # New fields
            dependencies=task_data.get("dependencies", []),
            group=task_data.get("group"),
            statistics=statistics
        )
        
    def _save_task_config(self, task_info: TaskInfo):
        """Save task configuration"""
        config_file = self.config_dir / f"{task_info.id}.json"
        config_data = {
            "id": task_info.id,
            "name": task_info.name,
            "type": task_info.type.value,
            "status": task_info.status.value,
            "priority": task_info.priority.value,
            "schedule": task_info.schedule,
            "start_time": task_info.start_time.isoformat(),
            "end_time": task_info.end_time.isoformat() if task_info.end_time else None,
            "last_run": task_info.last_run.isoformat() if task_info.last_run else None,
            "next_run": task_info.next_run.isoformat() if task_info.next_run else None,
            "max_retries": task_info.max_retries,
            "retry_count": task_info.retry_count,
            "timeout": task_info.timeout,
            "handler": task_info.handler.__name__,  # Note: This is a security risk, should use proper serialization
            "args": task_info.args,
            "kwargs": task_info.kwargs,
            "result": task_info.result,
            "error_message": task_info.error_message,
            # New fields
            "dependencies": task_info.dependencies,
            "group": task_info.group,
            "statistics": {
                "execution_times": task_info.statistics.execution_times,
                "success_count": task_info.statistics.success_count,
                "failure_count": task_info.statistics.failure_count
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
            
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task info"""
        return self.tasks.get(task_id)
        
    def get_tasks(self, task_type: Optional[TaskType] = None,
                 status: Optional[TaskStatus] = None) -> List[TaskInfo]:
        """Get filtered tasks"""
        tasks = list(self.tasks.values())
        
        if task_type:
            tasks = [t for t in tasks if t.type == task_type]
        if status:
            tasks = [t for t in tasks if t.status == status]
            
        return tasks 

    # --- Task Group Management ---
    def get_group_tasks(self, group: str) -> List[TaskInfo]:
        return [self.tasks[tid] for tid in self.task_groups.get(group, [])]

    def cancel_group(self, group: str):
        for tid in self.task_groups.get(group, []):
            self.cancel_task(tid)

    def group_statistics(self, group: str) -> Dict[str, Any]:
        stats = [self.tasks[tid].statistics for tid in self.task_groups.get(group, [])]
        total_runs = sum(s.total_runs() for s in stats)
        avg_time = sum(s.average_time() for s in stats) / len(stats) if stats else 0.0
        return {
            "total_runs": total_runs,
            "average_time": avg_time,
            "successes": sum(s.success_count for s in stats),
            "failures": sum(s.failure_count for s in stats),
        }

    def create_group(self, name: str) -> bool:
        """Create a new task group"""
        try:
            if name in self.task_groups:
                self.logger.warning(f"Group already exists: {name}")
                return False
            
            self.task_groups[name] = []
            self._save_group_config(name)
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating group: {e}")
            return False

    def delete_group(self, name: str) -> bool:
        """Delete a task group"""
        try:
            if name not in self.task_groups:
                self.logger.warning(f"Group not found: {name}")
                return False
            
            # Remove group from tasks
            for task_id in self.task_groups[name]:
                if task_id in self.tasks:
                    self.tasks[task_id].group = None
                    self._save_task_config(self.tasks[task_id])
                
            # Remove group
            del self.task_groups[name]
            self._remove_group_config(name)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting group: {e}")
            return False

    def _save_group_config(self, group_name: str):
        """Save group configuration"""
        config_file = self.config_dir / "groups" / f"{group_name}.json"
        config_file.parent.mkdir(exist_ok=True)
        
        config_data = {
            "name": group_name,
            "tasks": self.task_groups[group_name]
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    def _remove_group_config(self, group_name: str):
        """Remove group configuration"""
        config_file = self.config_dir / "groups" / f"{group_name}.json"
        if config_file.exists():
            config_file.unlink()

    def get_task_statistics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific task"""
        try:
            task_info = self.tasks.get(task_id)
            if not task_info:
                return None
            
            stats = task_info.statistics
            return {
                "total_runs": stats.total_runs(),
                "success_rate": stats.success_count / stats.total_runs() if stats.total_runs() > 0 else 0,
                "average_time": stats.average_time(),
                "success_count": stats.success_count,
                "failure_count": stats.failure_count,
                "last_execution_time": stats.execution_times[-1] if stats.execution_times else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting task statistics: {e}")
            return None

    def get_group_statistics(self, group: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a task group"""
        try:
            if group not in self.task_groups:
                return None
            
            tasks = [self.tasks[tid] for tid in self.task_groups[group] if tid in self.tasks]
            if not tasks:
                return None
            
            total_runs = sum(t.statistics.total_runs() for t in tasks)
            total_success = sum(t.statistics.success_count for t in tasks)
            total_failure = sum(t.statistics.failure_count for t in tasks)
            avg_time = sum(t.statistics.average_time() for t in tasks) / len(tasks)
            
            return {
                "total_tasks": len(tasks),
                "total_runs": total_runs,
                "success_rate": total_success / total_runs if total_runs > 0 else 0,
                "average_time": avg_time,
                "success_count": total_success,
                "failure_count": total_failure
            }
            
        except Exception as e:
            self.logger.error(f"Error getting group statistics: {e}")
            return None 