# Voice in the Fog - Starter Topics API

## Overview

Simple, single-purpose endpoints that analyze a player's last 20 matches and provide AI-generated insights on specific aspects of their gameplay. Each endpoint:

1. Takes a player ID and starter topic
2. Fetches the last 20 matches
3. Builds context for that specific topic
4. Generates insight using Amazon Nova Micro
5. Returns a simple response with the topic and insight

**No conversation history** - these are one-shot analysis tools.

## Flow Diagram

```
Player ID + Starter Topic
        ↓
Fetch last 20 matches (Lambda)
        ↓
Build topic-specific context
        ↓
Generate insight (Text Gen Service)
        ↓
Return {starterTopic, insight}
```

---

## API Endpoints

### 1. General Chat (No Player Context)

**Endpoint:** `POST /api/voice-in-fog/general-chat`

**Purpose:** General League of Legends gameplay advice without player-specific data.

**Request:**
```json
{
  "message": "Give me 3 quick jungle tips"
}
```

**Response:**
```json
{
  "modelUsed": "Amazon Nova Micro",
  "reply": "Always prioritize last-hitting minions..."
}
```

---

### 2. Echoes of Battle (Battle History)

**Endpoint:** `GET /api/voice-in-fog/echoes-of-battle/{player_id}?starter_topic={topic}`

**Purpose:** Insights on match history, win/loss patterns, and role performance.

**Starter Topics:**
1. **Battles Fought** - Total matches and patterns
2. **Claim / Fall Ratio** - Win/loss analysis
3. **Longest Claim & Fall Streaks** - Winning and losing streaks
4. **Clutch Battles** - Close games and comebacks
5. **Role Influence** - Performance by role

**Example Request:**
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Battles%20Fought"
```

**Example Response:**
```json
{
  "starterTopic": "Battles Fought",
  "insight": "Over your last 20 matches, you've played 12 games..."
}
```

**Metrics Analyzed:**
- Total matches, wins, losses
- Win rate, average game duration
- Most played champions and roles
- Performance by role (win rate per position)
- Streak patterns (longest win/loss streaks)
- Close game performance (games decided by < 5k gold)

---

### 3. Patterns Beneath Chaos (Playstyle Analysis)

**Endpoint:** `GET /api/voice-in-fog/patterns-beneath-chaos/{player_id}?starter_topic={topic}`

**Purpose:** Deep playstyle axis analysis across 7 dimensions.

**Starter Topics:**
1. **Aggression** - Kill participation, damage output
2. **Survivability** - Death avoidance, positioning
3. **Skirmish Bias** - Small fights vs teamfights
4. **Objective Impact** - Dragon/Baron/Tower focus
5. **Vision Discipline** - Ward placement and control
6. **Utility** - Support and team contribution
7. **Tempo Profile** - Game pacing and timing

**Example Request:**
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Aggression"
```

**Example Response:**
```json
{
  "starterTopic": "Aggression",
  "insight": "Your aggression score of 72/100 indicates a highly aggressive playstyle..."
}
```

**Metrics Analyzed Per Topic:**

**Aggression:**
- Average kills, assists, damage dealt
- Kill participation rate
- Early game aggression (0-15 min kills)

**Survivability:**
- Average deaths per game
- Death rate per minute
- Games with ≤ 3 deaths

**Skirmish Bias:**
- Kill/assist distribution
- Solo kills vs teamfight participation

**Objective Impact:**
- Dragons, Barons, Towers taken
- Objective participation rate

**Vision Discipline:**
- Vision score, wards placed/cleared
- Vision contribution to team

**Utility:**
- Assists, crowd control score
- Support actions

**Tempo Profile:**
- Game duration trends
- Early/mid/late game performance

---

### 4. Faultlines (Performance Indices)

**Endpoint:** `GET /api/voice-in-fog/faultlines-analysis/{player_id}?starter_topic={topic}`

**Purpose:** Analytical performance scoring across 7 key indices.

**Starter Topics:**
1. **Combat Efficiency Index** - KDA, damage, kills
2. **Objective Reliability Index** - Dragon/Baron control
3. **Survival Discipline Index** - Death patterns
4. **Vision & Awareness Index** - Vision score, wards
5. **Economy Utilization Index** - Gold and CS efficiency
6. **Momentum Index** - Early/mid/late game performance
7. **Composure Index** - Performance under pressure

