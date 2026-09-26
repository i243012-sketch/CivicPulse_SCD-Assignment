"""Rule-based triage provider (deterministic, no network, never fails)."""
import re

from app.models.complaint import Category, Priority
from app.schemas.triage import TriageResult


class RuleBasedTriage:
    """Deterministic keyword-based classifier."""

    name = "rules"

    # Keywords for category classification (lowercase)
    CATEGORY_KEYWORDS = {
        Category.WATER: [
            "water",
            "leak",
            "pipe",
            "burst",
            "flood",
            "drainage",
            "sewer",
            "tap",
            "supply",
        ],
        Category.ELECTRICITY: [
            "electricity",
            "power",
            "electric",
            "outage",
            "blackout",
            "voltage",
            "transformer",
            "wire",
            "cable",
        ],
        Category.SANITATION: [
            "garbage",
            "trash",
            "waste",
            "sanitation",
            "dump",
            "litter",
            "cleanup",
            "hygiene",
        ],
        Category.ROADS: [
            "road",
            "pothole",
            "street",
            "pavement",
            "highway",
            "asphalt",
            "traffic",
            "crossing",
        ],
        Category.STREETLIGHTS: [
            "streetlight",
            "street light",
            "lamp",
            "lighting",
            "dark",
            "illumination",
            "bulb",
        ],
    }

    # Priority keywords (lowercase)
    HIGH_PRIORITY_KEYWORDS = [
        "urgent",
        "emergency",
        "danger",
        "hazard",
        "critical",
        "immediate",
        "risk",
        "unsafe",
        "severe",
    ]

    def triage(self, text: str, location: str) -> TriageResult:
        """
        Classify complaint using keyword matching.
        
        Args:
            text: Complaint text
            location: Complaint location
            
        Returns:
            TriageResult with deterministic classification
        """
        combined = f"{text} {location}".lower()

        # Determine category
        category = self._classify_category(combined)

        # Determine priority
        priority = self._classify_priority(combined)

        # Generate summary (first 140 chars of text, cleaned)
        summary = self._generate_summary(text)

        # Rules engine always has high confidence
        return TriageResult(
            category=category,
            priority=priority,
            summary=summary,
            confidence=0.95,
        )

    def _classify_category(self, text: str) -> Category:
        """Classify category based on keyword matching."""
        scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score

        # Return category with highest score, or OTHER if no matches
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return Category.OTHER

    def _classify_priority(self, text: str) -> Priority:
        """Classify priority based on keyword matching."""
        # Check for high priority keywords
        for keyword in self.HIGH_PRIORITY_KEYWORDS:
            if keyword in text:
                return Priority.HIGH

        # Check for explicit "low" mentions
        if re.search(r"\b(low|minor|small)\b", text):
            return Priority.LOW

        # Default to normal
        return Priority.NORMAL

    def _generate_summary(self, text: str) -> str:
        """Generate a summary from the complaint text."""
        # Clean and truncate
        cleaned = " ".join(text.split())  # Normalize whitespace
        if len(cleaned) <= 140:
            return cleaned
        return cleaned[:137] + "..."
