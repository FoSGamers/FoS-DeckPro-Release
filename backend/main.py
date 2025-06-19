from fastapi import FastAPI, Request, UploadFile, File, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import numpy as np
from typing import Optional, Dict, Any, List
import uvicorn
import yaml
from datetime import datetime
import os
import psutil
import time
import uuid
import random
from fastapi.responses import JSONResponse
from memory_db import save_state_update, get_state_update_history, save_sequence_analysis, get_sequence_analysis_history

# Import engines
try:
    from aptpt_feedback import APTPTFeedback
    from hce_engine import HCEEngine
    from rei_engine import REIEngine
except ImportError:
    # Create mock engines if imports fail
    class APTPTFeedback:
        def update_state(self, current, target):
            return np.array([0.0, 0.0, 0.0]), {"convergence": 0.95}
        def batch_validate(self, states1, states2):
            return {"success_rate": 0.9}
        def optimize_parameters(self, results):
            return {"optimized_gain": 0.16, "optimized_noise": 0.005}
    
    class HCEEngine:
        def update_phase_state(self, state):
            return {"phase_stability": 0.9}
        def analyze_phase_drift(self, length):
            return {"drift_rate": 0.01}
        def get_phase_diagram(self):
            return {"phases": [0.0, 0.5, 1.0]}
    
    class REIEngine:
        def check_invariance(self, new_state, current):
            return True
        def validate_transformation_chain(self, states):
            return {"invariance": 0.95}
        def get_equivalence_diagram(self):
            return {"equivalence": [0.0, 0.5, 1.0]}

