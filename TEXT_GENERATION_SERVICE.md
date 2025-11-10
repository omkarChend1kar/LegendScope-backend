# Text Generation Service

## Overview
A centralized LLM-based text generation service that provides AI-powered narrative generation for all analysis services in the LegendScope backend.

## Architecture

### Service Layer
**File**: `app/services/text_generation.py`

The `TextGenerationService` class provides:
- **Asynchronous text generation** via `generate_text(context, query, max_tokens, temperature)`
- **Batch generation** via `generate_batch(requests)`
- **Fallback logic** when LLM is unavailable
- **Configurable parameters** (model, temperature, max tokens)

### API Endpoint
**Route**: `POST /api/text/generate`

**Request Schema**:
```json
{
  "context": "Background information and data for the LLM",
  "query": "The specific question or task",
  "max_tokens": 500,
  "temperature": 0.7
}
```

**Response Schema**:
```json
{
  "text": "Generated text from LLM",
  "status": "success",
  "error": null
}
```

## Integration Points

### 1. Signature Playstyle Analysis
**File**: `app/services/signature_playstyle.py`

Currently uses fallback logic for:
- **Playstyle labels**: "Frontline Anchor", "Aggressive Striker", etc.
- **One-liners**: Brief descriptions with KP and damage share
- **Insights**: 3-4 actionable recommendations
- **Tempo highlights**: Phase-specific performance summaries

### 2. Battle Summary (Future)
Can be integrated into `app/services/battle_summary.py` for:
- Risk profile narratives
- Performance summaries
- Champion-specific insights

## Usage Examples

### Direct API Call
```bash
curl -X POST http://localhost:3000/api/text/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Player: KDA 5.89, KP 50%, Damage Share 20%",
    "query": "Generate a playstyle label and one-liner",
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

### From Another Service (Future Async Integration)
```python
from app.services.text_generation import text_generation_service

# Generate playstyle label
text = await text_generation_service.generate_text(
    context="Player stats and metrics...",
    query="Generate a 2-4 word playstyle label",
    max_tokens=50,
    temperature=0.7
)
```

## Current Status

✅ **Completed**:
- Text generation service created (`text_generation.py`)
- API endpoint implemented (`POST /api/text/generate`)
- Schemas added (`TextGenerationRequest`, `TextGenerationResponse`)
- Integration structure in signature playstyle
- All linting passing
- Endpoints tested and working

⏳ **TODO**:
1. **Add LLM Provider Integration**:
   - Configure OpenAI API key in settings
   - Implement actual LLM API calls (replace fallback logic)
   - Add error handling and retries

2. **Make Services Async**:
   - Update `signature_playstyle.py` to use async/await
   - Convert text generation calls to async
   - Update route handlers to handle async service calls

3. **Enhance Prompt Engineering**:
   - Create specialized prompts for each use case
   - Add few-shot examples in prompts
   - Implement prompt templates

4. **Add Caching**:
   - Cache generated text to reduce API calls
   - Implement TTL for cache entries
   - Add cache invalidation strategy

5. **Monitoring & Logging**:
   - Track LLM API usage and costs
   - Log generation latency
   - Monitor fallback usage rate

## Testing

### Test Text Generation Endpoint
```bash
# Test with sample context
curl -s -X POST http://localhost:3000/api/text/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Player has high survivability (92) and utility (90)",
    "query": "Generate a playstyle archetype name",
    "max_tokens": 50
  }' | python3 -m json.tool
```

### Test Integrated Signature Playstyle
```bash
# Get full playstyle analysis with generated text
PUUID="AE6W6hK5V8cX9u7QgudTQsrYaGQQafYzONYl3EieQwtcZTkatRhVRLLRqAITJMKhy04eYi0vdPYPbA"
curl -s "http://localhost:3000/api/battles/${PUUID}/signature-playstyle/summary" \
  | python3 -m json.tool
```

## File Structure
```
app/
├── services/
│   ├── text_generation.py      # NEW: Text generation service
│   └── signature_playstyle.py  # UPDATED: Uses text generation
├── schemas.py                   # UPDATED: Added text gen schemas
└── api/
    └── routes.py                # UPDATED: Added text gen endpoint
```

## Benefits

1. **Centralized**: Single service for all text generation needs
2. **Reusable**: Can be called by any analysis service
3. **Flexible**: Supports various prompts and use cases
4. **Scalable**: Easy to swap LLM providers or add new features
5. **Testable**: Dedicated endpoint for testing generation quality
6. **Maintainable**: Prompt engineering in one place

## Next Steps

To fully integrate LLM capabilities:

1. Add OpenAI API key to `.env` or settings
2. Uncomment the LLM API call in `text_generation.py`
3. Update signature playstyle methods to be async
4. Test with real LLM responses
5. Fine-tune prompts for better output quality
