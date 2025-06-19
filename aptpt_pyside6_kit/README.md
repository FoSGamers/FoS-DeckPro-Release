# APTPT + PySide6 Adaptive Developer Kit

A comprehensive, plug-and-play developer kit for building robust, adaptive, and AI-assist-ready desktop applications with PySide6.

## Features

- **Universal Error Tracking**: Systematic feedback, error, and state tracking across GUI and core logic
- **Adaptive Function Wrapping**: Not just error catching, but measuring drift and adapting to changes
- **Live Monitoring**: Real-time system state and error monitoring with a dockable widget
- **Enhanced Error UI**: Beautiful, informative error dialogs with full context and recovery options
- **Deep Logging**: Structured, machine-readable logs for AI-assisted debugging and improvement
- **Runtime Configuration**: Flexible configuration system for thresholds, targets, and behavior
- **Demo Application**: Complete example showing all features in action

## Quick Start

1. Copy the `aptpt_pyside6_kit` directory into your project
2. Install dependencies:
   ```bash
   pip install PySide6
   ```
3. Import and use APTPT in your code:
   ```python
   from aptpt_pyside6_kit.aptpt import aptpt_wrapper
   from aptpt_pyside6_kit.aptpt_error_ui import show_aptpt_error_dialog
   from aptpt_pyside6_kit.aptpt_monitor import APTPTMonitor
   ```

## Core Components

### 1. `aptpt.py`: Universal Feedback and Logging

The core module providing:
- Function wrapping with error tracking
- Adaptive behavior based on targets
- Structured logging of all events
- Support for scalar, vector, and matrix operations

### 2. `aptpt_config.py`: Runtime Configuration

Flexible configuration system for:
- Per-function thresholds and targets
- Auto-adaptation behavior
- Runtime modification of parameters
- Default values and fallbacks

### 3. `aptpt_error_ui.py`: Enhanced Error UI

Beautiful error handling with:
- Detailed error dialogs
- Context-rich error information
- Recovery options
- Warning system for non-critical issues

### 4. `aptpt_monitor.py`: Live System Monitor

Real-time monitoring with:
- Dockable widget for system state
- Live error and warning display
- Auto-refresh capability
- Color-coded status indicators

## Usage Examples

### Basic Function Wrapping

```python
from aptpt_pyside6_kit.aptpt import aptpt_wrapper

def my_function(x, y):
    return x + y

# Wrap with target and threshold
result = aptpt_wrapper(
    target=10,  # Expected result
    func=my_function,
    x=5,
    y=5,
    threshold=0.1  # Optional threshold
)
```

### Error Handling

```python
from aptpt_pyside6_kit.aptpt_error_ui import show_aptpt_error_dialog

try:
    # Your code here
    result = risky_operation()
except Exception as e:
    show_aptpt_error_dialog(
        parent=self,  # Your widget
        event="operation_failed",
        description="Failed to perform operation",
        variables={"param1": value1, "param2": value2},
        exception=e
    )
```

### Adding the Monitor

```python
from aptpt_pyside6_kit.aptpt_monitor import APTPTMonitor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... other initialization ...
        
        # Add the monitor
        self.aptpt_monitor = APTPTMonitor(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.aptpt_monitor)
```

## Extending APTPT

### Custom Auto-adaptation

```python
def my_adaptation(result, target, error):
    # Implement your adaptation logic
    return adjusted_result

# Register in config
configs = {
    "my_function": {
        "threshold": 0.1,
        "autoadapt": my_adaptation
    }
}
```

### Custom Error Handling

```python
class CustomErrorDialog(APTPTErrorDialog):
    def __init__(self, parent, event, description, variables, exception=None):
        super().__init__(parent, event, description, variables, exception)
        # Add custom UI elements or behavior
```

## Best Practices

1. **Wrap Critical Functions**: Use `aptpt_wrapper` for functions where accuracy or reliability is important
2. **Set Meaningful Targets**: Define clear targets and thresholds for each wrapped function
3. **Monitor System State**: Always include the `APTPTMonitor` in your main window
4. **Use Structured Logging**: Take advantage of the built-in logging for debugging and improvement
5. **Implement Auto-adaptation**: Add custom adaptation logic for critical functions
6. **Keep Configuration Updated**: Maintain accurate configuration for all wrapped functions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PySide6 team for the excellent Qt bindings
- The Python community for inspiration and best practices 