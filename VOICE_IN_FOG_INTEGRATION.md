# Voice in the Fog - Streaming Chat Integration

## Overview

Voice in the Fog is a contextual AI chat service that provides real-time, streaming conversations about League of Legends gameplay analysis. It leverages AWS Lambda + Amazon Bedrock for high-quality, context-aware responses.

## Architecture

### Lambda Function
- **URL**: `https://miwqngotad6dp2g7whxpre6vmm0hesyo.lambda-url.eu-north-1.on.aws/`
- **Runtime**: Python + AWS Bedrock (Converse Stream API)
- **Models Available**:
  - Claude 3.7 Sonnet (default) - Best for chat
  - Claude 3.5 Sonnet
  - Claude 3.5 Haiku
  - Amazon Nova Pro
  - Amazon Nova Micro
  - DeepSeek-R1
  - Meta Llama 3.1 70B Instruct

### Backend Service
- **File**: `app/services/voice_in_fog.py`
- **Class**: `VoiceInFogService`
- **Singleton**: `voice_in_fog_service`

## API Endpoints

### 1. General Chat (No Context)
```
POST /api/voice-in-fog/chat
```

**Request Body**:
```json
{
  "message": "What's the current meta?",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ],
  "model": "Claude 3.7 Sonnet",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response**:
```json
{
  "modelUsed": "Claude 3.7 Sonnet",
  "reply": "The current meta focuses on..."
}
```

### 2. Chat with Match Context
```
POST /api/voice-in-fog/chat/matches/{player_id}
```

Automatically fetches and includes player's recent matches as context.

**Request Body**:
```json
{
  "message": "What's my best champion?",
  "conversation_history": []
}
```

**Response**:
```json
{
  "modelUsed": "Claude 3.7 Sonnet",
  "reply": "Based on your recent 20 matches, your best champion is Ahri with a 65% win rate and 4.2 KDA..."
}
```

### 3. Chat with Playstyle Context
```
POST /api/voice-in-fog/chat/playstyle/{player_id}
```

Includes player's full playstyle analysis (axes, efficiency, tempo, consistency).

**Request Body**:
```json
{
  "message": "How can I improve my aggression?",
  "conversation_history": []
}
```

**Response**:
```json
{
  "modelUsed": "Claude 3.7 Sonnet",
  "reply": "Your Aggression axis scores 72/100. To improve further, focus on..."
}
```

### 4. Chat with Faultlines Context
```
POST /api/voice-in-fog/chat/faultlines/{player_id}
```

Includes player's Faultlines analysis (8 axes of strengths/weaknesses).

**Request Body**:
```json
{
  "message": "Why is my survival discipline low?",
  "conversation_history": []
}
```

**Response**:
```json
{
  "modelUsed": "Claude 3.7 Sonnet",
  "reply": "Your Survival Discipline Index is 57/100 because your average deaths per game is 6.2..."
}
```

## Service Methods

### Core Methods

#### `async chat(messages, context_prompt, model, temperature, max_tokens)`
- Low-level chat method
- Sends messages to Lambda streaming endpoint
- Returns complete response

#### `async chat_with_player_matches(user_message, player_id, conversation_history, model)`
- Fetches player matches automatically
- Builds match context
- Returns contextual response

#### `async chat_with_playstyle_context(user_message, playstyle_data, conversation_history, model)`
- Uses playstyle analysis as context
- Includes axes, efficiency metrics, tempo, consistency

#### `async chat_with_faultlines_context(user_message, faultlines_data, conversation_history, model)`
- Uses Faultlines analysis as context
- Includes all 8 analytical axes with scores and insights

### Context Builders

#### `_build_match_context(matches, player_stats)`
- Formats match data into AI-readable context
- Includes overall stats and recent match summaries
- Limits to 10 most recent matches for token efficiency

#### `_build_playstyle_context(playstyle_data)`
- Formats playstyle analysis into context
- Includes role, style label, axes scores, efficiency metrics

#### `_build_faultlines_context(faultlines_data)`
- Formats Faultlines axes into context
- Includes scores, insights, and key metrics for each axis

## Usage Examples

### Frontend Integration

```typescript
// General chat
const response = await fetch('http://localhost:3000/api/voice-in-fog/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "What should I build on Ahri?",
    conversation_history: []
  })
});

