import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AI Bid Capture Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'bid_capture.db'}"
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SAM_GOV_API_KEY: str = os.getenv("SAM_GOV_API_KEY", "")
    
    # Default Target NAICS Codes
    DEFAULT_NAICS_CODES: List[str] = [
        "541512",  # Computer Systems Design Services
        "541511",  # Custom Computer Programming Services
        "541519",  # Other Computer Related Services
        "541330",  # Engineering Services
        "541611",  # Administrative Management and General Management Consulting
        "541690",  # Other Scientific and Technical Consulting Services
        "561210",  # Facilities Support Services
    ]
    
    # Default Search Keywords
    DEFAULT_KEYWORDS: List[str] = [
        "Custom AI & LLMs",
        "Cloud Migration",
        "Cybersecurity",
        "Data Engineering",
        "Process Automation",
        "Software Development",
        "Data Analytics",
        "IT Modernization",
        "Network Infrastructure",
    ]
    
    # Target Lookahead Days (Due Date Window)
    DEFAULT_DUE_WINDOW_DAYS: int = 45

settings = Settings()
