import io
import re
import logging
from typing import Optional
import pypdf

logger = logging.getLogger(__name__)

class DocumentParser:
    """Extracts and sanitizes text and sections from RFP solicitation documents (PDF, DOCX, TXT)."""

    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes, max_pages: int = 40) -> str:
        """Extract text from in-memory PDF bytes up to max_pages."""
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            extracted_pages = []
            num_pages = min(len(reader.pages), max_pages)
            for i in range(num_pages):
                page_text = reader.pages[i].extract_text() or ""
                extracted_pages.append(f"--- PAGE {i+1} ---\n{page_text}")
            return "\n\n".join(extracted_pages)
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return ""

    @staticmethod
    def extract_key_sections(full_text: str) -> dict:
        """Heuristic section finder for SOW, Instructions, and Evaluation."""
        sections = {
            "sow": "",
            "instructions": "",
            "evaluation": "",
            "summary_snippet": full_text[:2000] if full_text else ""
        }

        # Look for SOW / PWS section
        sow_match = re.search(r"(STATEMENT OF WORK|PERFORMANCE WORK STATEMENT|SCOPE OF SERVICES|SCOPE OF WORK)([\s\S]{300,5000})", full_text, re.IGNORECASE)
        if sow_match:
            sections["sow"] = sow_match.group(2).strip()

        # Look for Proposal Instructions / Section L
        instr_match = re.search(r"(INSTRUCTIONS TO OFFERORS|PROPOSAL SUBMISSION REQUIREMENTS|SECTION L)([\s\S]{200,4000})", full_text, re.IGNORECASE)
        if instr_match:
            sections["instructions"] = instr_match.group(2).strip()

        # Look for Evaluation / Section M
        eval_match = re.search(r"(EVALUATION FACTORS FOR AWARD|BASIS FOR AWARD|SECTION M)([\s\S]{200,4000})", full_text, re.IGNORECASE)
        if eval_match:
            sections["evaluation"] = eval_match.group(2).strip()

        return sections
