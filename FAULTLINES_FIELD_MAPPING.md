# Faultlines Field Mapping Analysis

## Match Data Fields Available

Total fields in match data: **90 fields**

### Core Combat Fields
- `kills` - Player kills
- `deaths` - Player deaths  
- `assists` - Player assists
- `kdaRatio` - Calculated KDA ratio
- `totalDamageDealtToChampions` - Total damage to champions
- `magicDamageDealtToChampions` - Magic damage portion
- `physicalDamageDealtToChampions` - Physical damage portion
- `trueDamageDealtToChampions` - True damage portion

### Objective Fields
- `damageDealtToObjectives` - Damage to objectives (Baron, Dragon, etc.)
- `damageDealtToTurrets` - Damage to turrets specifically
- `baronKills` - Baron kills
- `dragonKills` - Dragon kills
- `turretKills` - Turret kills
- `inhibitorKills` - Inhibitor kills
- `riftHeraldKills` - Rift Herald kills
- `objectivesStolen` - Objectives stolen (smite steals)
- `objectivesStolenAssists` - Assisted steals
- `teamBaronKills` - Team's total baron kills
- `teamDragonKills` - Team's total dragon kills
- `teamTowerKills` - Team's total turret kills

### Survival/Defense Fields
- `totalDamageTaken` - Total damage taken
- `magicDamageTaken` - Magic damage taken
- `physicalDamageTaken` - Physical damage taken
- `trueDamageTaken` - True damage taken
- `totalHeal` - Healing done
- `totalHealsOnTeammates` - Healing done to teammates
- `totalDamageShieldedOnTeammates` - Shielding done
- `timeCCingOthers` - Time spent CCing enemies

### Vision Fields
- `visionScore` - Total vision score
- `wardsPlaced` - Wards placed
- `wardsKilled` - Enemy wards killed (control wards)
- `detectorWardsPlaced` - Control wards placed
- `visionWardsBoughtInGame` - Control wards bought
- `visionPerMinute` - Vision score per minute

### Economy Fields
- `goldEarned` - Total gold earned
- `goldSpent` - Total gold spent
- `goldPerMinute` - Gold per minute
- `totalMinionsKilled` - Total CS (minions + monsters)
- `neutralMinionsKilled` - Jungle monsters killed
- `neutralMinionsKilledEnemyJungle` - Enemy jungle monsters
- `neutralMinionsKilledTeamJungle` - Own jungle monsters
- `csPerMinute` - CS per minute

### Role/Position Fields
- `teamPosition` - Role (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)
- `individualPosition` - Individual position assignment
- `lane` - Lane assignment

### Game Context Fields
- `win` - Whether player won (boolean)
- `gameDuration` - Game duration in seconds
- `gameEndTimestamp` - When game ended
- `gameCreation` - When game started
- `matchId` - Unique match identifier
- `queueId` - Queue type
- `gameMode` - Game mode
- `patchVersion` - Patch version
- `championName` - Champion played
- `championId` - Champion ID
- `championLevel` - Final champion level

### Streak/Special Fields
- `killingSprees` - Number of killing sprees
- `largestKillingSpree` - Longest killing spree
- `largestMultiKill` - Largest multikill
- `doubleKills` - Double kills
- `tripleKills` - Triple kills
- `quadraKills` - Quadra kills
- `pentaKills` - Penta kills
- `firstBloodKill` - Got first blood
- `firstTowerKill` - Got first tower
- `firstTowerAssist` - Assisted first tower
- `firstInhibitorKill` - Got first inhibitor

### Computed Indices (Already in data!)
- `aggressionIndex` - Pre-computed aggression score
- `objectiveIndex` - Pre-computed objective score
- `supportIndex` - Pre-computed support score
- `stabilityScore` - Pre-computed stability score
- `riskScore` - Pre-computed risk score
- `adaptationScore` - Pre-computed adaptation score
- `matchPerformanceIndex` - Overall match performance

## Field Mapping to Faultlines Axes

### ✅ 1. Combat Efficiency Index (CEI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| KDA Ratio | `kills`, `deaths`, `assists`, `kdaRatio` | `(kills + assists) / deaths` |
| Kill Participation | `kills`, `assists`, `teamKills` (derived) | Calculate from team total |
| Damage Per Minute | `totalDamageDealtToChampions`, `gameDuration` | `damage / (duration / 60)` |

**Additional available:**
- Damage breakdown by type
- Multikill stats
- First blood participation

### ✅ 2. Objective Reliability Index (ORI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| Baron Presence | `baronKills`, `teamBaronKills` | Baron participation rate |
| Dragon Presence | `dragonKills`, `teamDragonKills` | Dragon participation rate |
| Turret Participation | `turretKills`, `teamTowerKills` | Turret takedown rate |
| Objective Damage | `damageDealtToObjectives` | Avg per game |
| Steals | `objectivesStolen` | Smite steal count |

### ✅ 3. Survival Discipline Index (SDI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| Deaths Per Game | `deaths` | Average deaths |
| Damage Taken | `totalDamageTaken` | Effective HP metric |
| Self-Peel | `timeCCingOthers` | CC time contribution |
| Sustain | `totalHeal` | Healing done |

**Additional available:**
- Damage taken by type
- Shielding provided
- Heals on teammates

