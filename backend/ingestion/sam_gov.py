import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

SAM_API_BASE_URL = "https://api.sam.gov/opportunities/v2/search"

class SAMGovConnector:
    """Connector for querying and fetching opportunities from Federal SAM.gov."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SAM_GOV_API_KEY

    async def fetch_opportunities(
        self,
        naics_codes: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        days_back: int = 14,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fetch opportunities from SAM.gov API.
        If no API key is provided, generates realistic live-simulated federal RFPs.
        """
        target_naics = naics_codes or settings.DEFAULT_NAICS_CODES
        
        if not self.api_key:
            logger.info("No SAM.gov API Key configured. Generating simulated live SAM.gov opportunities.")
            return self._generate_simulated_opportunities(target_naics, keywords)

        posted_from = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%m/%d/%Y")
        posted_to = datetime.now(timezone.utc).strftime("%m/%d/%Y")

        results = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for naics in target_naics:
                params = {
                    "api_key": self.api_key,
                    "postedFrom": posted_from,
                    "postedTo": posted_to,
                    "ncode": naics,
                    "limit": limit,
                    "ptype": "o,k,p,r", # Opportunities, Solicitations, Combined Synopsis, Presolicitation
                }
                if keywords:
                    params["q"] = " ".join(keywords[:3])

                try:
                    resp = await client.get(SAM_API_BASE_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_list = data.get("opportunitiesData", [])
                        for item in raw_list:
                            results.append(self._normalize_sam_record(item))
                    else:
                        logger.warning(f"SAM.gov API returned status {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.error(f"Error querying SAM.gov for NAICS {naics}: {e}")

        return results

    def _normalize_sam_record(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert SAM.gov raw API JSON into normalized dictionary."""
        solicitation_number = item.get("solicitationNumber") or item.get("noticeId", "N/A")
        due_date = item.get("responseDeadLine") or ""
        if due_date and "T" in due_date:
            due_date = due_date.split("T")[0]

        posted_date = item.get("postedDate") or ""
        if posted_date and "T" in posted_date:
            posted_date = posted_date.split("T")[0]

        naics_info = item.get("naicsCode", "")
        if isinstance(naics_info, list) and len(naics_info) > 0:
            naics_code = str(naics_info[0])
        else:
            naics_code = str(naics_info)

        return {
            "source": "SAM_GOV",
            "source_type": "FEDERAL",
            "solicitation_number": solicitation_number,
            "title": item.get("title", "Untitled Federal RFP"),
            "agency": item.get("department", item.get("subTier", "Federal Agency")),
            "state": "US",
            "naics_code": naics_code,
            "naics_title": item.get("naicsTitle", "Federal Industry Code"),
            "posted_date": posted_date,
            "due_date": due_date,
            "set_aside": item.get("typeOfSetAsideDescription", "None"),
            "source_url": item.get("uiLink", f"https://sam.gov/opp/{item.get('noticeId')}/view"),
            "description_raw": item.get("description", ""),
            "raw_data": item,
            "attachments": [
                {
                    "name": att.get("name", "Document.pdf"),
                    "url": att.get("uri"),
                    "file_type": "PDF" if "pdf" in att.get("name", "").lower() else "DOCX"
                }
                for att in item.get("resourceLinks", [])
            ]
        }

    def _generate_simulated_opportunities(
        self, naics_codes: List[str], keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Simulate realistic live captures for federal opportunities when offline."""
        now = datetime.now(timezone.utc)
        simulated = [
            {
                "source": "SAM_GOV",
                "source_type": "FEDERAL",
                "solicitation_number": f"W911QX-26-R-{now.strftime('%M%S')}",
                "title": "US Army C5ISR Tactical Edge AI/ML Computer Vision and Object Detection System",
                "agency": "Department of the Army / Army Contracting Command (ACC-APG)",
                "state": "US",
                "naics_code": "541512",
                "naics_title": "Computer Systems Design Services",
                "posted_date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
                "due_date": (now + timedelta(days=26)).strftime("%Y-%m-%d"),
                "set_aside": "Total Small Business",
                "estimated_value": "$14,800,000",
                "source_url": "https://sam.gov/opp/w911qx26r0099/view",
                "description_raw": (
                    "ACC-APG is issuing a competitive Request for Proposal for tactical edge AI/ML compute hardware, "
                    "low-latency sensor fusion models, and integration with Next-Generation Tactical Command Networks."
                ),
                "attachments": [
                    {"name": "ACC_APG_C5ISR_Tactical_AI_SOW.pdf", "file_type": "PDF", "url": "https://sam.gov/sow.pdf"},
                    {"name": "DD_Form_254_Security_Requirements.pdf", "file_type": "PDF", "url": "https://sam.gov/dd254.pdf"}
                ]
            },
            {
                "source": "SAM_GOV",
                "source_type": "FEDERAL",
                "solicitation_number": f"70FA20-26-R-{now.strftime('%S%M')}",
                "title": "DHS FEMA National Disaster Data Mesh and Geospatial Analytics Architecture",
                "agency": "Department of Homeland Security / Federal Emergency Management Agency (FEMA)",
                "state": "US",
                "naics_code": "541511",
                "naics_title": "Custom Computer Programming Services",
                "posted_date": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
                "due_date": (now + timedelta(days=31)).strftime("%Y-%m-%d"),
                "set_aside": "Service-Disabled Veteran-Owned Small Business (SDVOSB)",
                "estimated_value": "$9,400,000",
                "source_url": "https://sam.gov/opp/70fa2026r0012/view",
                "description_raw": (
                    "DHS FEMA seeks contractor support to architect and deploy a modern enterprise Data Mesh, "
                    "integrating multi-source satellite imagery, flood gauges, and emergency incident feeds."
                ),
                "attachments": [
                    {"name": "FEMA_Disaster_Data_Mesh_PWS.pdf", "file_type": "PDF", "url": "https://sam.gov/pws.pdf"}
                ]
            }
        ]
        return simulated
