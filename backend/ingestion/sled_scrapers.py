import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from backend.config import settings

logger = logging.getLogger(__name__)

class SLEDScraperAggregator:
    """Aggregator for state, local, and education procurement portals."""

    def __init__(self):
        self.sources = ["TX_SMARTBUY", "CAL_EPROCURE", "NYS_CR", "FL_VIP"]

    async def fetch_sled_opportunities(
        self,
        sources: Optional[List[str]] = None,
        naics_codes: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        days_back: int = 14
    ) -> List[Dict[str, Any]]:
        """Fetch opportunities across all enabled SLED procurement systems."""
        active_sources = sources or self.sources
        if "ALL" in active_sources:
            active_sources = self.sources

        results = []
        if "TX_SMARTBUY" in active_sources:
            results.extend(await self._fetch_texas_smartbuy(naics_codes, keywords))
        if "CAL_EPROCURE" in active_sources:
            results.extend(await self._fetch_cal_eprocure(naics_codes, keywords))
        if "NYS_CR" in active_sources:
            results.extend(await self._fetch_nys_contract_reporter(naics_codes, keywords))
        if "FL_VIP" in active_sources:
            results.extend(await self._fetch_florida_vip(naics_codes, keywords))

        return results

    async def _fetch_texas_smartbuy(
        self, naics_codes: Optional[List[str]], keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Scrape or simulate Texas SmartBuy / Electronic State Business Daily (ESBD)."""
        now = datetime.now(timezone.utc)
        return [
            {
                "source": "TX_SMARTBUY",
                "source_type": "SLED",
                "solicitation_number": f"TX-DIR-2026-{now.strftime('%M%S')}",
                "title": "Texas DIR Statewide Cloud Assessment, FinOps, and Cost Optimization Services",
                "agency": "Texas Department of Information Resources (DIR)",
                "state": "TX",
                "naics_code": "541512",
                "naics_title": "Computer Systems Design Services",
                "posted_date": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
                "due_date": (now + timedelta(days=25)).strftime("%Y-%m-%d"),
                "set_aside": "HUB Certified Vendors Encouraged",
                "estimated_value": "$7,500,000",
                "source_url": "https://www.txsmartbuy.com/esbd/TX-DIR-2026-CLOUD",
                "description_raw": (
                    "Texas DIR requests proposals from qualified vendors to deliver automated FinOps cloud cost monitoring, "
                    "governance policies, and reserved capacity management across AWS, Azure, and Google Cloud environments for 80+ Texas agencies."
                ),
                "attachments": [
                    {"name": "TX_DIR_FinOps_Solicitation_Package.pdf", "file_type": "PDF", "url": "https://txsmartbuy.com/dir.pdf"}
                ]
            }
        ]

    async def _fetch_cal_eprocure(
        self, naics_codes: Optional[List[str]], keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Scrape or simulate California Cal eProcure state bids."""
        now = datetime.now(timezone.utc)
        return [
            {
                "source": "CAL_EPROCURE",
                "source_type": "SLED",
                "solicitation_number": f"CAL-CDCR-26-{now.strftime('%S%M')}",
                "title": "Corrections Rehabilitation Telehealth & Secure Video Portal Modernization",
                "agency": "California Department of Corrections and Rehabilitation (CDCR)",
                "state": "CA",
                "naics_code": "541511",
                "naics_title": "Custom Computer Programming Services",
                "posted_date": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
                "due_date": (now + timedelta(days=21)).strftime("%Y-%m-%d"),
                "set_aside": "DVBE (Disabled Veteran Business Enterprise) 3% Goal",
                "estimated_value": "$5,200,000",
                "source_url": "https://caleprocure.ca.gov/event/CAL-CDCR-26-TELE",
                "description_raw": (
                    "CDCR requires a secure WebRTC and HIPAA-compliant video telemedicine portal for inmate mental health and vocational training consultations."
                ),
                "attachments": [
                    {"name": "CDCR_Telehealth_RFP_Specification.pdf", "file_type": "PDF", "url": "https://caleprocure.ca.gov/telehealth.pdf"}
                ]
            }
        ]

    async def _fetch_nys_contract_reporter(
        self, naics_codes: Optional[List[str]], keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Scrape or simulate New York State Contract Reporter opportunities."""
        now = datetime.now(timezone.utc)
        return [
            {
                "source": "NYS_CR",
                "source_type": "SLED",
                "solicitation_number": f"NYS-DOT-2026-{now.strftime('%M%S')}",
                "title": "New York State Bridge & Highway Infrastructure Sensor Data Lakehouse",
                "agency": "New York State Department of Transportation (NYSDOT)",
                "state": "NY",
                "naics_code": "541330",
                "naics_title": "Engineering Services",
                "posted_date": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
                "due_date": (now + timedelta(days=29)).strftime("%Y-%m-%d"),
                "set_aside": "NYS MWBE 30% / SDVOB 6%",
                "estimated_value": "$6,100,000",
                "source_url": "https://www.nyscr.ny.gov/agency/oppView.cfm?num=NYS-DOT-2026-LAKE",
                "description_raw": (
                    "NYSDOT requires engineering data lakehouse architecture to ingest real-time seismic, vibration, and strain sensor data from major suspension bridges."
                ),
                "attachments": [
                    {"name": "NYSDOT_Bridge_Lakehouse_RFP.pdf", "file_type": "PDF", "url": "https://nyscr.ny.gov/bridge.pdf"}
                ]
            }
        ]

    async def _fetch_florida_vip(
        self, naics_codes: Optional[List[str]], keywords: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Scrape or simulate Florida Vendor Information Portal (VIP) bids."""
        now = datetime.now(timezone.utc)
        return [
            {
                "source": "FL_VIP",
                "source_type": "SLED",
                "solicitation_number": f"FL-DEO-2026-{now.strftime('%S%M')}",
                "title": "Florida Workforce AI Career Pathway & Apprenticeship Matching Engine",
                "agency": "Florida Department of Commerce / FloridaCommerce",
                "state": "FL",
                "naics_code": "541512",
                "naics_title": "Computer Systems Design Services",
                "posted_date": (now - timedelta(days=6)).strftime("%Y-%m-%d"),
                "due_date": (now + timedelta(days=19)).strftime("%Y-%m-%d"),
                "set_aside": "None",
                "estimated_value": "$3,800,000",
                "source_url": "https://vendor.myfloridamarketplace.com/rfp/FL-DEO-2026-AI",
                "description_raw": (
                    "FloridaCommerce seeks an intelligent matching platform connecting job seekers, trade schools, and state defense employers."
                ),
                "attachments": [
                    {"name": "FloridaCommerce_Workforce_AI_RFP.pdf", "file_type": "PDF", "url": "https://vendor.myfloridamarketplace.com/ai.pdf"}
                ]
            }
        ]