**Example Request:**
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Combat%20Efficiency%20Index"
```

**Example Response:**
```json
{
  "starterTopic": "Combat Efficiency Index",
  "insight": "Your Combat Efficiency Index is 68/100. Your KDA of 3.2 is solid..."
}
```

**Metrics Analyzed Per Index:**

**Combat Efficiency Index:**
- KDA (Kills, Deaths, Assists)
- Total damage dealt
- Damage per minute
- Kill participation

**Objective Reliability Index:**
- Dragons secured
- Barons secured
- Towers destroyed
- Objective participation rate

**Survival Discipline Index:**
- Average deaths
- Death rate per minute
- Games with low deaths
- Positioning score

**Vision & Awareness Index:**
- Vision score
- Wards placed
- Wards cleared
- Vision per minute

**Economy Utilization Index:**
- Gold earned
- CS (Creep Score)
- Gold per minute
- CS per minute

**Momentum Index:**
- Early game performance (0-15 min)
- Mid game performance (15-25 min)
- Late game performance (25+ min)

**Composure Index:**
- Performance in close games
- Comeback potential
- Performance under pressure

---

## Response Schema

### Starter Topic Response
```typescript
{
  starterTopic: string,  // The exact topic selected
  insight: string        // AI-generated analysis
}
```

### General Chat Response
```typescript
{
  modelUsed: string,     // "Amazon Nova Micro"
  reply: string          // AI-generated response
}
```

---

## Error Responses

### Invalid Starter Topic
```json
{
  "detail": "Invalid starter topic. Must be one of: Battles Fought, Claim / Fall Ratio, ..."
}
```
**Status:** 400 Bad Request

### Player Not Found / No Matches
```json
{
  "detail": "No matches found for this player"
}
```
**Status:** 500 Internal Server Error

### Lambda/Service Error
```json
{
  "detail": "Client error '404 Not Found' for url '...'"
}
```
**Status:** 500 Internal Server Error

---

## Testing

### Test Script
Use `test_starter_topics.py` to test all endpoints:

```bash
python test_starter_topics.py
```

### Manual Testing

**General Chat:**
```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are good jungle tips?"}'
```

**Echoes of Battle:**
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/echoes-of-battle/PLAYER_ID?starter_topic=Battles%20Fought"
```

**Patterns Beneath Chaos:**
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/patterns-beneath-chaos/PLAYER_ID?starter_topic=Aggression"
```

**Faultlines:**
```bash
curl -X GET "http://localhost:3000/api/voice-in-fog/faultlines-analysis/PLAYER_ID?starter_topic=Combat%20Efficiency%20Index"
```

---

## Implementation Details

### Service Methods

**Location:** `app/services/voice_in_fog.py`

**Methods:**
- `get_echoes_of_battle_insight(player_id, starter_topic)` → {starterTopic, insight}
- `get_patterns_beneath_chaos_insight(player_id, starter_topic)` → {starterTopic, insight}
- `get_faultlines_insight(player_id, starter_topic)` → {starterTopic, insight}

### Context Builders

**Methods:**
- `_build_echoes_context(matches, starter_topic)` - Battle history metrics
- `_build_patterns_context(matches, starter_topic)` - Playstyle axis calculations
- `_build_faultlines_topic_context(matches, starter_topic)` - Performance indices

### Text Generation

All insights generated via `TextGenerationService`:
```python
insight = await text_service.generate_text(
    context=topic_specific_context,
    query=analysis_query,
)
```

**Model:** Amazon Nova Micro  
**Timeout:** 10 seconds  
**Lambda URL:** https://hkeufmkvn7hvrutzxog4bzpijm0wpifk.lambda-url.eu-north-1.on.aws/

---

## Notes

- **No Conversation History:** These APIs don't support multi-turn conversations
- **Simple Flow:** player_id + topic → matches → context → insight
- **GET vs POST:** Starter topic endpoints use GET with query params for simplicity
- **Validation:** Each endpoint validates starter topic against allowed list
- **Error Handling:** Returns appropriate HTTP status codes with error details

**Match Data**: Last 20 games per request
