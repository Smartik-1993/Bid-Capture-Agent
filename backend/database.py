from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings
from backend.models import Base, OpportunityModel, AttachmentModel, UserProfileModel

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and seed with capability profiles and demo opportunities."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_capability_profiles(db)
        
        # Check if opportunities exist; if empty, seed rich sample data
        count = db.query(OpportunityModel).count()
        if count == 0:
            seed_initial_opportunities(db)
    finally:
        db.close()

def seed_capability_profiles(db: Session):
    """Seed structured capability decks from A11N Holdings LLC and PIScaleX."""
    
    # 1. A11N Holdings LLC (Federal + SLED IT & AI)
    a11n = db.query(UserProfileModel).filter(UserProfileModel.id == "profile_a11n").first()
    if not a11n:
        a11n = UserProfileModel(
            id="profile_a11n",
            is_active=True,
            company_name="A11N Holdings LLC",
            poc_name="Adrian Pittman, CEO",
            poc_email="advising@a11n.com",
            poc_phone="(404) 585-0449",
            location="Atlanta, Georgia",
            cage_code="13DX8",
            uei="TZFDB2A6BJU8",
            capabilities_summary=(
                "A11N Holdings LLC is a software & IT design and development firm specializing in "
                "custom AI systems development, LLMs, process automation, data engineering, enterprise software "
                "engineering, cloud & database design, legacy upgrades, cybersecurity vulnerability assessments, "
                "and hardware & network infrastructure (fiber/cabling, AV/sound, equipment room builds) "
                "for Consumer, Financial, Healthcare, Institutional, and Government agencies. 30 years industry experience."
            ),
            target_naics=[
                "541511", "541512", "541519", "54151", "511210", 
                "513210", "518210", "541611", "541690", "541715", "541990"
            ],
            target_keywords=[
                "Custom AI & LLMs", "Process Automation", "Data Engineering", "App & API Development",
                "Cloud & Database Design", "CyberSecurity", "Legacy Upgrades", "Fiber & Cabling",
                "AV & Sound Systems", "Network Design", "Equipment Room Builds", "Penetration Testing"
            ],
            certifications=[
                "EC-Council Certified Professionals",
                "ISACA CISA Certified",
                "ISC2 Certified Professionals",
                "PMP Certified Professionals",
                "Certified ScrumMaster (CSM)",
                "GIAC Certified",
                "NMSDC Certified Small Minority Business",
                "SWAM-Certified Small Business"
            ],
            compliance_posture=[
                "Commander's Coin for Excellence (U.S. Army Corps of Engineers)",
                "Active Directory Security Audit Certified",
                "Network Vulnerability Assessment Certified"
            ],
            past_performance=[
                {"client": "U.S. Army Corps of Engineers", "project": "Tourism Kiosk Software & Commander's Coin Award"},
                {"client": "General Services Administration (GSA)", "project": "Conference Room & Wayfinding System"},
                {"client": "Federal / Financial Client", "project": "External Network Penetration Test & Vulnerability Assessment"},
                {"client": "Enterprise Client", "project": "Internal Active Directory Security Audit"},
                {"client": "Enterprise FinTech", "project": "AI Systems & Predictive Analytics Development"}
            ],
            min_fit_score=65
        )
        db.add(a11n)

    # 2. PIScaleX (SLED Government Contracting Advisory & Civic Tech)
    piscalex = db.query(UserProfileModel).filter(UserProfileModel.id == "profile_piscalex").first()
    if not piscalex:
        piscalex = UserProfileModel(
            id="profile_piscalex",
            is_active=False,
            company_name="PIScaleX",
            poc_name="Amjad / SLED Advisory Team",
            poc_email="info@piscalex.us",
            poc_phone="+1 (703) 666-7959",
            location="U.S. National / SLED",
            cage_code="SAM.GOV Registered",
            uei="Available on Request",
            capabilities_summary=(
                "PIScaleX supports technology companies, SaaS providers, and IT organizations in navigating and pursuing "
                "U.S. State, Local, and Education (SLED) government contracts. Core areas include AI & Generative Intelligence, "
                "Cloud & Platform Engineering, Civic Mobile & Web Portals, Data Analytics & Modernization, ERP & CRM Advisory, "
                "Gov Cloud Migration, EdTech, SLED Bid & Tender Intelligence, Proposal Strategy, and Compliance Mapping."
            ),
            target_naics=["541511", "541512", "518210", "611420"],
            target_keywords=[
                "AI & Generative Intelligence", "Cloud & Platform Engineering", "Civic Mobile & Web Portals",
                "Data Analytics & Modernization", "ERP & CRM Advisory", "SLED Bid & Tender Intelligence",
                "Gov Cloud Migration", "EdTech", "Compliance Mapping", "Bid Readiness Assessment"
            ],
            certifications=[
                "CMMC Level 1 Compliant",
                "NIST 800-53 Compliant",
                "WCAG 2.2 AA Accessibility Certified",
                "FERPA Compliant",
                "HIPAA Compliant",
                "U.S. Data Residency Verified",
                "AWS GovCloud & Azure Government Partner"
            ],
            compliance_posture=[
                "NIST 800-53", "WCAG 2.2 AA", "FERPA", "HIPAA", "CMMC Level 1", "AWS GovCloud", "Azure Government"
            ],
            past_performance=[
                {"client": "Maycomb Community College (Higher EDU SLED · Michigan)", "project": "RFQ Q 1971: AV equipment bid intelligence and submission engineering in 72h under NDA"},
                {"client": "Kansas City KS Public Schools (K-12 SLED · Kansas)", "project": "RFP 26-003: Districtwide data-dashboard bid intelligence across 7 data domains mapped to 125-pt evaluation"}
            ],
            min_fit_score=60
        )
        db.add(piscalex)

    db.commit()

