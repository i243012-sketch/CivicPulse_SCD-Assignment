"""Base triage provider protocol/interface."""
from typing import Protocol

from app.schemas.triage import TriageResult


class TriageProvider(Protocol):
    """Protocol defining the interface for triage providers."""

    name: str

    def triage(self, text: str, location: str) -> TriageResult:
        """
        Triage a complaint and return categorization results.
        
        Args:
            text: The complaint text (untrusted user input)
            location: The complaint location (untrusted user input)
            
        Returns:
            TriageResult with category, priority, summary, and confidence
        """
        ...