### ✅ 4. Vision & Awareness Index (VAI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| Vision Score | `visionScore` | Total vision score |
| Wards Placed | `wardsPlaced` | Wards placed per game |
| Wards Cleared | `wardsKilled` | Enemy wards killed |
| Vision Per Minute | `visionPerMinute` | Pre-computed |
| Control Wards | `detectorWardsPlaced`, `visionWardsBoughtInGame` | Control ward usage |

### ✅ 5. Economy Utilization Index (EUI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| Gold Per Minute | `goldPerMinute` | Pre-computed |
| Gold Efficiency | `goldSpent / goldEarned` | Spend ratio |
| Damage Per Gold | `totalDamageDealtToChampions / goldEarned` | Conversion rate |
| CS Per Minute | `csPerMinute` | Pre-computed |

**Additional available:**
- Jungle farm metrics
- Enemy jungle invades

### ✅ 6. Role Stability Index (RSI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| Primary Role | `teamPosition` | Most played role |
| Win Rate by Role | `win`, `teamPosition` | Win% per role |
| KDA by Role | `kdaRatio`, `teamPosition` | KDA variance |

### ✅ 7. Momentum Index (MI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| Win Streaks | `win`, `gameEndTimestamp` | Sequential wins |
| Loss Streaks | `win`, `gameEndTimestamp` | Sequential losses |
| Streak Recovery | Sequence analysis | Games to recover |

### ✅ 8. Composure Index (CI)
**All fields available!**

| Metric | Field(s) Used | Formula |
|--------|---------------|---------|
| KDA Variance | `kdaRatio` | Standard deviation |
| Gold Variance | `goldEarned` | Standard deviation |
| Death Variance | `deaths` | Standard deviation |
| Performance Consistency | Multiple metrics | Coefficient of variation |

## Comparison: Mock Data vs Actual Implementation

### Mock Frontend Structure
```typescript
{
  id: string,
  title: string,
  description: string,
  derivedFrom: string[],
  score: number,
  insight: string,
  visualization: { type, value/points/buckets },
  metrics: [{ id, label, value, formattedValue, unit, percent, trend }]
}
```

### Actual Backend Structure
```json
{
  "key": "cei",
  "label": "Combat Efficiency Index",
  "description": "Measures offensive efficiency...",
  "score": 59,
  "scoreLabel": "Moderate",
  "variant": "neutral",
  "narrative": {
    "headline": "You convert fights when allies collapse.",
    "body": "Kill participation and KDA outpace..."
  },
  "metrics": [{
    "id": "kda",
    "label": "KDA Ratio",
    "unit": "ratio",
    "value": 3.65,
    "displayValue": "3.65",
    "comparison": "+28% vs cohort",
    "direction": "positive",
    "percent": 0.73
  }],
  "trend": {
    "label": "Momentum (last 10 games)",
    "series": [{ match, delta, value, ... }]
  },
  "telemetry": {...},
  "charts": [...]
}
```

### Key Differences
1. ✅ Backend has `key` (cei, ori, etc.) - Frontend uses `id`
2. ✅ Backend has `narrative` object - Frontend has flat `insight` string
3. ✅ Backend has `scoreLabel` and `variant` - Frontend doesn't
4. ✅ Backend has `comparison` field - Frontend has `trend` (up/down/flat)
5. ✅ Backend has richer `trend` data with multiple series
6. ✅ Backend includes `telemetry` and `charts` arrays

## Why Some UUIDs Might Return Null

### Possible Reasons:
1. **Profile Status Not READY**: `lastMatches` field must be "READY"
2. **No Matches in DynamoDB**: Player profile exists but no match data stored
3. **Empty Match Array**: Lambda returns empty array
4. **Lambda Timeout**: 30s timeout might be too short for some queries
5. **Data Format Issues**: Match data structure might vary by region/patch

### How to Debug:
```bash
# 1. Check profile status
curl -X POST "http://localhost:3000/api/profile" \
  -H "Content-Type: application/json" \
  -d '{"puuid":"<PUUID>","region":"na1"}'

# 2. Check if matches exist in DynamoDB
curl -X POST "https://4x454duo26y5k7lkblp2sfvgq40xrcpn.lambda-url.eu-north-1.on.aws/" \
  -H "Content-Type: application/json" \
  -d '{"puuid":"<PUUID>"}'

# 3. If no matches, fetch them first
curl -X POST "http://localhost:3000/api/matches/last" \
  -H "Content-Type: application/json" \
  -d '{"puuid":"<PUUID>","region":"na1"}'

# 4. Then retry Faultlines
curl "http://localhost:3000/api/battles/<PUUID>/faultlines/summary"
```

## Field Coverage Summary

| Axis | Required Fields | Available | Coverage |
|------|----------------|-----------|----------|
| CEI | 6 fields | 6 | 100% ✅ |
| ORI | 5 fields | 5 | 100% ✅ |
| SDI | 5 fields | 5 | 100% ✅ |
| VAI | 4 fields | 4 | 100% ✅ |
| EUI | 4 fields | 4 | 100% ✅ |
| RSI | 3 fields | 3 | 100% ✅ |
| MI | 2 fields | 2 | 100% ✅ |
| CI | 3 fields | 3 | 100% ✅ |

**Total: 32/32 fields available (100% coverage)**

## Bonus: Pre-computed Indices Already Available!

The match data includes several pre-computed indices that could enhance analysis:
- `aggressionIndex`
- `objectiveIndex`
- `supportIndex`
- `stabilityScore`
- `riskScore`
- `adaptationScore`
- `matchPerformanceIndex`

These could be used for cross-validation or additional insights.
