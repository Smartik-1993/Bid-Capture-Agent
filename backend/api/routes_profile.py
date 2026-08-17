from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from backend.database import get_db
from backend.models import UserProfileModel, UserProfileSchema, OpportunityModel
from backend.extraction.doc_parser import DocumentParser
from backend.extraction.ai_analyzer import RFPAnalysisEngine

router = APIRouter(prefix="/api/profile", tags=["Company Profile & Matching"])

class ProfileUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    poc_name: Optional[str] = None
    poc_email: Optional[str] = None
    poc_phone: Optional[str] = None
    location: Optional[str] = None
    cage_code: Optional[str] = None
    uei: Optional[str] = None
    capabilities_summary: Optional[str] = None
    target_naics: Optional[List[str]] = None
    target_keywords: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    compliance_posture: Optional[List[str]] = None
    min_fit_score: Optional[int] = None

@router.get("", response_model=UserProfileSchema)
def get_active_profile(db: Session = Depends(get_db)):
    """Retrieve currently active company profile and target matching parameters."""
    profile = db.query(UserProfileModel).filter(UserProfileModel.is_active == True).first()
    if not profile:
        profile = db.query(UserProfileModel).first()
        if profile:
            profile.is_active = True
            db.commit()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found")
    return profile

@router.get("/all", response_model=List[UserProfileSchema])
def list_all_profiles(db: Session = Depends(get_db)):
    """List all available capability profiles (e.g. A11N Holdings LLC, PIScaleX)."""
    return db.query(UserProfileModel).all()

@router.post("/switch/{profile_id}")
async def switch_active_profile(profile_id: str, db: Session = Depends(get_db)):
    """Switch active profile and re-score entire RFP pipeline."""
    target = db.query(UserProfileModel).filter(UserProfileModel.id == profile_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Set all other profiles inactive
    db.query(UserProfileModel).update({UserProfileModel.is_active: False})
    target.is_active = True
    db.commit()

    # Re-score pipeline against newly selected profile
    profile_data = {
        "company_name": target.company_name,
        "capabilities_summary": target.capabilities_summary,
        "target_naics": target.target_naics or [],
        "target_keywords": target.target_keywords or [],
        "certifications": target.certifications or [],
        "clearances": target.compliance_posture or []
    }

    opportunities = db.query(OpportunityModel).all()
    ai_engine = RFPAnalysisEngine()

    for opp in opportunities:
        opp_dict = {
            "title": opp.title,
            "agency": opp.agency,
            "solicitation_number": opp.solicitation_number,
            "naics_code": opp.naics_code,
            "due_date": opp.due_date,
            "set_aside": opp.set_aside,
            "description_raw": opp.description_raw
        }
        analysis = await ai_engine.analyze_rfp(rfp_data=opp_dict, company_profile=profile_data)
        opp.fit_score = analysis.get("fit_score", opp.fit_score)
        opp.fit_rationale = analysis.get("fit_rationale", opp.fit_rationale)

    db.commit()

    return {
        "message": f"Switched active profile to '{target.company_name}'. Pipeline re-scored.",
        "active_profile": UserProfileSchema.model_validate(target)
    }

@router.put("", response_model=UserProfileSchema)
def update_profile(
    req: ProfileUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update active company capabilities and targeting rules."""
    profile = db.query(UserProfileModel).filter(UserProfileModel.is_active == True).first()
    if not profile:
        profile = db.query(UserProfileModel).first()
        if not profile:
            profile = UserProfileModel(id="profile_custom", is_active=True)
            db.add(profile)

    if req.company_name is not None:
        profile.company_name = req.company_name
    if req.poc_name is not None:
        profile.poc_name = req.poc_name
    if req.poc_email is not None:
        profile.poc_email = req.poc_email
    if req.poc_phone is not None:
        profile.poc_phone = req.poc_phone
    if req.location is not None:
        profile.location = req.location
    if req.cage_code is not None:
        profile.cage_code = req.cage_code
    if req.uei is not None:
        profile.uei = req.uei
    if req.capabilities_summary is not None:
        profile.capabilities_summary = req.capabilities_summary
    if req.target_naics is not None:
        profile.target_naics = req.target_naics
    if req.target_keywords is not None:
        profile.target_keywords = req.target_keywords
    if req.certifications is not None:
        profile.certifications = req.certifications
    if req.min_fit_score is not None:
        profile.min_fit_score = req.min_fit_score

    db.commit()
    db.refresh(profile)
    return profile

@router.post("/upload-deck")
async def upload_capability_deck(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload and auto-extract structured company profile from a Capability Deck (PDF/TXT) or raw text."""
    extracted_text = ""
    if file:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            extracted_text = DocumentParser.extract_text_from_pdf_bytes(content)
        else:
            extracted_text = content.decode("utf-8", errors="ignore")
    elif raw_text:
        extracted_text = raw_text
    else:
        raise HTTPException(status_code=400, detail="No file or text provided")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract readable text from document")

    ai_engine = RFPAnalysisEngine()
    extracted_profile = await ai_engine.extract_capability_deck_profile(extracted_text)

    # Create or update profile
    profile_id = f"profile_{len(db.query(UserProfileModel).all()) + 1}"
    profile = UserProfileModel(
        id=profile_id,
        is_active=True,
        company_name=extracted_profile.get("company_name", "Uploaded Company Profile"),
        capabilities_summary=extracted_profile.get("capabilities_summary", ""),
        target_naics=extracted_profile.get("target_naics", []),
        target_keywords=extracted_profile.get("target_keywords", []),
        certifications=extracted_profile.get("certifications", []),
        compliance_posture=extracted_profile.get("clearances", [])
    )
    
    # Deactivate other profiles
    db.query(UserProfileModel).update({UserProfileModel.is_active: False})
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "message": f"Capability Deck parsed and Profile for '{profile.company_name}' activated!",
        "extracted_profile": extracted_profile,
        "profile_id": profile.id
    }

@router.post("/rescore-pipeline")
async def rescore_pipeline(db: Session = Depends(get_db)):
    """Re-score all opportunities in the pipeline against the currently active profile."""
    active_profile = db.query(UserProfileModel).filter(UserProfileModel.is_active == True).first()
    if not active_profile:
        active_profile = db.query(UserProfileModel).first()
    if not active_profile:
        raise HTTPException(status_code=404, detail="No active profile found")

    profile_data = {
        "company_name": active_profile.company_name,
        "capabilities_summary": active_profile.capabilities_summary,
        "target_naics": active_profile.target_naics or [],
        "target_keywords": active_profile.target_keywords or [],
        "certifications": active_profile.certifications or [],
        "clearances": active_profile.compliance_posture or []
    }

    opportunities = db.query(OpportunityModel).all()
    ai_engine = RFPAnalysisEngine()

    for opp in opportunities:
        opp_dict = {
            "title": opp.title,
            "agency": opp.agency,
            "solicitation_number": opp.solicitation_number,
            "naics_code": opp.naics_code,
            "due_date": opp.due_date,
            "set_aside": opp.set_aside,
            "description_raw": opp.description_raw
        }
        analysis = await ai_engine.analyze_rfp(rfp_data=opp_dict, company_profile=profile_data)
        opp.fit_score = analysis.get("fit_score", opp.fit_score)
        opp.fit_rationale = analysis.get("fit_rationale", opp.fit_rationale)

    db.commit()

    return {
        "message": f"Successfully re-scored {len(opportunities)} opportunities against '{active_profile.company_name}'.",
        "total_rescored": len(opportunities)
    }

