"""Factory for creating triage provider instances based on configuration."""

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage

logger = get_logger(__name__)


def get_triage_provider() -> TriageProvider:
    """
    Get the configured triage provider instance.

    Returns:
        TriageProvider implementation based on TRIAGE_PROVIDER env var

    Raises:
        ValueError: If provider name is not recognized
    """
    provider_name = settings.TRIAGE_PROVIDER.lower()

    if provider_name == "llm":
        logger.info("Initializing LLM triage provider (Groq)")
        return LLMTriage()  # type: ignore[return-value]
    elif provider_name == "rules":
        logger.info("Initializing rule-based triage provider")
        return RuleBasedTriage()  # type: ignore[return-value]
    elif provider_name == "simulated":
        logger.info("Initializing simulated triage provider")
        return SimulatedTriage()  # type: ignore[return-value]
    else:
        raise ValueError(
            f"Unknown triage provider: {provider_name}. "
            f"Valid options: llm, rules, simulated"
        )
