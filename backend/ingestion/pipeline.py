import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import OpportunityModel, AttachmentModel, UserProfileModel, CaptureRunLogModel
from backend.ingestion.sam_gov import SAMGovConnector
from backend.ingestion.sled_scrapers import SLEDScraperAggregator
from backend.extraction.ai_analyzer import RFPAnalysisEngine

logger = logging.getLogger(__name__)

class BidCapturePipeline:
    """End-to-end orchestrator for discovering, filtering, analyzing, and storing Federal & SLED RFPs."""

    def __init__(self, db: Session):
        self.db = db
        self.sam_connector = SAMGovConnector()
        self.sled_aggregator = SLEDScraperAggregator()
        self.ai_engine = RFPAnalysisEngine()

    async def run_capture(
        self,
        naics_codes: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        due_window_days: int = 45,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute full capture across Federal and SLED sources."""
        sources = sources or ["ALL"]
        profile = self.db.query(UserProfileModel).filter(UserProfileModel.is_active == True).first()
        if not profile:
            profile = self.db.query(UserProfileModel).first()
        profile_data = {
            "company_name": profile.company_name if profile else "GovTech Vendor",
            "capabilities_summary": profile.capabilities_summary if profile else "",
            "target_naics": naics_codes or (profile.target_naics if profile else settings.DEFAULT_NAICS_CODES),
            "target_keywords": keywords or (profile.target_keywords if profile else settings.DEFAULT_KEYWORDS),
            "certifications": profile.certifications if profile else [],
            "clearances": profile.compliance_posture if profile else [],
            "min_fit_score": profile.min_fit_score if profile else 60
        }

        target_naics = profile_data["target_naics"]
        target_keywords = profile_data["target_keywords"]

        all_raw_opps = []

        # 1. Fetch Federal (SAM.gov)
        if "ALL" in sources or "SAM_GOV" in sources:
            try:
                sam_opps = await self.sam_connector.fetch_opportunities(
                    naics_codes=target_naics,
                    keywords=target_keywords,
                    days_back=14
                )
                all_raw_opps.extend(sam_opps)
            except Exception as e:
                logger.error(f"Error fetching SAM.gov opportunities: {e}")

        # 2. Fetch SLED Portals
        if "ALL" in sources or any(s in ["TX_SMARTBUY", "CAL_EPROCURE", "NYS_CR", "FL_VIP"] for s in sources):
            try:
                sled_opps = await self.sled_aggregator.fetch_sled_opportunities(
                    sources=sources,
                    naics_codes=target_naics,
                    keywords=target_keywords,
                    days_back=14
                )
                all_raw_opps.extend(sled_opps)
            except Exception as e:
                logger.error(f"Error fetching SLED opportunities: {e}")

        # 3. Filter and Deduplicate
        filtered_opps = self._filter_and_deduplicate(all_raw_opps, target_naics, due_window_days)

        # 4. Enrich with AI Analysis & Persist
        new_count = 0
        persisted_ids = []

        for opp_dict in filtered_opps:
            sol_num = opp_dict.get("solicitation_number")
            existing = self.db.query(OpportunityModel).filter(
                OpportunityModel.solicitation_number == sol_num,
                OpportunityModel.source == opp_dict.get("source")
            ).first()

            if existing:
                continue

            # Run AI Analysis & Fit Scoring
            analysis_result = await self.ai_engine.analyze_rfp(
                rfp_data=opp_dict,
                company_profile=profile_data
            )

            # Combine fields
            opp_record = OpportunityModel(
                source=opp_dict.get("source", "UNKNOWN"),
                source_type=opp_dict.get("source_type", "FEDERAL"),
                solicitation_number=sol_num,
                title=opp_dict.get("title", "Untitled RFP"),
                agency=opp_dict.get("agency", "Government Agency"),
                state=opp_dict.get("state", "US"),
                naics_code=opp_dict.get("naics_code"),
                naics_title=opp_dict.get("naics_title"),
                posted_date=opp_dict.get("posted_date"),
                due_date=opp_dict.get("due_date"),
                set_aside=opp_dict.get("set_aside", "None"),
                estimated_value=opp_dict.get("estimated_value"),
                source_url=opp_dict.get("source_url"),
                description_raw=opp_dict.get("description_raw"),
                status="NEW",
                fit_score=analysis_result.get("fit_score", 60),
                fit_rationale=analysis_result.get("fit_rationale"),
                ai_summary=analysis_result.get("ai_summary"),
                sow_deliverables=analysis_result.get("sow_deliverables", []),
                mandatory_qualifications=analysis_result.get("mandatory_qualifications", []),
                compliance_checklist=analysis_result.get("compliance_checklist", []),
                evaluation_criteria=analysis_result.get("evaluation_criteria", []),
                raw_data=opp_dict.get("raw_data", {})
            )

            self.db.add(opp_record)
            self.db.flush()

            # Add attachments
            for att in opp_dict.get("attachments", []):
                attachment_record = AttachmentModel(
                    opportunity_id=opp_record.id,
                    name=att.get("name", "Document.pdf"),
                    url=att.get("url"),
                    file_type=att.get("file_type", "PDF")
                )
                self.db.add(attachment_record)

            persisted_ids.append(opp_record.id)
            new_count += 1

        self.db.commit()

        # Log run
        run_log = CaptureRunLogModel(
            source=",".join(sources),
            total_found=len(all_raw_opps),
            total_new=new_count,
            status="SUCCESS",
            log_message=f"Captured {len(all_raw_opps)} raw records, {new_count} new opportunities inserted."
        )
        self.db.add(run_log)
        self.db.commit()

        return {
            "total_found": len(all_raw_opps),
            "new_captured": new_count,
            "new_opportunity_ids": persisted_ids,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _filter_and_deduplicate(
        self, opps: List[Dict[str, Any]], target_naics: List[str], due_window_days: int
    ) -> List[Dict[str, Any]]:
        """Filter out bids with past due dates or non-matching NAICS, and eliminate duplicates."""
        now = datetime.now(timezone.utc)
        max_due_date = (now + timedelta(days=due_window_days)).strftime("%Y-%m-%d")
        now_str = now.strftime("%Y-%m-%d")

        unique_opps = {}
        for opp in opps:
            sol_num = opp.get("solicitation_number") or opp.get("title")
            if not sol_num:
                continue

            # NAICS match check (if naics provided on opp)
            opp_naics = opp.get("naics_code")
            if opp_naics and target_naics:
                # Check if opp_naics matches or starts with any target NAICS code
                if not any(str(opp_naics).startswith(tn[:3]) for tn in target_naics):
                    continue

            # Due Date filtering (ignore expired)
            due_date = opp.get("due_date")
            if due_date and len(due_date) >= 10:
                due_date_clean = due_date[:10]
                if due_date_clean < now_str:
                    continue # Expired bid

            if sol_num not in unique_opps:
                unique_opps[sol_num] = opp

        return list(unique_opps.values())
