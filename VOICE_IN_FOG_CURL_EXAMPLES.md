# Voice in the Fog - cURL Examples

Complete cURL command reference for all Voice in the Fog APIs.

---

## 1. General Chat (With Conversation History Support)

### Simple Message (No History)
```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Give me 3 quick jungle tips"
  }'
```

### With Conversation History
```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Should I focus on farming or ganking early?",
    "conversation_history": [
      {
        "role": "user",
        "content": "Give me 3 quick jungle tips"
      },
      {
        "role": "assistant",
        "content": "1. Always track enemy jungler 2. Ward before objectives 3. Maintain healthy clear"
      }
    ]
  }'
```

### With Custom Model Settings
```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I build on Jinx?",
    "model": "claude-3-7-sonnet-20250219",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### More Examples

**Champion Build Advice:**
```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What should I build on Jinx?"}'
```

**Meta Discussion:**
```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are the best supports in the current meta?"}'
```

**Strategy Questions:**
```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{"message":"When should I prioritize Herald over Dragon?"}'
```

**Response Format:**
```json
{
  "modelUsed": "Amazon Nova Micro",
  "reply": "Your answer here..."
}
```

---

## 2. Echoes of Battle (5 Topics)

**Replace `PLAYER_ID` with actual PUUID**

Example working PUUID: `AE6W6hK5V8cX9u7QgudTQsrYaGQQafYzONYl3EieQwtcZTkatRhVRLLRqAITJMKhy04eYi0vdPYPbA`

### Topic 1: Battles Fought
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Battles%20Fought"
```

### Topic 2: Claim / Fall Ratio
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Claim%20/%20Fall%20Ratio"
```

### Topic 3: Longest Claim & Fall Streaks
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Longest%20Claim%20%26%20Fall%20Streaks"
```

### Topic 4: Clutch Battles
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Clutch%20Battles"
```

### Topic 5: Role Influence
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Role%20Influence"
```

**Response Format:**
```json
{
  "starterTopic": "Battles Fought",
  "insight": "Your personalized analysis here..."
}
```

---

## 3. Patterns Beneath Chaos (7 Topics)

### Topic 1: Aggression
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Aggression"
```

### Topic 2: Survivability
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Survivability"
```

### Topic 3: Skirmish Bias
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Skirmish%20Bias"
```

### Topic 4: Objective Impact
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Objective%20Impact"
```

### Topic 5: Vision Discipline
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Vision%20Discipline"
```

### Topic 6: Utility
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Utility"
```

### Topic 7: Tempo Profile
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Tempo%20Profile"
```

**Response Format:**
```json
{
  "starterTopic": "Aggression",
  "insight": "Your playstyle analysis here..."
}
```

---

## 4. Faultlines Analysis (7 Topics)

### Topic 1: Combat Efficiency Index
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Combat%20Efficiency%20Index"
```

### Topic 2: Objective Reliability Index
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Objective%20Reliability%20Index"
```

### Topic 3: Survival Discipline Index
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Survival%20Discipline%20Index"
```

### Topic 4: Vision & Awareness Index
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Vision%20%26%20Awareness%20Index"
```

### Topic 5: Economy Utilization Index
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Economy%20Utilization%20Index"
```

### Topic 6: Momentum Index
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Momentum%20Index"
```

### Topic 7: Composure Index
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Composure%20Index"
```

**Response Format:**
```json
{
  "starterTopic": "Combat Efficiency Index",
  "insight": "Your performance index analysis here..."
}
```

---

## Testing with Working Player ID

```bash
# Set test player ID
PLAYER_ID="AE6W6hK5V8cX9u7QgudTQsrYaGQQafYzONYl3EieQwtcZTkatRhVRLLRqAITJMKhy04eYi0vdPYPbA"

# Test Echoes of Battle
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/$PLAYER_ID?starter_topic=Battles%20Fought" \
  2>/dev/null | python3 -m json.tool

# Test Patterns Beneath Chaos
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/$PLAYER_ID?starter_topic=Aggression" \
  2>/dev/null | python3 -m json.tool

# Test Faultlines
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/$PLAYER_ID?starter_topic=Combat%20Efficiency%20Index" \
  2>/dev/null | python3 -m json.tool
```

---

## Multi-Turn Conversation Example

```bash
# First message
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What makes a good support player?"
  }' | python3 -m json.tool

# Save the response, then send follow-up
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which champions would you recommend for beginners?",
    "conversation_history": [
      {
        "role": "user",
        "content": "What makes a good support player?"
      },
      {
        "role": "assistant",
        "content": "A good support excels at vision control, peel, engage timing, and map awareness..."
      }
    ]
  }' | python3 -m json.tool
```

---

## Pretty Print JSON

Add `2>/dev/null | python3 -m json.tool` to any command:

```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Give me ADC tips"}' \
  2>/dev/null | python3 -m json.tool
```

---

## Quick Reference

| API | Method | Conversation Support | Player Data |
|-----|--------|---------------------|-------------|
| General Chat | POST | ✅ Yes | ❌ No |
| Echoes of Battle | GET | ❌ No | ✅ Yes (20 matches) |
| Patterns Beneath Chaos | GET | ❌ No | ✅ Yes (20 matches) |
| Faultlines Analysis | GET | ❌ No | ✅ Yes (20 matches) |

---

## API Summary

- **Total Endpoints**: 4
- **Total Topics**: 19 (5 + 7 + 7)
- **General Chat**: Supports multi-turn conversations
- **Starter Topics**: Single-shot analysis (no conversation)
- **All GET APIs**: Work in browser URL bar

---

## Browser Testing

Starter topic APIs can be tested directly in your browser:

```
http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Battles%20Fought
http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Aggression
http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Combat%20Efficiency%20Index
```

---

## Request Schemas

### VoiceInFogChatRequest (General Chat)
```typescript
{
  message: string,                    // Required: User's message
  conversation_history?: [            // Optional: Previous messages
    {
      role: "user" | "assistant",
      content: string
    }
  ],
  model?: string,                     // Optional: Model override
  temperature?: number,               // Optional: 0.0-1.0 (default: 0.7)
  max_tokens?: number                 // Optional: 50-2000 (default: 500)
}
```

### Response Schemas

**General Chat:**
```typescript
{
  modelUsed: string,
  reply: string
}
```

**Starter Topics:**
```typescript
{
  starterTopic: string,
  insight: string
}
```

---

**Ready to use!** 🚀
