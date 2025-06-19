import os
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

DB_PATH = os.environ.get("PHASESYNTH_DB_PATH", "phasesynth.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StateUpdateHistory(Base):
    __tablename__ = "state_update_history"
    id = Column(Integer, primary_key=True, index=True)
    current_state = Column(Text, nullable=False)
    target_state = Column(Text, nullable=False)
    new_state = Column(Text, nullable=False)
    convergence_rate = Column(Float, nullable=False)
    error_reduction = Column(Float, nullable=False)
    iterations = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, default="")

class SequenceAnalysisHistory(Base):
    __tablename__ = "sequence_analysis_history"
    id = Column(Integer, primary_key=True, index=True)
    states = Column(Text, nullable=False)
    description = Column(Text, default="")
    aptpt_analysis = Column(Text, nullable=False)
    hce_analysis = Column(Text, nullable=False)
    rei_analysis = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def save_state_update(
    current_state: List[float],
    target_state: List[float],
    new_state: List[float],
    convergence_rate: float,
    error_reduction: float,
    iterations: int,
    description: str = ""
):
    db = SessionLocal()
    record = StateUpdateHistory(
        current_state=json.dumps(current_state),
        target_state=json.dumps(target_state),
        new_state=json.dumps(new_state),
        convergence_rate=convergence_rate,
        error_reduction=error_reduction,
        iterations=iterations,
        description=description
    )
    db.add(record)
    db.commit()
    db.close()

def get_state_update_history(limit: int = 100) -> List[Dict[str, Any]]:
    db = SessionLocal()
    records = db.query(StateUpdateHistory).order_by(StateUpdateHistory.timestamp.desc()).limit(limit).all()
    db.close()
    return [
        {
            "id": r.id,
            "current_state": json.loads(r.current_state),
            "target_state": json.loads(r.target_state),
            "new_state": json.loads(r.new_state),
            "convergence_rate": r.convergence_rate,
            "error_reduction": r.error_reduction,
            "iterations": r.iterations,
            "timestamp": r.timestamp.isoformat(),
            "description": r.description
        }
        for r in records
    ]

def save_sequence_analysis(
    states: List[List[float]],
    description: str,
    aptpt_analysis: Dict[str, Any],
    hce_analysis: Dict[str, Any],
    rei_analysis: Dict[str, Any]
):
    db = SessionLocal()
    record = SequenceAnalysisHistory(
        states=json.dumps(states),
        description=description,
        aptpt_analysis=json.dumps(aptpt_analysis),
        hce_analysis=json.dumps(hce_analysis),
        rei_analysis=json.dumps(rei_analysis)
    )
    db.add(record)
    db.commit()
    db.close()

def get_sequence_analysis_history(limit: int = 100) -> List[Dict[str, Any]]:
    db = SessionLocal()
    records = db.query(SequenceAnalysisHistory).order_by(SequenceAnalysisHistory.timestamp.desc()).limit(limit).all()
    db.close()
    return [
        {
            "id": r.id,
            "states": json.loads(r.states),
            "description": r.description,
            "aptpt_analysis": json.loads(r.aptpt_analysis),
            "hce_analysis": json.loads(r.hce_analysis),
            "rei_analysis": json.loads(r.rei_analysis),
            "timestamp": r.timestamp.isoformat()
        }
        for r in records
    ] 