def seed_initial_opportunities(db: Session):
    """Seed high-quality initial Federal (SAM.gov) and SLED RFPs across USA."""
    today = datetime.now(timezone.utc)
    
    sample_opps = [
        {
            "id": "opp-fed-001",
            "source": "SAM_GOV",
            "source_type": "FEDERAL",
            "solicitation_number": "FA8771-26-R-0042",
            "title": "Enterprise Cloud Migration and Zero-Trust Cybersecurity Modernization",
            "agency": "Department of the Air Force / Air Force Life Cycle Management Center (AFLCMC)",
            "state": "US",
            "naics_code": "541512",
            "naics_title": "Computer Systems Design Services",
            "posted_date": (today - timedelta(days=4)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=22)).strftime("%Y-%m-%d"),
            "set_aside": "Total Small Business",
            "estimated_value": "$12,500,000",
            "source_url": "https://sam.gov/opp/fa877126r0042/view",
            "status": "NEW",
            "fit_score": 96,
            "fit_rationale": "Exceptional alignment with A11N Holdings capabilities in Cloud Design, Cybersecurity (ISC2/CISA/EC-Council), and past defense performance with U.S. Army Corps of Engineers.",
            "ai_summary": (
                "The Department of the Air Force requires full lifecycle engineering to migrate 45+ legacy on-premises "
                "defense mission applications to AWS GovCloud / Azure Government IL5 environments. Includes Zero-Trust "
                "architecture implementation, automated CI/CD security pipelines, and continuous authorization (cATO) support."
            ),
            "sow_deliverables": [
                "Detailed Cloud Architecture & Workload Migration Plan (30 days post-award)",
                "Infrastructure-as-Code (Terraform/Ansible) repository for GovCloud IL5 deployment",
                "Zero Trust Architecture (ZTA) enforcement with Identity & Access Management (ICAM)",
                "Continuous Monitoring & NIST SP 800-53 Rev 5 compliance artifact package",
                "24/7 Tier-3 Tier-4 Cloud Engineering Support & Incident Response"
            ],
            "mandatory_qualifications": [
                "Active DoD Secret Facility Clearance or ability to obtain",
                "Lead Personnel must hold AWS Certified Solutions Architect or Azure Solutions Architect Expert",
                "Past performance: Minimum 2 completed Federal Cloud migrations in past 3 years",
                "DoD 8570.01-M IAM Level III / CISA / ISC2 certified cybersecurity leads"
            ],
            "compliance_checklist": [
                {"item": "SF-1449 Form Signed and Completed", "mandatory": True, "status": "Ready"},
                {"item": "Technical Volume (Max 35 pages)", "mandatory": True, "status": "In Progress"},
                {"item": "Cost/Price Model Excel Spreadsheet", "mandatory": True, "status": "Pending"},
                {"item": "Small Business Subcontracting Plan", "mandatory": False, "status": "N/A - Prime Small Biz"},
                {"item": "CMMC Level 2 Self-Assessment in SPRS", "mandatory": True, "status": "Verified"}
            ],
            "evaluation_criteria": [
                {"factor": "Technical Approach & Architecture", "weight": "40%"},
                {"factor": "Past Performance & Key Personnel", "weight": "30%"},
                {"factor": "Price Realism & Reasonableness", "weight": "30%"}
            ],
            "poc_contacts": [
                {"name": "Capt. James Miller", "email": "james.miller.af@mail.mil", "role": "Contracting Officer"}
            ],
            "attachments": [
                {"name": "FA877126R0042_Statement_of_Work_Final.pdf", "file_type": "PDF", "url": "https://sam.gov/attachments/sow.pdf"},
                {"name": "Section_L_M_Proposal_Instructions.pdf", "file_type": "PDF", "url": "https://sam.gov/attachments/section_lm.pdf"},
                {"name": "Pricing_Template_Matrix.xlsx", "file_type": "XLSX", "url": "https://sam.gov/attachments/pricing.xlsx"}
            ]
        },
        {
            "id": "opp-sled-tx-002",
            "source": "TX_SMARTBUY",
            "source_type": "SLED",
            "solicitation_number": "RFP-304-26-00892",
            "title": "Statewide Automated Data Analytics and AI Predictive Case Management System",
            "agency": "Texas Health and Human Services Commission (HHSC)",
            "state": "TX",
            "naics_code": "541511",
            "naics_title": "Custom Computer Programming Services",
            "posted_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=18)).strftime("%Y-%m-%d"),
            "set_aside": "HUB (Historically Underutilized Business) Preference",
            "estimated_value": "$6,800,000",
            "source_url": "https://www.txsmartbuy.com/esbd/RFP-304-26-00892",
            "status": "REVIEWING",
            "fit_score": 93,
            "fit_rationale": "High synergy with Custom AI & LLMs, Data Engineering, and Process Automation. Small Minority Business / HUB status provides strong competitive positioning.",
            "ai_summary": (
                "Texas HHSC seeks a turnkey modern data platform leveraging AI/ML predictive analytics to identify "
                "casework bottleneck anomalies, automate eligibility document processing, and integrate with existing "
                "Texas Child Welfare and Medicaid databases with HIPAA-compliant encryption."
            ),
            "sow_deliverables": [
                "Custom web portal & dashboard for 2,400+ state social workers",
                "Automated OCR and NLP document extraction pipeline for public benefit applications",
                "Secure REST API middleware connecting legacy Oracle DB with Snowflake data lake",
                "SOC 2 Type II audit report & Texas DIR Security Compliance certification"
            ],
            "mandatory_qualifications": [
                "Demonstrated experience with Texas DIR (Department of Information Resources) framework",
                "HIPAA and TX-RAMP Level 2 certified cloud infrastructure",
                "3 client references from state-level health/human service agencies"
            ],
            "compliance_checklist": [
                {"item": "HUB Subcontracting Plan (HSP) signed", "mandatory": True, "status": "Ready"},
                {"item": "Texas DIR Contract terms acknowledgment", "mandatory": True, "status": "Ready"},
                {"item": "VPAT / Accessibility Section 508 compliance statement", "mandatory": True, "status": "Pending"}
            ],
            "evaluation_criteria": [
                {"factor": "Demonstrated AI/ML Accuracy & Solution Architecture", "weight": "45%"},
                {"factor": "Implementation Schedule & Risk Management", "weight": "25%"},
                {"factor": "Cost Proposal & Hourly Rate Card", "weight": "30%"}
            ],
            "poc_contacts": [
                {"name": "Elena Rodriguez, CTCD", "email": "elena.rodriguez@hhs.texas.gov", "role": "Purchaser"}
            ],
            "attachments": [
                {"name": "TX_HHSC_RFP_304_26_00892.pdf", "file_type": "PDF", "url": "https://txsmartbuy.com/docs/rfp.pdf"},
                {"name": "Attachment_A_Requirements_Matrix.xlsx", "file_type": "XLSX", "url": "https://txsmartbuy.com/docs/matrix.xlsx"}
            ]
        },
        {
            "id": "opp-sled-ca-003",
            "source": "CAL_EPROCURE",
            "source_type": "SLED",
            "solicitation_number": "0000031849",
            "title": "Caltrans Intelligent Transportation Network & Cloud Telemetry Infrastructure",
            "agency": "California Department of Transportation (Caltrans)",
            "state": "CA",
            "naics_code": "541330",
            "naics_title": "Engineering Services",
            "posted_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=34)).strftime("%Y-%m-%d"),
            "set_aside": "DVBE / SB (Small Business)",
            "estimated_value": "$8,200,000",
            "source_url": "https://caleprocure.ca.gov/event/0000031849",
            "status": "NEW",
            "fit_score": 84,
            "fit_rationale": "Direct match for NAICS 541330, Network Design, and IoT telemetry sensor builds.",
            "ai_summary": (
                "Caltrans requires an engineering and software contractor to upgrade real-time IoT sensor data collection "
                "across District 4 & 7 highway corridors. Modernize legacy SCADA data telemetry into a resilient, "
                "geo-distributed cloud dashboard for traffic management centers."
            ),
            "sow_deliverables": [
                "Edge IoT gateway telemetry firmware configuration",
                "High-throughput event streaming architecture (Apache Kafka / AWS Kinesis)",
                "Real-time GIS map interface for traffic incident dispatchers",
                "Comprehensive operations and maintenance manual"
            ],
            "mandatory_qualifications": [
                "California Professional Engineer (PE) license on team",
                "Proven experience with Caltrans Traffic Management Systems (TMS)",
                "California DGS Small Business (SB) certification preference"
            ],
            "compliance_checklist": [
                {"item": "Caltrans Bidder Declaration Form 843", "mandatory": True, "status": "Ready"},
                {"item": "California Civil Rights Laws Certification", "mandatory": True, "status": "Ready"},
                {"item": "Contractor Certification Clauses (CCC 04/2017)", "mandatory": True, "status": "Ready"}
            ],
            "evaluation_criteria": [
                {"factor": "Technical Capability & System Scalability", "weight": "50%"},
                {"factor": "Relevant Engineering Past Performance", "weight": "30%"},
                {"factor": "Total Cost of Ownership", "weight": "20%"}
            ],
            "poc_contacts": [
                {"name": "Marcus Vance", "email": "marcus.vance@dot.ca.gov", "role": "Contract Analyst"}
            ],
            "attachments": [
                {"name": "Caltrans_Event_0000031849_RFP.pdf", "file_type": "PDF", "url": "https://caleprocure.ca.gov/rfp.pdf"}
            ]
        },
        {
            "id": "opp-fed-004",
            "source": "SAM_GOV",
            "source_type": "FEDERAL",
            "solicitation_number": "75FCMC26R0015",
            "title": "Medicare Claims Integrity AI Fraud Detection Engine & Machine Learning Pipeline",
            "agency": "Department of Health and Human Services / Centers for Medicare & Medicaid Services (CMS)",
            "state": "US",
            "naics_code": "541519",
            "naics_title": "Other Computer Related Services",
            "posted_date": (today - timedelta(days=9)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
            "set_aside": "8(a) / Small Disadvantaged Business",
            "estimated_value": "$19,800,000",
            "source_url": "https://sam.gov/opp/75fcmc26r0015/view",
            "status": "REVIEWING",
            "fit_score": 97,
            "fit_rationale": "Direct alignment with Custom AI & LLMs, Data Engineering, and Healthcare/Enterprise Fintech past performance.",
            "ai_summary": (
                "CMS requires an advanced AI/ML fraud, waste, and abuse (FWA) detection pipeline to analyze billions "
                "of Medicare Part A, B, and D transaction logs in real time. The system will deploy supervised and "
                "unsupervised anomaly models, graph neural networks for collusion rings, and explainable AI audit trails."
            ),
            "sow_deliverables": [
                "Distributed ML Model Training Pipeline on CMS AWS Cloud Environment (CCIC)",
                "Graph Database (Neo4j / Amazon Neptune) modeling billing provider networks",
                "Explainable AI (XAI) risk scoring service with sub-second API response",
                "FedRAMP High security compliance documentation and ATO package"
            ],
            "mandatory_qualifications": [
                "Small Disadvantaged Business / Minority status",
                "Experience processing large-scale claims (1B+ records/year)",
                "Key Personnel with Ph.D./M.S. in Machine Learning or Data Science"
            ],
            "compliance_checklist": [
                {"item": "Volume I - Technical and Management", "mandatory": True, "status": "In Progress"},
                {"item": "Volume II - Past Performance (3 projects)", "mandatory": True, "status": "Ready"},
                {"item": "Volume III - Pricing Proposal Model", "mandatory": True, "status": "In Progress"},
                {"item": "Organizational Conflict of Interest (OCI) Mitigation Plan", "mandatory": True, "status": "Ready"}
            ],
            "evaluation_criteria": [
                {"factor": "Technical Excellence & AI Model Design", "weight": "40%"},
                {"factor": "Management Plan & Key Personnel", "weight": "25%"},
                {"factor": "Past Performance", "weight": "15%"},
                {"factor": "Evaluated Cost", "weight": "20%"}
            ],
            "poc_contacts": [
                {"name": "Sarah Jenkins", "email": "sarah.jenkins@cms.hhs.gov", "role": "Contract Specialist"}
            ],
            "attachments": [
                {"name": "CMS_FWA_Solictation_75FCMC26R0015.pdf", "file_type": "PDF", "url": "https://sam.gov/cms.pdf"},
                {"name": "Attachment_3_Data_Dictionary.xlsx", "file_type": "XLSX", "url": "https://sam.gov/dict.xlsx"}
            ]
        },
        {
            "id": "opp-sled-ny-005",
            "source": "NYS_CR",
            "source_type": "SLED",
            "solicitation_number": "NYS-ITS-2026-04",
            "title": "Statewide Identity & Access Management (IAM) Modernization and SSO Portal",
            "agency": "New York State Office of Information Technology Services (ITS)",
            "state": "NY",
            "naics_code": "541512",
            "naics_title": "Computer Systems Design Services",
            "posted_date": (today - timedelta(days=12)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=28)).strftime("%Y-%m-%d"),
            "set_aside": "NYS MWBE Goal: 30%",
            "estimated_value": "$5,400,000",
            "source_url": "https://www.nyscr.ny.gov/agency/oppView.cfm?num=NYS-ITS-2026-04",
            "status": "NEW",
            "fit_score": 91,
            "fit_rationale": "High fit for cybersecurity audits (Active Directory security audit credentials) and enterprise app & API development.",
            "ai_summary": (
                "New York State ITS is seeking proposals to consolidate 18 disparate citizen and employee authentication "
                "systems into a unified, accessible Identity Provider (Okta / Ping Identity / Microsoft Entra ID) "
                "supporting Multi-Factor Authentication (MFA), FIDO2 passkeys, and WCAG 2.1 AA accessibility."
            ),
            "sow_deliverables": [
                "Statewide Enterprise IAM architecture design & tenant provisioning",
                "Integration with 60+ NYS agency web applications & legacy mainframes",
                "Self-service citizen password recovery & identity verification workflow",
                "24/7 Security Operations Center (SOC) integration and SIEM audit logging"
            ],
            "mandatory_qualifications": [
                "Authorized partner for enterprise IAM platform (Okta / Microsoft / Ping)",
                "Minimum 5 years deploying IAM solutions exceeding 500,000 user accounts",
                "Compliance with NYS Cyber Security Policy (NYS-P03-002)"
            ],
            "compliance_checklist": [
                {"item": "NYS Vendor Responsibility Questionnaire (CCA-2)", "mandatory": True, "status": "Ready"},
                {"item": "MWBE Utilization Plan & EEO Policy Statement", "mandatory": True, "status": "In Progress"},
                {"item": "NYS Non-Collusive Bidding Certification", "mandatory": True, "status": "Ready"}
            ],
            "evaluation_criteria": [
                {"factor": "Technical & Architectural Approach", "weight": "40%"},
                {"factor": "Vendor Qualifications & Reference Sites", "weight": "30%"},
                {"factor": "Cost Proposal", "weight": "30%"}
            ],
            "poc_contacts": [
                {"name": "Arthur Chen", "email": "its.bids@its.ny.gov", "role": "Procurement Director"}
            ],
            "attachments": [
                {"name": "NYS_ITS_IAM_RFP_Final.pdf", "file_type": "PDF", "url": "https://nyscr.ny.gov/iam_rfp.pdf"}
            ]
        },
        {
            "id": "opp-sled-fl-006",
            "source": "FL_VIP",
            "source_type": "SLED",
            "solicitation_number": "RFP-FL-DOT-26-881",
            "title": "Emergency Response Logistics & Facilities Asset Management Software",
            "agency": "Florida Department of Transportation (FDOT) & Division of Emergency Management",
            "state": "FL",
            "naics_code": "561210",
            "naics_title": "Facilities Support Services",
            "posted_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "due_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
            "set_aside": "None",
            "estimated_value": "$4,200,000",
            "source_url": "https://vendor.myfloridamarketplace.com/rfp/RFP-FL-DOT-26-881",
            "status": "NEW",
            "fit_score": 76,
            "fit_rationale": "Matches software tracking and field telemetry capabilities.",
            "ai_summary": (
                "FDOT seeks a rapid deployment asset tracking and facilities logistics platform to manage heavy equipment, "
                "debris cleanup contractors, and fuel reserves during hurricane and extreme weather emergencies across Florida's 67 counties."
            ),
            "sow_deliverables": [
                "Mobile field asset inspection and GPS telemetry app (iOS / Android offline capable)",
                "Emergency Operations Center real-time resource allocation dashboard",
                "Automated FEMA reimbursement audit trail and reporting module"
            ],
            "mandatory_qualifications": [
                "Demonstrated FEMA public assistance reporting compliance experience",
                "99.99% uptime SLA with cellular fallback in disaster zones"
            ],
            "compliance_checklist": [
                {"item": "MyFloridaMarketPlace (MFMP) Registration", "mandatory": True, "status": "Ready"},
                {"item": "Florida Public Records Exemption Certification", "mandatory": True, "status": "Ready"},
                {"item": "Drug-Free Workplace Program Certification", "mandatory": True, "status": "Ready"}
            ],
            "evaluation_criteria": [
                {"factor": "Field Usability & Offline Resilience", "weight": "40%"},
                {"factor": "FEMA Audit Readiness & Compliance", "weight": "35%"},
                {"factor": "Implementation Cost & Licensing", "weight": "25%"}
            ],
            "poc_contacts": [
                {"name": "Danielle Cooper", "email": "danielle.cooper@dot.state.fl.us", "role": "Contracts Officer"}
            ],
            "attachments": [
                {"name": "FDOT_Emergency_Asset_RFP.pdf", "file_type": "PDF", "url": "https://fdot.gov/rfp.pdf"}
            ]
        }
    ]

    for opp_data in sample_opps:
        attachments_data = opp_data.pop("attachments", [])
        opp = OpportunityModel(**opp_data)
        db.add(opp)
        db.flush()
        
        for att in attachments_data:
            attachment = AttachmentModel(
                opportunity_id=opp.id,
                name=att.get("name"),
                file_type=att.get("file_type"),
                url=att.get("url")
            )
            db.add(attachment)
            
    db.commit()