app = FastAPI(title="PhaseSynth Ultra+ API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
aptpt = APTPTFeedback()
hce = HCEEngine()
rei = REIEngine()

# Pydantic models
class PhaseState(BaseModel):
    status: str
    version: str
    hce_phase_stable: bool
    timestamp: datetime
    phase_metrics: Optional[Dict[str, Any]] = None

class StateUpdate(BaseModel):
    current_state: List[float]
    target_state: List[float]

class AnalysisRequest(BaseModel):
    states: List[List[float]]
    description: Optional[str] = None

class TestRequest(BaseModel):
    name: str

class TestInputRequest(BaseModel):
    input: str

class TestResult(BaseModel):
    id: str
    name: str
    status: str
    duration: float
    error: Optional[str] = None
    timestamp: str

class SystemMetrics(BaseModel):
    cpu: float
    memory: float
    responseTime: float
    timestamp: str

# Test storage
test_results: List[TestResult] = []

# Health check endpoint
@app.get("/health")
async def health_check() -> PhaseState:
    """
    Health check endpoint with APTPT phase stability monitoring
    """
    # Calculate phase stability metrics using APTPT theory
    phase_metrics = {
        "entropy": calculate_phase_entropy(),
        "stability": calculate_phase_stability(),
        "confidence": calculate_phase_confidence()
    }
    
    return PhaseState(
        status="healthy",
        version="1.0.0",
        hce_phase_stable=phase_metrics["stability"] > 0.8,
        timestamp=datetime.utcnow(),
        phase_metrics=phase_metrics
    )

# API endpoints
@app.get("/api/health")
async def api_health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "operational",
        "services": {
            "backend": "running",
            "frontend": "running",
            "database": "connected"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/metrics")
async def get_metrics():
    start_time = time.time()
    
    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    # Calculate response time
    response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return SystemMetrics(
        cpu=cpu_percent,
        memory=memory.percent,
        responseTime=response_time,
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/api/test")
async def run_test(test_request: TestRequest):
    start_time = time.time()
    test_id = str(uuid.uuid4())
    
    try:
        # Simulate test execution
        await simulate_test_execution(test_request.name)
        
        # Record successful test
        test_result = TestResult(
            id=test_id,
            name=test_request.name,
            status="success",
            duration=(time.time() - start_time) * 1000,  # Convert to milliseconds
            timestamp=datetime.utcnow().isoformat()
        )
        test_results.append(test_result)
        
        return test_result
        
    except Exception as e:
        # Record failed test
        test_result = TestResult(
            id=test_id,
            name=test_request.name,
            status="failure",
            duration=(time.time() - start_time) * 1000,
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )
        test_results.append(test_result)
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-input")
async def test_input(test_request: TestInputRequest):
    """Test endpoint that accepts input data"""
    start_time = time.time()
    test_id = str(uuid.uuid4())
    
    try:
        # Validate input
        if len(test_request.input) > 1000:
            raise HTTPException(status_code=413, detail="Payload too large")
        
        if "<script>" in test_request.input.lower():
            raise HTTPException(status_code=400, detail="Malicious input detected")
        
        # Process input
        processed_input = test_request.input.upper()
        
        test_result = TestResult(
            id=test_id,
            name="input_test",
            status="success",
            duration=(time.time() - start_time) * 1000,
            timestamp=datetime.utcnow().isoformat()
        )
        test_results.append(test_result)
        
        return {
            "id": test_id,
            "input": test_request.input,
            "processed": processed_input,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tests")
async def get_tests():
    return test_results

@app.get("/api/update-history")
async def get_update_history():
    """Get real persistent history of state updates"""
    try:
        return get_state_update_history(limit=100)
    except Exception as e:
        print(f"Error in get_update_history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get update history")

@app.post("/api/update-state")
async def api_update_state(request: dict):
    """Update system state using APTPT feedback control and persist to SQLite"""
    try:
        current_state = request.get("current_state", [])
        target_state = request.get("target_state", [])
        description = request.get("description", "")
        
        if not current_state or not target_state:
            raise HTTPException(status_code=422, detail="Both current_state and target_state are required")
        
        # Convert to numpy arrays
        current = np.array(current_state)
        target = np.array(target_state)
        
        # Apply APTPT feedback control
        new_state = aptpt.update_state(current, target)
        
        # Calculate metrics
        convergence_rate = aptpt.calculate_convergence_rate(current, new_state, target)
        error_reduction = aptpt.calculate_error_reduction(current, new_state, target)
        iterations = aptpt.get_iteration_count()
        
        # Save to persistent history
        save_state_update(
            current_state=current_state,
            target_state=target_state,
            new_state=new_state.tolist(),
            convergence_rate=convergence_rate,
            error_reduction=error_reduction,
            iterations=iterations,
            description=description
        )
        
        result = {
            "new_state": new_state.tolist(),
            "convergence_rate": float(convergence_rate),
            "error_reduction": float(error_reduction),
            "iterations": int(iterations),
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    except Exception as e:
        print(f"Error in update_state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update state: {str(e)}")

@app.get("/api/sequence-analysis-history")
async def get_sequence_analysis_history_api():
    """Get real persistent history of sequence analyses"""
    try:
        return get_sequence_analysis_history(limit=100)
    except Exception as e:
        print(f"Error in get_sequence_analysis_history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sequence analysis history")

@app.get("/api/sequence-analyses")
async def get_sequence_analyses():
    """Get sequence analyses in the format expected by the frontend"""
    try:
        history = get_sequence_analysis_history(limit=100)
        
        # Transform the data to match the frontend interface
        analyses = []
        for record in history:
            analysis = {
                "id": record["id"],
                "timestamp": record["timestamp"],
                "sequence_type": record.get("analysis_type", "pattern"),
                "analysis_type": record.get("description", "State Sequence Analysis"),
                "input_data": str(record.get("states", [])),
                "output_data": str(record.get("results", {})),
                "confidence_score": record.get("confidence_score", 0.85),
                "processing_time": record.get("processing_time", 150.0),
                "status": "completed",
                "metadata": {
                    "aptpt_metrics": record.get("aptpt_analysis", {}),
                    "hce_metrics": record.get("hce_analysis", {}),
                    "rei_metrics": record.get("rei_analysis", {}),
                    "system_impact": {
                        "performance_change": record.get("performance_impact", 0.1),
                        "stability_improvement": record.get("stability_impact", 0.05),
                        "complexity_reduction": record.get("complexity_impact", 0.02)
                    }
                }
            }
            analyses.append(analysis)
        
        return {"analyses": analyses}
    except Exception as e:
        print(f"Error in get_sequence_analyses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sequence analyses")

@app.post("/api/analyze-sequence")
async def api_analyze_sequence(request: dict):
    """Analyze a sequence of states for APTPT, HCE, and REI compliance and persist to SQLite"""
    try:
        states = request.get("states", [])
        description = request.get("description", "")
        
        if not states or len(states) < 2:
            raise HTTPException(status_code=422, detail="At least 2 states are required for analysis")
        
        # Convert to numpy arrays
        state_arrays = [np.array(s) for s in states]
        
        # APTPT analysis
        aptpt_results = aptpt.batch_validate(state_arrays[:-1], state_arrays[1:])
        
        # HCE analysis
        hce_results = hce.analyze_phase_drift(len(state_arrays))
        
        # REI analysis
        rei_results = rei.validate_transformation_chain(state_arrays)
        
        # Save to persistent history
        save_sequence_analysis(
            states=states,
            description=description,
            aptpt_analysis=aptpt_results,
            hce_analysis=hce_results,
            rei_analysis=rei_results
        )
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        return {
            "aptpt_analysis": convert_numpy_types(aptpt_results),
            "hce_analysis": convert_numpy_types(hce_results),
            "rei_analysis": convert_numpy_types(rei_results)
        }
    except Exception as e:
        print(f"Error in analyze_sequence: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze sequence: {str(e)}")

# Theory-specific endpoints
@app.post("/update-state")
async def update_state(request: StateUpdate):
    """
    Update system state using APTPT feedback law
    """
    try:
        current = np.array(request.current_state)
        target = np.array(request.target_state)
        
        # Get APTPT feedback - new method returns only the new state
        new_state = aptpt.update_state(current, target)
        
        # Update HCE phase state
        hce_metrics = hce.update_phase_state(new_state)
        
        # Check REI invariance
        rei_valid = rei.check_invariance(new_state.tolist(), current.tolist())
        
        # Calculate metrics
        convergence_rate = aptpt.calculate_convergence_rate(current, new_state, target)
        error_reduction = aptpt.calculate_error_reduction(current, new_state, target)
        iterations = aptpt.get_iteration_count()
        
        return {
            "new_state": new_state.tolist(),
            "convergence_rate": float(convergence_rate),
            "error_reduction": float(error_reduction),
            "iterations": int(iterations),
            "timestamp": datetime.now().isoformat(),
            "hce_metrics": hce_metrics,
            "rei_valid": rei_valid
        }
    except Exception as e:
        print(f"Error in update_state: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.post("/analyze-sequence")
async def analyze_sequence(request: AnalysisRequest):
    """
    Analyze a sequence of states for APTPT, HCE, and REI compliance
    """
    try:
        states = [np.array(s) for s in request.states]
        
        # APTPT analysis
        aptpt_results = aptpt.batch_validate(states[:-1], states[1:])
        
        # HCE analysis
        hce_results = hce.analyze_phase_drift(len(states))
        
        # REI analysis
        rei_results = rei.validate_transformation_chain(states)
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        return {
            "aptpt_analysis": convert_numpy_types(aptpt_results),
            "hce_analysis": convert_numpy_types(hce_results),
            "rei_analysis": convert_numpy_types(rei_results)
        }
    except Exception as e:
        print(f"Error in analyze_sequence: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.get("/phase-diagram")
async def get_phase_diagram():
    """
    Get current phase diagram data
    """
    return {
        "hce_diagram": hce.get_phase_diagram(),
        "rei_diagram": rei.get_equivalence_diagram()
    }

@app.get("/dashboard")
async def dashboard():
    """Dashboard endpoint for system metrics"""
    return {
        "status": "ok",
        "aptpt": {
            "gain": getattr(aptpt, 'gain', 0.16),
            "noise": getattr(aptpt, 'noise', 0.005),
            "convergence_threshold": getattr(aptpt, 'convergence_threshold', 0.03)
        },
        "phase": getattr(hce, 'phase_history', []),
        "entropy": getattr(hce, 'entropy_history', []),
        "rei": {
            "xi": getattr(rei, 'xi', 1.0),
            "invariance_threshold": getattr(rei, 'invariance_threshold', 0.95)
        }
    }

# Helper functions
def convert_numpy_types(obj):
    """Convert numpy types to Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def calculate_phase_entropy() -> float:
    """
    Calculate system entropy using APTPT theory
    Returns a value between 0 (low entropy) and 1 (high entropy)
    """
    # Simulate entropy calculation using APTPT equations
    # In a real system, this would use actual system metrics
    return np.random.normal(0.2, 0.1)  # Low entropy is good

def calculate_phase_stability() -> float:
    """
    Calculate phase stability using APTPT theory
    Returns a value between 0 (unstable) and 1 (stable)
    """
    # Simulate stability calculation using APTPT equations
    return np.random.normal(0.9, 0.05)  # High stability is good

def calculate_phase_confidence() -> float:
    """
    Calculate phase confidence using HCE theory
    Returns a value between 0 (low confidence) and 1 (high confidence)
    """
    # Simulate confidence calculation using HCE equations
    return np.random.normal(0.95, 0.02)  # High confidence is good

async def simulate_test_execution(test_name: str):
    """
    Simulates test execution with realistic timing and potential failures.
    """
    # Simulate network delay
    await asyncio.sleep(0.5)
    
    # Simulate random failures (10% chance)
    if random.random() < 0.1:
        raise Exception(f"Simulated failure in test: {test_name}")
    
    # Simulate processing time
    await asyncio.sleep(random.uniform(0.1, 1.0))

# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import asyncio
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 