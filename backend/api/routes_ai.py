from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import OpportunityModel, UserProfileModel, AIQuestionRequest
from backend.extraction.ai_analyzer import RFPAnalysisEngine

router = APIRouter(prefix="/api/ai", tags=["AI Engine"])

@router.post("/ask/{opportunity_id}")
async def ask_rfp_question(
    opportunity_id: str,
    request: AIQuestionRequest,
    db: Session = Depends(get_db)
):
    """Ask an interactive question about a specific RFP to the Gemini AI Agent."""
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp_dict = {
        "title": opp.title,
        "agency": opp.agency,
        "solicitation_number": opp.solicitation_number,
        "due_date": opp.due_date,
        "set_aside": opp.set_aside,
        "estimated_value": opp.estimated_value,
        "ai_summary": opp.ai_summary,
        "description_raw": opp.description_raw
    }

    ai_engine = RFPAnalysisEngine()
    answer = await ai_engine.answer_rfp_question(rfp_data=opp_dict, question=request.question)

    return {
        "opportunity_id": opportunity_id,
        "question": request.question,
        "answer": answer
    }


@router.post("/reanalyze/{opportunity_id}")
async def reanalyze_rfp(
    opportunity_id: str,
    db: Session = Depends(get_db)
):
    """Re-analyze and re-score an RFP against the current company capability profile."""
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    profile = db.query(UserProfileModel).filter(UserProfileModel.is_active == True).first()
    if not profile:
        profile = db.query(UserProfileModel).first()
    profile_data = {
        "company_name": profile.company_name if profile else "GovTech Vendor",
        "capabilities_summary": profile.capabilities_summary if profile else "",
        "target_naics": profile.target_naics if profile else [],
        "target_keywords": profile.target_keywords if profile else [],
        "certifications": profile.certifications if profile else [],
        "clearances": profile.compliance_posture if profile else []
    }

    opp_dict = {
        "title": opp.title,
        "agency": opp.agency,
        "solicitation_number": opp.solicitation_number,
        "naics_code": opp.naics_code,
        "due_date": opp.due_date,
        "set_aside": opp.set_aside,
        "description_raw": opp.description_raw
    }

    ai_engine = RFPAnalysisEngine()
    analysis = await ai_engine.analyze_rfp(rfp_data=opp_dict, company_profile=profile_data)

    opp.fit_score = analysis.get("fit_score", opp.fit_score)
    opp.fit_rationale = analysis.get("fit_rationale", opp.fit_rationale)
    opp.ai_summary = analysis.get("ai_summary", opp.ai_summary)
    opp.sow_deliverables = analysis.get("sow_deliverables", opp.sow_deliverables)
    opp.mandatory_qualifications = analysis.get("mandatory_qualifications", opp.mandatory_qualifications)
    opp.compliance_checklist = analysis.get("compliance_checklist", opp.compliance_checklist)
    opp.evaluation_criteria = analysis.get("evaluation_criteria", opp.evaluation_criteria)

    db.commit()
    db.refresh(opp)

    return {
        "message": "Opportunity re-analyzed successfully",
        "fit_score": opp.fit_score,
        "fit_rationale": opp.fit_rationale,
        "ai_summary": opp.ai_summary
    }
