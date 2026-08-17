import os
import json
import logging
from typing import Dict, Any, Optional, List
from backend.config import settings

logger = logging.getLogger(__name__)

# Check if google-genai client can be initialized
gemini_client = None
if settings.GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Could not initialize Google GenAI Client: {e}")

class RFPAnalysisEngine:
    """AI Extraction, Summarization, and Fit Scoring engine using Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = gemini_client
        if self.api_key and not self.client:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed initializing GenAI: {e}")

    async def extract_capability_deck_profile(self, deck_text: str) -> Dict[str, Any]:
        """Parse raw text from an uploaded capability deck / past performance PDF and synthesize structured profile."""
        if not self.client:
            return self._fallback_deck_extraction(deck_text)

        prompt = (
            f"You are an expert Government Contracting Proposal Strategist.\n"
            f"Analyze the following Company Capability Deck / Past Performance document text and extract a structured profile for bid capture:\n\n"
            f"DOCUMENT CONTENT:\n{deck_text[:12000]}\n\n"
            f"Extract and return ONLY a valid JSON object with the following schema:\n"
            f"{{\n"
            f'  "company_name": "Extracted or inferred company name",\n'
            f'  "capabilities_summary": "Comprehensive 3-5 sentence summary of core capabilities, technical stack, and past performance",\n'
            f'  "target_naics": ["List of 6-digit NAICS codes relevant to the company"],\n'
            f'  "target_keywords": ["List of 8-15 high-signal keywords/technologies for filtering bids"],\n'
            f'  "certifications": ["List of certifications e.g. CMMC, FedRAMP, ISO 9001, SOC 2, 8(a), HUBZone, SDVOSB"],\n'
            f'  "clearances": ["Facility Clearance Level or Personnel Clearances mentioned"]\n'
            f"}}"
        )

        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            text = response.text or "{}"
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini capability deck parsing error: {e}")
            return self._fallback_deck_extraction(deck_text)

    def _fallback_deck_extraction(self, deck_text: str) -> Dict[str, Any]:
        """Heuristic fallback when Gemini is offline."""
        lines = [l.strip() for l in deck_text.split("\n") if l.strip()]
        company_name = lines[0] if lines else "Apex GovTech Solutions"
        if len(company_name) > 60:
            company_name = "GovTech Solutions"

        return {
            "company_name": company_name,
            "capabilities_summary": (deck_text[:400] + "...").replace("\n", " ") if deck_text else "General IT & Engineering Services",
            "target_naics": ["541512", "541511", "541519", "541330", "541611"],
            "target_keywords": ["Cloud Migration", "Cybersecurity", "AI/ML", "DevOps", "Data Analytics"],
            "certifications": ["ISO 9001", "CMMC Level 2 (Self-Assessed)", "Small Business"],
            "clearances": ["Secret Facility Clearance"]
        }

    async def analyze_rfp(
        self,
        rfp_data: Dict[str, Any],
        doc_text: Optional[str] = None,
        company_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an RFP and extract:
        - Executive Summary
        - SOW & Deliverables list
        - Mandatory Qualifications
        - Compliance Checklist
        - Evaluation Criteria
        - Fit Score (0-100) & Rationale based on company capabilities.
        """
        if self.client:
            try:
                return await self._analyze_with_gemini(rfp_data, doc_text, company_profile)
            except Exception as e:
                logger.error(f"Gemini API analysis failed: {e}. Falling back to rule-based engine.")
                return self._fallback_rule_analysis(rfp_data, company_profile)
        else:
            return self._fallback_rule_analysis(rfp_data, company_profile)

    async def answer_rfp_question(
        self,
        rfp_data: Dict[str, Any],
        question: str,
        doc_text: Optional[str] = None
    ) -> str:
        """Answer a specific user query regarding an RFP using Gemini."""
        if not self.client:
            return (
                f"[AI Q&A Preview - Set GEMINI_API_KEY for live answers]\n"
                f"Regarding '{question}' on Solicitation '{rfp_data.get('solicitation_number')} - {rfp_data.get('title')}':\n"
                f"Due Date: {rfp_data.get('due_date', 'See solicitation')}. Agency: {rfp_data.get('agency')}. "
                f"Set-Aside: {rfp_data.get('set_aside', 'None')}."
            )

        prompt = (
            f"You are a senior government proposal capture manager. Answer the user question based on this RFP:\n\n"
            f"Title: {rfp_data.get('title')}\n"
            f"Agency: {rfp_data.get('agency')}\n"
            f"Solicitation: {rfp_data.get('solicitation_number')}\n"
            f"Due Date: {rfp_data.get('due_date')}\n"
            f"Set-Aside: {rfp_data.get('set_aside')}\n"
            f"Estimated Value: {rfp_data.get('estimated_value')}\n"
            f"Summary / SOW:\n{rfp_data.get('ai_summary') or rfp_data.get('description_raw')}\n\n"
            f"Additional Document Context:\n{doc_text[:6000] if doc_text else 'N/A'}\n\n"
            f"User Question: {question}\n\n"
            f"Provide a concise, direct, and actionable answer highlighting risks, deadlines, or requirements."
        )

        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text or "No response generated."
        except Exception as e:
            return f"Error querying Gemini: {e}"

    async def _analyze_with_gemini(
        self,
        rfp_data: Dict[str, Any],
        doc_text: Optional[str] = None,
        company_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform structured extraction with Gemini 2.5 Flash."""
        from google.genai import types

        profile_text = ""
        if company_profile:
            profile_text = (
                f"Company Name: {company_profile.get('company_name')}\n"
                f"Capabilities Summary: {company_profile.get('capabilities_summary')}\n"
                f"Target NAICS: {company_profile.get('target_naics')}\n"
                f"Target Keywords: {company_profile.get('target_keywords')}\n"
                f"Certifications: {company_profile.get('certifications')}\n"
                f"Clearances: {company_profile.get('clearances')}\n"
            )

        prompt = (
            f"You are an expert AI Bid Capture Agent for US Federal & SLED government contracts.\n"
            f"Extract structured key information and evaluate bid fitness.\n\n"
            f"RFP METADATA:\n"
            f"Title: {rfp_data.get('title')}\n"
            f"Agency: {rfp_data.get('agency')}\n"
            f"Solicitation Number: {rfp_data.get('solicitation_number')}\n"
            f"NAICS Code: {rfp_data.get('naics_code')}\n"
            f"Due Date: {rfp_data.get('due_date')}\n"
            f"Set Aside: {rfp_data.get('set_aside')}\n"
            f"Description/Text:\n{rfp_data.get('description_raw', '')}\n"
            f"Document Text:\n{doc_text[:8000] if doc_text else 'N/A'}\n\n"
            f"TARGET COMPANY PROFILE & CAPABILITY DECK:\n{profile_text}\n\n"
            f"Output ONLY a valid JSON object matching this schema:\n"
            f"{{\n"
            f'  "ai_summary": "2-3 sentence executive summary of the opportunity",\n'
            f'  "fit_score": integer between 0 and 100 representing alignment with company profile,\n'
            f'  "fit_rationale": "Explanation of the score, matching capabilities, and set-aside compatibility",\n'
            f'  "sow_deliverables": ["List of 3-6 key deliverable bullet points"],\n'
            f'  "mandatory_qualifications": ["List of mandatory licenses, certifications, clearances, or past performance"],\n'
            f'  "compliance_checklist": [{{"item": "Document or form required", "mandatory": true, "status": "Pending"}}],\n'
            f'  "evaluation_criteria": [{{"factor": "Factor name", "weight": "Percentage or relative importance"}}]\n'
            f"}}"
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        text = response.text or "{}"
        parsed = json.loads(text)
        return parsed

    def _fallback_rule_analysis(
        self,
        rfp_data: Dict[str, Any],
        company_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Intelligent heuristic scoring and extraction when Gemini API key is offline."""
        title = rfp_data.get("title", "").lower()
        desc = (rfp_data.get("description_raw") or "").lower()
        naics = str(rfp_data.get("naics_code") or "")
        
        target_naics = (company_profile.get("target_naics") if company_profile else None) or settings.DEFAULT_NAICS_CODES
        target_keywords = (company_profile.get("target_keywords") if company_profile else None) or settings.DEFAULT_KEYWORDS

        score = 50
        matches = []
        
        # Check NAICS match
        if naics in target_naics:
            score += 25
            matches.append(f"Target NAICS {naics}")
            
        # Check Keyword matches
        for kw in target_keywords:
            if kw.lower() in title or kw.lower() in desc:
                score += 8
                matches.append(kw)

        # Cap score
        score = min(score, 98)

        ai_summary = rfp_data.get("ai_summary") or (
            f"The {rfp_data.get('agency')} has released solicitation '{rfp_data.get('solicitation_number')}' "
            f"for {rfp_data.get('title')}. Proposals are due on {rfp_data.get('due_date', 'the specified deadline')}."
        )

        return {
            "ai_summary": ai_summary,
            "fit_score": score,
            "fit_rationale": f"Calculated based on NAICS match and key domain alignment with: {', '.join(matches[:4]) if matches else 'general procurement profile'}.",
            "sow_deliverables": rfp_data.get("sow_deliverables") or [
                "Full Technical Solution Architecture and Implementation Plan",
                "System Integration, Data Migration, and Quality Assurance Testing",
                "Deployment and Security Compliance Documentation",
                "Ongoing Operational Maintenance and Technical Support"
            ],
            "mandatory_qualifications": rfp_data.get("mandatory_qualifications") or [
                "Demonstrated past performance on projects of similar scope and magnitude",
                "Active business registration and required state/federal certifications",
                "Qualified key personnel with verified industry credentials"
            ],
            "compliance_checklist": rfp_data.get("compliance_checklist") or [
                {"item": "Signed Solicitation / Offer Form", "mandatory": True, "status": "Pending"},
                {"item": "Technical & Management Proposal Volume", "mandatory": True, "status": "Pending"},
                {"item": "Cost / Price Schedule Volume", "mandatory": True, "status": "Pending"},
                {"item": "Past Performance References", "mandatory": True, "status": "Pending"}
            ],
            "evaluation_criteria": rfp_data.get("evaluation_criteria") or [
                {"factor": "Technical Capability & Approach", "weight": "40%"},
                {"factor": "Past Performance & Key Personnel", "weight": "30%"},
                {"factor": "Price Proposal", "weight": "30%"}
            ]
        }
