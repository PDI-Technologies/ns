"""Vendor duplicate detection using fuzzy string matching."""

from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from vendor_analysis.core.config import Settings
from vendor_analysis.db.models import VendorRecord


@dataclass
class DuplicatePair:
    """Potential duplicate vendor pair."""

    vendor_1_id: str
    vendor_1_name: str
    vendor_2_id: str
    vendor_2_name: str
    similarity_score: float


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not str1 or not str2:
        return 0.0

    # Normalize strings
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    return SequenceMatcher(None, s1, s2).ratio()


def detect_duplicate_vendors(
    session: Session,
    settings: Settings,
    threshold: float | None = None,
) -> list[DuplicatePair]:
    """
    Detect potential duplicate vendors using fuzzy matching.

    Args:
        session: Database session
        settings: Application settings
        threshold: Similarity threshold (None = use config default)

    Returns:
        List of potential duplicate pairs
    """
    if threshold is None:
        threshold = settings.duplicate_threshold

    # Get all active vendors
    vendors = session.query(VendorRecord).filter_by(is_inactive=False).all()

    duplicates: list[DuplicatePair] = []

    # Compare all pairs
    for i, vendor1 in enumerate(vendors):
        name1 = vendor1.company_name or vendor1.entity_id

        for vendor2 in vendors[i + 1 :]:
            name2 = vendor2.company_name or vendor2.entity_id

            similarity = calculate_similarity(name1, name2)

            if similarity >= threshold:
                duplicates.append(
                    DuplicatePair(
                        vendor_1_id=vendor1.id,
                        vendor_1_name=name1,
                        vendor_2_id=vendor2.id,
                        vendor_2_name=name2,
                        similarity_score=similarity,
                    )
                )

    # Sort by similarity score descending
    duplicates.sort(key=lambda x: x.similarity_score, reverse=True)

    return duplicates
