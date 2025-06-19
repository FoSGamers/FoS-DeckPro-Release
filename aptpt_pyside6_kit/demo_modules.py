"""
Demo modules for testing and demonstrating APTPT functionality.
These modules simulate various real-world scenarios and error conditions.
"""

import random
import time
from typing import List, Union, Optional

def get_temperature() -> float:
    """
    Simulate a temperature sensor reading with random drift.
    
    Returns:
        float: Simulated temperature in Fahrenheit
    """
    # Simulate sensor drift and noise
    base_temp = 70.0
    drift = random.uniform(-3, 5)
    noise = random.gauss(0, 0.5)
    return base_temp + drift + noise

def get_status_vector() -> List[float]:
    """
    Simulate a multi-sensor status vector with random variations.
    
    Returns:
        List[float]: Vector of sensor readings
    """
    # Simulate multiple sensor readings with different characteristics
    return [
        1.0 + random.uniform(-0.2, 0.2),  # Primary sensor
        0.0 + random.uniform(-0.5, 0.5),  # Secondary sensor
        -0.1 + random.uniform(-0.3, 0.3)  # Tertiary sensor
    ]

def risky_division(x: float, y: float) -> float:
    """
    Perform division with potential for error.
    
    Args:
        x: Numerator
        y: Denominator
        
    Returns:
        float: Result of division
        
    Raises:
        ZeroDivisionError: If y is zero
    """
    return x / y

def simulate_network_request(timeout: float = 1.0) -> dict:
    """
    Simulate a network request with potential timeouts and errors.
    
    Args:
        timeout: Maximum time to wait for response
        
    Returns:
        dict: Simulated response data
        
    Raises:
        TimeoutError: If request takes too long
        ConnectionError: If connection fails
    """
    # Simulate network latency
    time.sleep(random.uniform(0.1, timeout * 1.5))
    
    # Simulate random errors
    if random.random() < 0.1:  # 10% chance of timeout
        raise TimeoutError("Request timed out")
    elif random.random() < 0.05:  # 5% chance of connection error
        raise ConnectionError("Failed to connect to server")
    
    # Return simulated response
    return {
        "status": "success",
        "data": {
            "id": random.randint(1000, 9999),
            "timestamp": time.time(),
            "value": random.uniform(0, 100)
        }
    }

def process_data(data: List[float], threshold: Optional[float] = None) -> dict:
    """
    Process a list of data points with validation and analysis.
    
    Args:
        data: List of data points to process
        threshold: Optional threshold for outlier detection
        
    Returns:
        dict: Processing results including statistics and outliers
        
    Raises:
        ValueError: If data is empty or invalid
    """
    if not data:
        raise ValueError("Empty data list")
    
    if threshold is None:
        threshold = 2.0  # Default threshold
    
    # Calculate basic statistics
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    
    # Detect outliers
    outliers = [x for x in data if abs(x - mean) > threshold * std_dev]
    
    return {
        "mean": mean,
        "std_dev": std_dev,
        "outliers": outliers,
        "count": len(data),
        "threshold": threshold
    } 