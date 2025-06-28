import json
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime
from .aptpt_config import get_config, update_config
from .aptpt_logger import log_aptpt_event

def log_aptpt_event(
    level: str,
    description: str,
    variables: Optional[Dict[str, Any]] = None,
    exception: Optional[Exception] = None
) -> None:
    """Log an APTPT event with full context."""
    try:
        event = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'description': description,
            'variables': variables or {},
        }
        
        if exception:
            event['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        # Write to log file
        with open('aptpt_error_log.jsonl', 'a') as f:
            f.write(json.dumps(event) + '\n')
    except Exception as e:
        print(f"Failed to log APTPT event: {e}")

def aptpt_wrapper(target: float = 1.0, threshold: Optional[float] = None, autoadapt: bool = True):
    """
    Decorator factory for adaptive function execution with error tracking.
    Usage: @aptpt_wrapper(target=..., threshold=..., autoadapt=...)
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # Get function configuration
                config = get_config(func.__name__)
                thres = threshold if threshold is not None else config['threshold']
                # Execute function
                result = func(*args, **kwargs)
                # Calculate execution time
                execution_time = time.time() - start_time
                # Log performance
                log_aptpt_event(
                    'performance',
                    f'Function {func.__name__} executed',
                    {
                        'execution_time': execution_time,
                        'threshold': thres,
                        'target': target
                    }
                )
                # Check if performance is within threshold
                if execution_time > thres:
                    log_aptpt_event(
                        'warning',
                        f'Function {func.__name__} exceeded threshold',
                        {
                            'execution_time': execution_time,
                            'threshold': thres,
                            'target': target
                        }
                    )
                    # Auto-adapt if enabled
                    if autoadapt and config['autoadapt']:
                        # Calculate new threshold
                        new_threshold = thres * 1.2
                        update_config(func.__name__, {'threshold': new_threshold})
                        log_aptpt_event(
                            'adaptive',
                            f'Increased threshold for {func.__name__}',
                            {
                                'old_threshold': thres,
                                'new_threshold': new_threshold
                            }
                        )
                return result
            except Exception as e:
                log_aptpt_event(
                    'error',
                    f'Function {func.__name__} failed',
                    {
                        'args': args,
                        'kwargs': kwargs,
                        'execution_time': time.time() - start_time
                    },
                    e
                )
                raise
        return wrapper
    return decorator

def calculate_error(actual: float, target: float) -> float:
    """Calculate error between actual and target values."""
    return abs(actual - target) / target if target != 0 else float('inf')

def log_deviation(
    function_name: str,
    actual: float,
    target: float,
    threshold: float
) -> None:
    """Log deviation from target performance."""
    error = calculate_error(actual, target)
    if error > threshold:
        log_aptpt_event(
            'warning',
            f'Performance deviation detected in {function_name}',
            {
                'actual': actual,
                'target': target,
                'error': error,
                'threshold': threshold
            }
        )

def adaptive_execute(
    func: Callable,
    *args: Any,
    target_time: float,
    max_retries: int = 3,
    **kwargs: Any
) -> Tuple[Any, float]:
    """Execute function with adaptive retries to meet target time."""
    best_result = None
    best_time = float('inf')
    
    for attempt in range(max_retries):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time < best_time:
                best_result = result
                best_time = execution_time
            
            # Log attempt
            log_aptpt_event(
                'adaptive',
                f'Adaptive execution attempt {attempt + 1}',
                {
                    'execution_time': execution_time,
                    'target_time': target_time,
                    'best_time': best_time
                }
            )
            
            # If we're within 10% of target, we're good
            if calculate_error(execution_time, target_time) < 0.1:
                break
                
        except Exception as e:
            log_aptpt_event(
                'error',
                f'Adaptive execution attempt {attempt + 1} failed',
                {'error': str(e)}
            )
            if attempt == max_retries - 1:
                raise
    
    return best_result, best_time

def monitor_performance(
    func: Callable,
    *args: Any,
    target_time: float,
    window_size: int = 10,
    **kwargs: Any
) -> None:
    """Monitor function performance over time and adjust thresholds."""
    execution_times = []
    
    def wrapped_func(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        execution_times.append(execution_time)
        if len(execution_times) > window_size:
            execution_times.pop(0)
        
        # Calculate average execution time
        avg_time = sum(execution_times) / len(execution_times)
        
        # Log performance
        log_aptpt_event(
            'performance',
            f'Function {func.__name__} performance',
            {
                'execution_time': execution_time,
                'average_time': avg_time,
                'target_time': target_time
            }
        )
        
        # Adjust threshold if needed
        if len(execution_times) == window_size:
            config = get_config(func.__name__)
            if avg_time > config['threshold'] * 1.5:
                new_threshold = config['threshold'] * 1.2
                update_config(func.__name__, {'threshold': new_threshold})
                log_aptpt_event(
                    'adaptive',
                    f'Increased threshold for {func.__name__}',
                    {
                        'old_threshold': config['threshold'],
                        'new_threshold': new_threshold,
                        'average_time': avg_time
                    }
                )
        
        return result
    
    return wrapped_func 