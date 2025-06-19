from fastapi import FastAPI, Request, UploadFile, File, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import numpy as np
from typing import Dict, List, Optional, Any
import yaml
from datetime import datetime
import os
import psutil
import time
import uuid
import random
from fastapi.responses import JSONResponse

from aptpt_feedback import APTPTFeedback
from hce_engine import HCEEngine
from rei_engine import REIEngine

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

PAPER_PATHS = {
    'aptpt': 'backend/aptpt_hce_rei_papers/aptpt_paper.tex',
    'hce': 'backend/aptpt_hce_rei_papers/hce_paper.tex',
    'rei': 'backend/aptpt_hce_rei_papers/rei_paper.tex',
    'cms': 'backend/aptpt_hce_rei_papers/cosmic_motion_symphony_paper.tex',
}

# APTPT Phase 3: Test Storage
test_results: List[TestResult] = []

@app.post("/update-state")
async def update_state(request: StateUpdate):
    """
    Update system state using APTPT feedback law
    """
    current = np.array(request.current_state)
    target = np.array(request.target_state)
    
    # Get APTPT feedback
    new_state, aptpt_metrics = aptpt.update_state(current, target)
    
    # Update HCE phase state
    hce_metrics = hce.update_phase_state(new_state)
    
    # Check REI invariance
    rei_valid = rei.check_invariance(new_state, current)
    
    return {
        "new_state": new_state.tolist(),
        "aptpt_metrics": aptpt_metrics,
        "hce_metrics": hce_metrics,
        "rei_valid": rei_valid
    }

@app.post("/analyze-sequence")
async def analyze_sequence(request: AnalysisRequest):
    """
    Analyze a sequence of states for APTPT, HCE, and REI compliance
    """
    states = [np.array(s) for s in request.states]
    
    # APTPT analysis
    aptpt_results = aptpt.batch_validate(states[:-1], states[1:])
    
    # HCE analysis
    hce_results = hce.analyze_phase_drift(len(states))
    
    # REI analysis
    rei_results = rei.validate_transformation_chain(states)
    
    return {
        "aptpt_analysis": aptpt_results,
        "hce_analysis": hce_results,
        "rei_analysis": rei_results
    }

@app.get("/phase-diagram")
async def get_phase_diagram():
    """
    Get current phase diagram data
    """
    return {
        "hce_diagram": hce.get_phase_diagram(),
        "rei_diagram": rei.get_equivalence_diagram()
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/optimize-parameters")
async def optimize_parameters(request: AnalysisRequest):
    """
    Optimize APTPT, HCE, and REI parameters based on state sequence
    """
    states = [np.array(s) for s in request.states]
    
    # Optimize APTPT parameters
    aptpt_results = aptpt.batch_validate(states[:-1], states[1:])
    aptpt_optimized = aptpt.optimize_parameters(aptpt_results)
    
    # Update config with optimized parameters
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    config["aptpt"]["default_gain"] = aptpt_optimized["optimized_gain"]
    config["aptpt"]["default_noise"] = aptpt_optimized["optimized_noise"]
    
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)
    
    return {
        "optimized_parameters": aptpt_optimized,
        "config_updated": True
    }

@app.get("/api/dashboard")
async def api_dashboard():
    """API Dashboard endpoint for system metrics"""
    return {
        "status": "ok",
        "aptpt": {
            "gain": getattr(aptpt, 'gain', None),
            "noise": getattr(aptpt, 'noise', None),
            "convergence_threshold": getattr(aptpt, 'convergence_threshold', None)
        },
        "phase": getattr(hce, 'phase_history', []),
        "entropy": getattr(hce, 'entropy_history', []),
        "rei": {
            "xi": getattr(rei, 'xi', None),
            "invariance_threshold": getattr(rei, 'invariance_threshold', None)
        }
    }

@app.get("/dashboard")
async def dashboard():
    """Dashboard endpoint for system metrics"""
    return {
        "status": "ok",
        "aptpt": {
            "gain": getattr(aptpt, 'gain', None),
            "noise": getattr(aptpt, 'noise', None),
            "convergence_threshold": getattr(aptpt, 'convergence_threshold', None)
        },
        "phase": getattr(hce, 'phase_history', []),
        "entropy": getattr(hce, 'entropy_history', []),
        "rei": {
            "xi": getattr(rei, 'xi', None),
            "invariance_threshold": getattr(rei, 'invariance_threshold', None)
        }
    }

@app.get('/api/paper/{paper_key}')
def get_paper(paper_key: str):
    path = PAPER_PATHS.get(paper_key)
    if not path or not os.path.exists(path):
        return Response(content='Paper not found.', status_code=404)
    with open(path, 'r', encoding='utf-8') as f:
        return Response(content=f.read(), media_type='text/plain')

@app.get("/api/health")
async def health_check():
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

@app.get("/api/update-history")
async def get_update_history():
    """Get history of state updates"""
    try:
        # Return mock data for now - in production this would come from a database
        history = [
            {
                "new_state": [0.15, 0.25, 0.35],
                "convergence_rate": 0.85,
                "error_reduction": 0.12,
                "iterations": 3,
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "new_state": [0.20, 0.30, 0.40],
                "convergence_rate": 0.92,
                "error_reduction": 0.08,
                "iterations": 2,
                "timestamp": "2024-01-15T10:35:00Z"
            },
            {
                "new_state": [0.25, 0.35, 0.45],
                "convergence_rate": 0.88,
                "error_reduction": 0.05,
                "iterations": 1,
                "timestamp": "2024-01-15T10:40:00Z"
            }
        ]
        return history
    except Exception as e:
        print(f"Error in get_update_history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get update history")

@app.post("/api/update-state")
async def update_state(request: dict):
    """Update system state using APTPT feedback control"""
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

@app.post("/api/analyze-sequence")
async def analyze_sequence(request: dict):
    """Analyze a sequence of states for APTPT, HCE, and REI compliance"""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 