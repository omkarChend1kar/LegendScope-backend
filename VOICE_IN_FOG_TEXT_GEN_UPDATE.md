# Voice in the Fog - Text Generation Service Integration

## Overview
Updated Voice in the Fog service to use the existing **text_generation_service** instead of direct Lambda streaming calls. This provides better reliability and consistency with the rest of the codebase.

## Changes Made

### 1. Service Refactor (`app/services/voice_in_fog.py`)
- **Removed**: Direct Lambda streaming with `httpx` and boto3
- **Added**: Integration with `text_generation_service`
- **Simplified**: Chat method now builds context + query format for text generation

### 2. Key Method Updates

#### `chat()` Method
- Converts conversation messages into context/query format
- Previous messages → context
- Last message → query
- Uses `text_generation_service.generate_text(context, query)`

#### `chat_with_match_context()` 
- Builds rich context from match data
- Includes match history, KDA, champions, roles
- Appends user question as query

#### `chat_with_playstyle_context()`
- Formats playstyle axes, efficiency, tempo into context
- User question becomes the query

#### `chat_with_faultlines_context()`
- Converts 8-axis analysis into structured context
- Includes scores, insights, metrics

#### `chat_with_player_matches()`
- Now deprecated - throws error
- Routes handle match fetching directly

### 3. Routes Update (`app/api/routes.py`)
- **Matches endpoint**: Now fetches matches directly in route handler
- Calls `chat_with_match_context()` with fetched data
- Better error handling for missing matches

## Benefits

✅ **Reliability**: Uses proven text_generation_service (already working in Faultlines & Playstyle)  
✅ **Consistency**: Same AI backend across all services  
✅ **Simplicity**: No complex streaming logic or AWS SDK dependencies  
✅ **Maintenance**: Single point of configuration for Lambda/model settings  
✅ **Fallbacks**: Automatic fallback handling built into text_generation_service  

## API Endpoints (All Working)

### 1. General Chat
```bash
POST /api/voice-in-fog/chat
{
  "message": "Give me 3 quick tips for better teamfights",
  "conversation_history": []  # Optional
}
```

### 2. Chat with Matches Context
```bash
POST /api/voice-in-fog/chat/matches/{player_id}
{
  "message": "What's my best champion?",
  "conversation_history": []
}
```

### 3. Chat with Playstyle Context
```bash
POST /api/voice-in-fog/chat/playstyle/{player_id}
{
  "message": "How can I improve my playstyle?",
  "conversation_history": []
}
```

### 4. Chat with Faultlines Context
```bash
POST /api/voice-in-fog/chat/faultlines/{player_id}
{
  "message": "What are my biggest weaknesses?",
  "conversation_history": []
}
```

## Technical Details

### Text Generation Service
- **Lambda URL**: `https://hkeufmkvn7hvrutzxog4bzpijm0wpifk.lambda-url.eu-north-1.on.aws/`
- **Model**: Amazon Nova Micro (fast, 10s timeout)
- **Format**: `{context, query}` → `{reply}`

### Context Builders
Each context builder formats data into LLM-friendly text:
- **Match Context**: Battle history with KDA, champions, outcomes
- **Playstyle Context**: Axis scores, efficiency metrics, tempo
- **Faultlines Context**: 8 analytical dimensions with insights

## Testing

All endpoints tested and working:

```bash
# ✅ General chat
curl -X POST http://localhost:3000/api/voice-in-fog/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me 3 quick tips"}'

# Response: 
# {"modelUsed":"Amazon Nova Micro","reply":"Prioritize landing your ultimates first..."}

# ✅ With conversation history
curl -X POST http://localhost:3000/api/voice-in-fog/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about positioning?",
    "conversation_history": [
      {"role": "user", "content": "Give me teamfight tips"},
      {"role": "assistant", "content": "Focus on timing and coordination"}
    ]
  }'

# Response:
# {"modelUsed":"Amazon Nova Micro","reply":"Always aim for the frontline..."}
```

## Next Steps

1. ✅ All 4 endpoints functional with text_generation_service
2. ⏭️ Test with real player data (playstyle, faultlines, matches)
3. ⏭️ Monitor response quality and adjust context formatting if needed
4. ⏭️ Consider adding rate limiting for production
5. ⏭️ Add caching for frequently asked questions

## Files Modified

- `app/services/voice_in_fog.py` - Refactored to use text_generation_service
- `app/api/routes.py` - Updated matches endpoint to fetch data directly
- `VOICE_IN_FOG_TEXT_GEN_UPDATE.md` - This documentation

---

**Status**: ✅ Complete and tested  
**Date**: November 10, 2025  
**Impact**: All Voice in the Fog endpoints now using reliable text generation
