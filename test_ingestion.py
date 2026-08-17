import asyncio
from datetime import datetime, timedelta, timezone
from backend.ingestion.sam_gov import SAMGovConnector
from backend.ingestion.sled_scrapers import SLEDScraperAggregator
from backend.ingestion.pipeline import BidCapturePipeline
from backend.database import SessionLocal, init_db

def test_sam_gov_connector():
    connector = SAMGovConnector()
    opps = asyncio.run(connector.fetch_opportunities(naics_codes=["541512", "541511"]))
    assert len(opps) > 0
    assert opps[0]["source"] == "SAM_GOV"
    assert opps[0]["source_type"] == "FEDERAL"
    assert "solicitation_number" in opps[0]

def test_sled_scrapers():
    aggregator = SLEDScraperAggregator()
    sled_opps = asyncio.run(aggregator.fetch_sled_opportunities(sources=["ALL"]))
    assert len(sled_opps) >= 4
    
    sources = [o["source"] for o in sled_opps]
    assert "TX_SMARTBUY" in sources
    assert "CAL_EPROCURE" in sources
    assert "NYS_CR" in sources
    assert "FL_VIP" in sources

def test_pipeline_deduplication_and_filtering():
    init_db()
    db = SessionLocal()
    try:
        pipeline = BidCapturePipeline(db=db)
        raw_mock = [
            {
                "source": "SAM_GOV",
                "source_type": "FEDERAL",
                "solicitation_number": "DEDUP-TEST-100",
                "title": "Cloud System Engineering",
                "agency": "DoD",
                "naics_code": "541512",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d")
            },
            {
                "source": "SAM_GOV",
                "source_type": "FEDERAL",
                "solicitation_number": "DEDUP-TEST-100", # duplicate
                "title": "Cloud System Engineering",
                "agency": "DoD",
                "naics_code": "541512",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d")
            },
            {
                "source": "SAM_GOV",
                "source_type": "FEDERAL",
                "solicitation_number": "EXPIRED-TEST-200",
                "title": "Expired Proposal",
                "agency": "Army",
                "naics_code": "541512",
                "due_date": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d") # expired
            }
        ]

        filtered = pipeline._filter_and_deduplicate(raw_mock, target_naics=["541512"], due_window_days=45)
        assert len(filtered) == 1
        assert filtered[0]["solicitation_number"] == "DEDUP-TEST-100"
    finally:
        db.close()
