# Battle Summary with Status Check Implementation

## Overview
Updated the Battle Summary service to check the `last_matches` status from the player profile before fetching match data. This ensures that match data is only retrieved when it's ready (status = "READY").

## Changes Made

### 1. Schema Updates (`app/schemas.py`)

#### ProfileRequest
- Made `riot_id` **optional** (can be None)
- Added `puuid` field as **optional** (can be None)
- At least one of `riot_id` or `puuid` must be provided
- Supports querying profiles by either identifier

```python
class ProfileRequest(BaseModel):
    riot_id: str | None = Field(default=None, ...)
    puuid: str | None = Field(default=None, ...)
    region: str = Field(...)
```

#### ProfileResponse
- Added `last_matches` field to track match fetching status
- Field is optional and can be: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED

```python
class ProfileResponse(BaseModel):
    # ... existing fields ...
    last_matches: str | None = Field(
        default=None,
        alias="lastMatches",
        description="Status: NOT_STARTED, FETCHING, READY, NO_MATCHES, FAILED"
    )
```

### 2. Profile Service Updates (`app/services/profile.py`)

#### Enhanced get_profile()
- Now accepts either `riot_id` or `puuid` (or both)
- Validates that at least one identifier is provided
- Returns profile with `last_matches` status included

#### Updated _query_lambda()
- Supports querying by either `riot_id` or `puuid`
- Dynamically builds payload based on available fields

```python
payload = {}
if request.riot_id:
    payload["riotId"] = request.riot_id
if request.puuid:
    payload["puuid"] = request.puuid
payload["region"] = request.region
```

### 3. Battle Summary Service Updates (`app/services/battle_summary.py`)

#### New Method: _get_profile_status()
- Fetches player profile to check `last_matches` status
- Returns status string or None on error
- Used before fetching match data

```python
async def _get_profile_status(self, puuid: str, region: str = "na1") -> str | None:
    """Get the last_matches status from player profile."""
    from app.services.profile import profile_service
    
    request = ProfileRequest(puuid=puuid, region=region)
    profile = await profile_service.get_profile(request)
    return profile.last_matches
```

#### Updated All Summary Methods
All five battle summary methods now:
1. **Check status first** using `_get_profile_status()`
2. **Return default/empty values** if status is not "READY"
3. **Fetch and process matches** only when status is "READY"

Methods updated:
- `get_last_twenty_summary_cards()` - Returns zero values
- `get_last_twenty_role_summaries()` - Returns empty list
- `get_last_twenty_champion_summaries()` - Returns empty list
- `get_last_twenty_risk_profile()` - Returns explanatory message
- `get_last_twenty_narrative()` - Returns default message

### 4. API Route Documentation Updates (`app/api/routes.py`)

Updated endpoint documentation to explain:
- Profile endpoint now accepts `riot_id` OR `puuid`
- Battle summary endpoints check status before returning data
- What happens when status is not "READY"

## Status Flow

### Match Status Lifecycle
```
NOT_STARTED → FETCHING → READY ✓
                      ↘ NO_MATCHES
                      ↘ FAILED
```

### API Behavior Based on Status

| Status | Battle Summary Response |
|--------|------------------------|
| `NOT_STARTED` | Default/empty values with explanatory messages |
| `FETCHING` | Default/empty values (matches still being fetched) |
| `READY` | Full statistics computed from match data |
| `NO_MATCHES` | Default/empty values (player has no games) |
| `FAILED` | Default/empty values (error occurred during fetch) |

## Usage Examples

### Query Profile by Riot ID
```bash
POST /api/profile
{
    "riot_id": "cant type#1998",
    "region": "na1"
}
```

### Query Profile by PUUID
```bash
POST /api/profile
{
    "puuid": "PcymtY31rEewJXMEZRv4...",
    "region": "na1"
}
```

### Get Battle Summary (with Status Check)
```bash
GET /api/battles/{puuid}/summary/last-20/cards
```

**Response when NOT READY:**
```json
{
    "battlesFought": 0,
    "claims": 0,
    "falls": 0,
    "claimFallRatio": 0.0,
    "longestClaimStreak": 0,
    "longestFallStreak": 0,
    "clutchGames": 0,
    "surrenderRate": 0,
    "averageMatchDuration": "0m 0s"
}
```

**Response when READY:**
```json
{
    "battlesFought": 20,
    "claims": 11,
    "falls": 9,
    "claimFallRatio": 1.22,
    "longestClaimStreak": 3,
    "longestFallStreak": 2,
    "clutchGames": 4,
    "surrenderRate": 10,
    "averageMatchDuration": "28m 14s"
}
```

## Benefits

1. **No Stale Data**: Only fetches matches when they're confirmed ready
2. **Better User Experience**: Clear feedback when data isn't available yet
3. **Flexible Querying**: Support both Riot ID and PUUID lookups
4. **Error Handling**: Gracefully handles missing or failed match data
5. **Performance**: Avoids unnecessary Lambda calls when matches aren't ready

## Testing

All changes pass:
- ✅ Linting checks (ruff)
- ✅ Type checks (no errors)
- ✅ Schema validation tests

## Next Steps

- [ ] Add retry logic for FAILED status
- [ ] Implement polling mechanism for FETCHING status
- [ ] Add caching for profile status checks
- [ ] Update frontend to handle different status states
- [ ] Add metrics/monitoring for status transitions
