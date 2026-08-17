from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import CaptureRunLogModel, CaptureTriggerRequest
from backend.ingestion.pipeline import BidCapturePipeline

router = APIRouter(prefix="/api/capture", tags=["Capture Engine"])

@router.post("/run")
async def trigger_capture_run(
    request: CaptureTriggerRequest,
    db: Session = Depends(get_db)
):
    """Trigger an on-demand capture run across Federal (SAM.gov) and SLED portals."""
    pipeline = BidCapturePipeline(db=db)
    
    result = await pipeline.run_capture(
        naics_codes=request.naics_codes,
        keywords=request.keywords,
        due_window_days=request.due_window_days or 45,
        sources=request.sources or ["ALL"]
    )
    
    return {
        "status": "COMPLETED",
        "message": f"Capture executed successfully. {result['new_captured']} new opportunities saved.",
        "details": result
    }


@router.get("/logs")
def get_capture_logs(
    limit: int = 15,
    db: Session = Depends(get_db)
):
    """Retrieve history of capture pipeline runs."""
    logs = db.query(CaptureRunLogModel).order_by(desc(CaptureRunLogModel.timestamp)).limit(limit).all()
    return [
        {
            "id": log.id,
            "source": log.source,
            "total_found": log.total_found,
            "total_new": log.total_new,
            "status": log.status,
            "log_message": log.log_message,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in logs
    ]
