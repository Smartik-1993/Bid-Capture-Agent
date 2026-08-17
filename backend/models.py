import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Boolean, JSON, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, ConfigDict, Field

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class OpportunityModel(Base):
    __tablename__ = "opportunities"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(50), nullable=False, index=True)          # e.g., 'SAM_GOV', 'CAL_EPROCURE', 'TX_SMARTBUY'
    source_type = Column(String(20), nullable=False, index=True)     # 'FEDERAL' or 'SLED'
    solicitation_number = Column(String(100), nullable=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    agency = Column(String(300), nullable=False, index=True)
    state = Column(String(10), nullable=False, default="US", index=True) # 'US' for federal, 'TX', 'CA', etc.
    naics_code = Column(String(20), nullable=True, index=True)
    naics_title = Column(String(200), nullable=True)
    posted_date = Column(String(50), nullable=True)
    due_date = Column(String(50), nullable=True, index=True)
    set_aside = Column(String(100), nullable=True, default="None")
    estimated_value = Column(String(100), nullable=True)
    source_url = Column(String(1000), nullable=True)
    description_raw = Column(Text, nullable=True)
    
    # Workflow Status
    status = Column(String(50), default="NEW", index=True)          # 'NEW', 'REVIEWING', 'BID', 'NO_BID', 'ARCHIVED'
    
    # AI Enrichment & Match Scoring
    fit_score = Column(Integer, default=0, index=True)              # 0 - 100
    fit_rationale = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    sow_deliverables = Column(JSON, nullable=True, default=list)
    mandatory_qualifications = Column(JSON, nullable=True, default=list)
    compliance_checklist = Column(JSON, nullable=True, default=list)
    evaluation_criteria = Column(JSON, nullable=True, default=list)
    poc_contacts = Column(JSON, nullable=True, default=list)
    
    raw_data = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    attachments = relationship("AttachmentModel", back_populates="opportunity", cascade="all, delete-orphan")


class AttachmentModel(Base):
    __tablename__ = "attachments"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(String(64), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(300), nullable=False)
    url = Column(String(1000), nullable=True)
    file_type = Column(String(50), nullable=True)                  # 'PDF', 'DOCX', 'XLSX', etc.
    local_path = Column(String(1000), nullable=True)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    opportunity = relationship("OpportunityModel", back_populates="attachments")


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id = Column(String(64), primary_key=True)
    is_active = Column(Boolean, default=False)
    company_name = Column(String(200), default="Company Name")
    poc_name = Column(String(200), nullable=True)
    poc_email = Column(String(200), nullable=True)
    poc_phone = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    cage_code = Column(String(50), nullable=True)
    uei = Column(String(50), nullable=True)
    
    capabilities_summary = Column(Text, default="")
    target_naics = Column(JSON, default=list)
    target_keywords = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    compliance_posture = Column(JSON, default=list)
    past_performance = Column(JSON, default=list)
    min_fit_score = Column(Integer, default=60)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)


class CaptureRunLogModel(Base):
    __tablename__ = "capture_run_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(50), nullable=False)
    total_found = Column(Integer, default=0)
    total_new = Column(Integer, default=0)
    status = Column(String(50), default="SUCCESS")
    log_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now)


# -------------------------------------------------------------
# Pydantic Schemas for API Serialization & Validation
# -------------------------------------------------------------

class AttachmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    url: Optional[str] = None
    file_type: Optional[str] = None
    local_path: Optional[str] = None


class OpportunitySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    source_type: str
    solicitation_number: Optional[str] = None
    title: str
    agency: str
    state: str
    naics_code: Optional[str] = None
    naics_title: Optional[str] = None
    posted_date: Optional[str] = None
    due_date: Optional[str] = None
    set_aside: Optional[str] = None
    estimated_value: Optional[str] = None
    source_url: Optional[str] = None
    description_raw: Optional[str] = None
    status: str
    fit_score: int
    fit_rationale: Optional[str] = None
    ai_summary: Optional[str] = None
    sow_deliverables: Optional[List[Any]] = None
    mandatory_qualifications: Optional[List[Any]] = None
    compliance_checklist: Optional[List[Any]] = None
    evaluation_criteria: Optional[List[Any]] = None
    poc_contacts: Optional[List[Any]] = None
    attachments: Optional[List[AttachmentSchema]] = None
    created_at: datetime
    updated_at: datetime


class UserProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    company_name: str
    poc_name: Optional[str] = None
    poc_email: Optional[str] = None
    poc_phone: Optional[str] = None
    location: Optional[str] = None
    cage_code: Optional[str] = None
    uei: Optional[str] = None
    capabilities_summary: str
    target_naics: List[str]
    target_keywords: List[str]
    certifications: Optional[List[str]] = None
    compliance_posture: Optional[List[str]] = None
    past_performance: Optional[List[Any]] = None
    min_fit_score: int


class CaptureTriggerRequest(BaseModel):
    naics_codes: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    due_window_days: Optional[int] = 45
    sources: Optional[List[str]] = ["ALL"]


class AIQuestionRequest(BaseModel):
    question: str
