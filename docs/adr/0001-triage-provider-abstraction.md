# ADR-0001: Triage Provider Abstraction via Factory Pattern

## Status
Accepted

## Context

Complaints need to be automatically triaged (categorized and prioritized). We have multiple triage strategies:
1. **LLM-based**: Uses Groq API with Mixtral model for intelligent classification
2. **Rules-based**: Simple keyword matching (fallback when LLM unavailable)
3. **Simulated**: Returns random values for testing

The system needs to:
- Switch between providers without code changes
- Support testing without external API dependencies
- Allow future provider additions (e.g., different LLM vendors)

## Decision

We use the **Factory Pattern** to abstract triage provider creation:

1. **Base Interface**: `TriageProviderBase` defines contract (`triage()` method)
   - **File**: `backend/app/providers/triage/base.py`, lines 10-25

2. **Factory**: `get_triage_provider()` returns correct implementation based on env var
   - **File**: `backend/app/providers/triage/factory.py`, lines 15-30
   - **Reads**: `TRIAGE_PROVIDER` environment variable

3. **Implementations**:
   - `LLMTriageProvider`: Calls Groq API
   - `RulesTriageProvider`: Keyword matching
   - `SimulatedTriageProvider`: Random responses

## Consequences

### Positive
✅ Easy to swap providers via environment variable
✅ Testable without external dependencies
✅ Future-proof for new providers
✅ Each provider is independently testable

### Negative
❌ Abstraction overhead for simple feature
❌ All providers must conform to same interface

## References
- **Factory**: `backend/app/providers/triage/factory.py`, lines 15-30
- **Base class**: `backend/app/providers/triage/base.py`, lines 10-25
- **LLM provider**: `backend/app/providers/triage/llm.py`
- **Rules provider**: `backend/app/providers/triage/rules.py`
- **Simulated provider**: `backend/app/providers/triage/simulated.py`
- **Usage**: `backend/app/services/complaint_service.py`, line 35
