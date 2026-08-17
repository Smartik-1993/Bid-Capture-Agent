import io
import csv
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.database import get_db
from backend.models import OpportunityModel, OpportunitySchema

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities"])

@router.get("", response_model=List[OpportunitySchema])
def list_opportunities(
    q: Optional[str] = Query(None, description="Keyword search in title, agency, or summary"),
    source_type: Optional[str] = Query(None, description="FEDERAL or SLED"),
    source: Optional[str] = Query(None, description="Specific portal e.g. SAM_GOV, TX_SMARTBUY"),
    naics_code: Optional[str] = Query(None, description="Filter by NAICS code"),
    state: Optional[str] = Query(None, description="Filter by state code e.g. US, TX, CA, NY"),
    status: Optional[str] = Query(None, description="Filter by status: NEW, REVIEWING, BID, NO_BID"),
    min_fit_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum fit score"),
    sort_by: str = Query("fit_score", pattern="^(fit_score|due_date|posted_date|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List and search captured Federal and SLED opportunities with advanced filters."""
    query = db.query(OpportunityModel)

    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            or_(
                OpportunityModel.title.ilike(search_pattern),
                OpportunityModel.agency.ilike(search_pattern),
                OpportunityModel.solicitation_number.ilike(search_pattern),
                OpportunityModel.ai_summary.ilike(search_pattern),
                OpportunityModel.description_raw.ilike(search_pattern)
            )
        )

    if source_type and source_type != "ALL":
        query = query.filter(OpportunityModel.source_type == source_type.upper())

    if source and source != "ALL":
        query = query.filter(OpportunityModel.source == source)

    if naics_code:
        query = query.filter(OpportunityModel.naics_code.startswith(naics_code))

    if state and state != "ALL":
        query = query.filter(OpportunityModel.state == state.upper())

    if status and status != "ALL":
        query = query.filter(OpportunityModel.status == status.upper())

    if min_fit_score is not None:
        query = query.filter(OpportunityModel.fit_score >= min_fit_score)

    # Sorting
    sort_column = getattr(OpportunityModel, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    return query.offset(offset).limit(limit).all()


@router.get("/stats")
def get_opportunity_stats(db: Session = Depends(get_db)):
    """Calculate dashboard metrics and KPIs across captured RFPs."""
    total = db.query(OpportunityModel).count()
    federal_count = db.query(OpportunityModel).filter(OpportunityModel.source_type == "FEDERAL").count()
    sled_count = db.query(OpportunityModel).filter(OpportunityModel.source_type == "SLED").count()
    
    all_scores = [opp.fit_score for opp in db.query(OpportunityModel.fit_score).all()]
    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    
    high_match_count = db.query(OpportunityModel).filter(OpportunityModel.fit_score >= 80).count()
    bid_pipeline_count = db.query(OpportunityModel).filter(OpportunityModel.status == "BID").count()

    return {
        "total_rfps": total,
        "federal_rfps": federal_count,
        "sled_rfps": sled_count,
        "avg_fit_score": avg_score,
        "high_match_rfps": high_match_count,
        "active_bids": bid_pipeline_count
    }


@router.get("/export")
def export_opportunities(
    format: str = Query("csv", pattern="^(csv|json)$"),
    source_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Export opportunities as downloadable CSV or JSON."""
    query = db.query(OpportunityModel)
    if source_type and source_type != "ALL":
        query = query.filter(OpportunityModel.source_type == source_type)
    
    records = query.all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Solicitation Number", "Title", "Agency", "Source Type", "Source Portal",
            "NAICS Code", "Due Date", "Set Aside", "Est. Value", "Fit Score", "Status", "Source URL"
        ])
        for opp in records:
            writer.writerow([
                opp.solicitation_number or "",
                opp.title,
                opp.agency,
                opp.source_type,
                opp.source,
                opp.naics_code or "",
                opp.due_date or "",
                opp.set_aside or "",
                opp.estimated_value or "",
                opp.fit_score,
                opp.status,
                opp.source_url or ""
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rfp_capture_export.csv"}
        )
    else:
        return [OpportunitySchema.model_validate(opp) for opp in records]


@router.get("/{opportunity_id}", response_model=OpportunitySchema)
def get_opportunity(opportunity_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed opportunity record with SOW, compliance matrix, and attachments."""
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.patch("/{opportunity_id}/status")
def update_opportunity_status(
    opportunity_id: str,
    status: str = Query(..., pattern="^(NEW|REVIEWING|BID|NO_BID|ARCHIVED)$"),
    db: Session = Depends(get_db)
):
    """Update pursuit decision / workflow status for an RFP."""
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp.status = status
    db.commit()
    return {"message": "Status updated successfully", "opportunity_id": opportunity_id, "new_status": status}
