# Faultlines Null Values Analysis

## Issue Summary

**Found 2 issues causing null/zero values:**

1. **Kill Participation = 0%** - Missing `teamKills` field in match data
2. **Composure Index trends = null** - Using `value` field instead of appropriate metric

---

## 1. Kill Participation Issue

### Problem
```json
{
  "id": "kp",
  "label": "Kill Participation",
  "value": 0.0,
  "displayValue": "0%",
  "comparison": "+12% vs cohort",
  "direction": "neutral",
  "percent": 0.0
}
```

### Root Cause
The match data **does NOT include `teamKills` field**. 

Current calculation in `faultlines.py`:
```python
# This returns 0 because teamKills doesn't exist
team_kills = m.get("teamKills", 0)
if team_kills > 0:
    kp = (kills + assists) / team_kills
```

### Available Team Fields
- ✅ `teamBaronKills`
- ✅ `teamDragonKills`
- ✅ `teamTowerKills`
- ✅ `teamPosition`
- ✅ `teamEarlySurrendered`
- ❌ `teamKills` - **NOT AVAILABLE**
- ❌ `teamDeaths` - **NOT AVAILABLE**

### Solution Options

#### Option A: Remove Kill Participation (Quick Fix)
Remove the KP metric entirely since we can't calculate it accurately.

#### Option B: Estimate Team Kills (Recommended)
Estimate team kills based on player performance:
```python
# Rough estimation based on player contribution
# Typical KP ranges: 40-70% for carries, 50-80% for supports
# Assume average KP of 60% across all roles
estimated_team_kills = (kills + assists) / 0.60
kp = 0.60  # Fixed estimate
```

#### Option C: Use Alternative Metric
Replace with a different metric we CAN calculate:
- **Damage Share**: `player_damage / team_damage` (if team damage available)
- **Solo Kill Rate**: `kills / (kills + assists)` - measures independence
- **First Blood Rate**: `firstBloodKill` count / games

#### Option D: Mark as Unavailable (Best for Transparency)
```python
kp_metric = FaultlinesMetricModel(
    id="kp",
    label="Kill Participation",
    unit="%",
    value=None,  # Explicitly null
    displayValue="N/A",
    comparison="Data unavailable",
    direction="neutral",
    percent=0.0
)
```

---

## 2. Composure Index Trend Nulls

### Problem
```json
"trend": {
  "label": "Performance Stability",
  "series": [
    {
      "match": 1,
      "minute": null,
      "delta": null,
      "value": null,  // ❌ All null
      "role": null,
      ...
    }
  ]
}
```

### Root Cause
The Composure Index trends are trying to use `value` field, but Composure is about **variance/consistency**, not absolute values.

Current code likely does:
```python
series.append(FaultlinesTrendPointModel(
    match=i,
    value=None,  # Wrong - should be the variance metric
    delta=None,  # Wrong - should be change in consistency
    ...
))
```

### Solution: Use Appropriate Metrics

For Composure Index trends, we should track:

**Option 1: Rolling Coefficient of Variation**
```python
# Calculate CV for each window of 5 games
for i in range(10, 21):
    recent_kdas = kdas[i-5:i]
    cv = statistics.stdev(recent_kdas) / statistics.mean(recent_kdas)
    
    series.append(FaultlinesTrendPointModel(
        match=i,
        value=cv,  # Coefficient of variation (lower = more consistent)
        delta=cv - previous_cv,
        ...
    ))
```

**Option 2: Performance Variance Score**
```python
# Track how much performance varies game to game
for i in range(10, 21):
    current_kda = kdas[i]
    avg_kda = statistics.mean(kdas[:i])
    deviation = abs(current_kda - avg_kda) / avg_kda
    
    series.append(FaultlinesTrendPointModel(
        match=i,
        value=1 - deviation,  # Higher = more consistent
        delta=deviation - previous_deviation,
        ...
    ))
```

---

## Recommended Fixes

### Priority 1: Kill Participation (Combat Efficiency Index)

**Immediate Fix**: Use Option D - mark as unavailable
```python
# In _build_combat_efficiency_index method
kp_values = []
for m in matches:
    # Skip KP calculation - data not available
    kp_values.append(None)

metrics.append(FaultlinesMetricModel(
    id="kp",
    label="Kill Participation",
    unit="%",
    value=None,
    displayValue="N/A",
    comparison="Requires team kill data",
    direction="neutral",
    percent=0.0
))
```

**Better Fix**: Use Option C - replace with Solo Kill Rate
```python
# Calculate solo kill rate instead
solo_kill_rate = kills / (kills + assists) if (kills + assists) > 0 else 0

metrics.append(FaultlinesMetricModel(
    id="solo_kill_rate",
    label="Solo Kill Rate",
    unit="%",
    value=solo_kill_rate,
    displayValue=f"{solo_kill_rate*100:.0f}%",
    comparison=f"+{(solo_kill_rate - 0.4)*100:.0f}% vs cohort",
    direction="positive" if solo_kill_rate > 0.4 else "neutral",
    percent=solo_kill_rate
))
```

### Priority 2: Composure Index Trends

**Fix**: Track rolling consistency score
```python
# In _build_composure_index method
def calculate_consistency_score(values):
    """Calculate consistency (inverse of coefficient of variation)."""
    if len(values) < 2:
        return 0.5
    mean_val = statistics.mean(values)
    if mean_val == 0:
        return 0.0
    cv = statistics.stdev(values) / mean_val
    # Normalize: CV of 0 = perfect consistency (100), CV of 1+ = poor (0)
    return max(0, 1 - cv)

# Build trend with rolling windows
series_data = []
for i in range(10, 21):
    window_kdas = [m.get("kdaRatio", 0) for m in matches[max(0, i-5):i]]
    consistency = calculate_consistency_score(window_kdas)
    
    series_data.append(FaultlinesTrendPointModel(
        match=i,
        value=consistency,  # 0-1 score
        delta=consistency - previous_consistency if i > 10 else 0,
        minute=None,
        role=None,
        bucket=None,
        metric=None,
        low=None,
        mid=None,
        high=None,
        result=None,
        x=None,
        y=None,
        axis=None
    ))
```

---

## Summary of Changes Needed

| Issue | Location | Fix Type | Priority |
|-------|----------|----------|----------|
| Kill Participation = 0 | `_build_combat_efficiency_index()` | Replace with Solo Kill Rate or mark N/A | HIGH |
| Composure trends null | `_build_composure_index()` | Add rolling consistency calculation | MEDIUM |

---

## Testing After Fix

```bash
# Test with cant type#1998
curl "http://localhost:3000/api/battles/AE6W6hK5V8cX9u7QgudTQsrYaGQQafYzONYl3EieQwtcZTkatRhVRLLRqAITJMKhy04eYi0vdPYPbA/faultlines/summary" | \
  python -c "import sys, json; d = json.load(sys.stdin); 
  cei = d['data']['axes'][0];
  ci = d['data']['axes'][7];
  kp = [m for m in cei['metrics'] if m['id'] == 'kp'][0];
  print(f'KP Value: {kp[\"value\"]}');
  print(f'KP Display: {kp[\"displayValue\"]}');
  print(f'CI Trend Points: {len(ci[\"trend\"][\"series\"])}');
  print(f'CI Nulls: {sum(1 for p in ci[\"trend\"][\"series\"] if p[\"value\"] is None)}')"
```

Expected after fix:
- ✅ KP Value: 0.65 (or "N/A" if marked unavailable)
- ✅ KP Display: "65%" (or "N/A")
- ✅ CI Trend Points: 10
- ✅ CI Nulls: 0