// Chat with match context
const matchResponse = await fetch(`http://localhost:3000/api/voice-in-fog/chat/matches/${puuid}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Am I playing too aggressively?",
    conversation_history: previousMessages
  })
});

// Chat with playstyle context
const playstyleResponse = await fetch(`http://localhost:3000/api/voice-in-fog/chat/playstyle/${puuid}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "What's my signature strength?",
    conversation_history: []
  })
});
```

### Backend Usage

```python
from app.services.voice_in_fog import voice_in_fog_service

# Direct chat
result = await voice_in_fog_service.chat(
    messages=[{"role": "user", "content": "Tell me about jungle pathing"}],
    model="Claude 3.7 Sonnet"
)

# With match context
result = await voice_in_fog_service.chat_with_player_matches(
    user_message="What's my win rate on Ahri?",
    player_id="player-puuid-here"
)

# With playstyle context
result = await voice_in_fog_service.chat_with_playstyle_context(
    user_message="Am I an aggressive player?",
    playstyle_data=playstyle_analysis
)
```

## Context Prompts

Voice in the Fog uses rich context prompts that include:

### Match Context
```
You are 'Voice in the Fog', an expert League of Legends analyst...

## Overall Statistics:
- Average KDA: 3.2
- Win Rate: 55%
- Games Played: 100

## Recent Matches (10 games):
1. Ahri (MID) - Win - 8/2/12
2. Yasuo (MID) - Loss - 3/7/5
...
```

### Playstyle Context
```
You are 'Voice in the Fog'...

## Profile:
- Role: MID
- Style: Aggressive Striker
- Summary: High kill participation with strong early rotations
- Record: 12W - 8L

## Playstyle Axes:
- Aggression: 85/100
- Survivability: 62/100
...
```

### Faultlines Context
```
You are 'Voice in the Fog'...

## Analytical Axes:

### Combat Efficiency Index (Score: 90/100)
ID: combat_efficiency_index
Insight: Improve jungle pathing and secure more solo kills...
Metrics:
  - KDA Ratio: 4.5
  - Kill Participation: 68%
...
```

## Configuration

### Timeout Settings
- Default timeout: 60 seconds (for streaming responses)
- Can be adjusted in `VoiceInFogService.__init__()`

### Model Selection
- Default: Claude 3.7 Sonnet (best for chat)
- Can be overridden per request
- All 7 Bedrock models supported

### Token Limits
- Default: 500 tokens
- Range: 50-2000 tokens
- Configurable per request

## Error Handling

The service includes comprehensive error handling:

1. **Timeout Exceptions**: Falls back to error message
2. **HTTP Errors**: Logs and raises detailed exceptions
3. **Empty Responses**: Raises exception if Lambda returns empty reply
4. **Missing Data**: Returns 404 if no matches/analysis found

## Performance Considerations

1. **Context Size**: Match context limited to 10 recent games
2. **Streaming**: Lambda uses streaming for real-time responses
3. **Caching**: Consider caching match/analysis data for repeated queries
4. **Rate Limiting**: Implement rate limiting on frontend for production

## Future Enhancements

1. **True Streaming**: Implement SSE or WebSocket for real-time streaming to frontend
2. **Conversation Memory**: Store conversation history in database
3. **Multi-turn Context**: Maintain context across multiple messages
4. **Voice Input/Output**: Add speech-to-text and text-to-speech
5. **Personalization**: Learn user preferences over time
6. **Recommendations**: Proactive suggestions based on gameplay patterns

## Testing

```bash
# Test general chat
curl -X POST http://localhost:3000/api/voice-in-fog/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current meta?",
    "conversation_history": []
  }'

# Test with match context
curl -X POST http://localhost:3000/api/voice-in-fog/chat/matches/{puuid} \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my best champion?",
    "conversation_history": []
  }'
```

## Security

- CORS enabled for all origins (adjust for production)
- No authentication required (add in production)
- Rate limiting recommended for production use
- Input validation on all request parameters

## Monitoring

Recommended metrics to track:
- Request count by endpoint
- Average response time
- Error rate by type
- Model usage distribution
- Token consumption
- Context size distribution

---

**Status**: ✅ Fully Integrated and Ready for Testing
**Version**: 1.0.0
**Last Updated**: November 10, 2025
