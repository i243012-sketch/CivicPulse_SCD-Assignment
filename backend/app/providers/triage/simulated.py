"""Simulated triage provider for CI/testing (deterministic, no network)."""
import hashlib

from app.models.complaint import Category, Priority
from app.schemas.triage import TriageResult


class SimulatedTriage:
    """Deterministic fake triage for testing - never makes network calls."""

    name = "simulated"

    def triage(self, text: str, location: str) -> TriageResult:
        """
        Generate deterministic triage results based on input hash.

        This ensures tests are never flaky due to network issues or
        non-deterministic AI responses.

        Args:
            text: Complaint text
            location: Complaint location

        Returns:
            TriageResult with deterministic classification based on hash
        """
        # Hash input for deterministic selection
        combined = f"{text}|{location}"
        hash_value = int(hashlib.sha256(combined.encode()).hexdigest(), 16)

        # Deterministically select category
        categories = list(Category)
        category = categories[hash_value % len(categories)]

        # Deterministically select priority
        priorities = list(Priority)
        priority = priorities[(hash_value // len(categories)) % len(priorities)]

        # Generate deterministic summary
        summary = self._generate_summary(text, hash_value)

        # Deterministic confidence
        confidence = 0.7 + (hash_value % 30) / 100.0  # 0.7 to 0.99

        return TriageResult(
            category=category,
            priority=priority,
            summary=summary,
            confidence=confidence,
        )

    def _generate_summary(self, text: str, hash_value: int) -> str:
        """Generate a deterministic summary."""
        # Clean and truncate
        cleaned = " ".join(text.split())

        # Use hash to determine summary length variation (100-140 chars)
        max_len = 100 + (hash_value % 41)

        if len(cleaned) <= max_len:
            return cleaned
        return cleaned[:max_len - 3] + "..."
