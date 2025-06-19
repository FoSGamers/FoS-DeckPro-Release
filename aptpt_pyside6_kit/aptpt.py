import traceback
import json
from datetime import datetime
from aptpt_pyside6_kit.aptpt_config import get_config
import functools

def log_aptpt_event(event, description, variables, exception=None, level="ERROR"):
    """Log an APTPT event with full context and stack trace."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "event": event,
        "description": description,
        "variables": variables,
        "exception": str(exception) if exception else None,
        "traceback": traceback.format_exc() if exception else None,
    }
    with open("aptpt_error_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print("[APTPT]", log_entry)

def aptpt_wrapper(target, threshold=None, autoadapt=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[APTPT] Wrapping function: {func.__name__}")
            cfg = get_config(func.__name__)
            thres = threshold if threshold is not None else cfg.get("threshold", 0.05)
            try:
                result = func(*args, **kwargs)
                # Adaptive: support scalar, vector, matrix
                if isinstance(result, (int, float)):
                    error = abs(result - target)
                elif hasattr(result, "__len__"):
                    error = float(sum((r-t)**2 for r, t in zip(result, target))**0.5)
                else:
                    error = 0
                if error > thres:
                    log_aptpt_event(
                        event=func.__name__,
                        description="Deviation from target detected",
                        variables={"target": target, "result": result, "error": error, "threshold": thres},
                        level="WARN"
                    )
                    if autoadapt and "autoadapt" in cfg and callable(cfg["autoadapt"]):
                        result = cfg["autoadapt"](result, target, error)
                return result
            except Exception as e:
                log_aptpt_event(
                    event=func.__name__,
                    description="Exception during execution",
                    variables={"target": target, "args": args, "kwargs": kwargs},
                    exception=e,
                    level="ERROR"
                )
                return None
        return wrapper
    return decorator 