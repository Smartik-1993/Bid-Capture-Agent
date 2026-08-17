import pytest
from backend.database import SessionLocal, init_db
from backend.models import OpportunityModel, UserProfileModel

def test_database_init_and_seeding():
    init_db()
    db = SessionLocal()
    try:
        # Check profiles
        profiles = db.query(UserProfileModel).all()
        assert len(profiles) >= 2
        
        company_names = [p.company_name for p in profiles]
        assert "A11N Holdings LLC" in company_names
        assert "PIScaleX" in company_names

        # Check opportunities
        opps = db.query(OpportunityModel).all()
        assert len(opps) >= 6
        
        fed_opps = [o for o in opps if o.source_type == "FEDERAL"]
        sled_opps = [o for o in opps if o.source_type == "SLED"]
        assert len(fed_opps) >= 2
        assert len(sled_opps) >= 4
    finally:
        db.close()
