# DeepSeek-R1 Integration with Multi-Tier Fallback

## Overview

The text generation service has been updated to use **DeepSeek-R1** as the primary model with a robust multi-tier fallback system for reliability.

## Model Hierarchy

### 1. Primary Model: DeepSeek-R1
- **Purpose**: High-quality, reasoning-focused text generation
- **Timeout**: 15 seconds (allows for deeper reasoning)
- **Use Case**: Complex analysis, detailed insights, strategic recommendations

### 2. Fallback Model: Amazon Nova Micro
- **Purpose**: Fast, reliable fallback when DeepSeek-R1 is unavailable
- **Timeout**: 10 seconds (optimized for speed)
- **Use Case**: Quick insights, basic responses, time-sensitive queries

### 3. Rule-Based Fallback
- **Purpose**: Last resort when all AI models fail
- **Timeout**: Instant (no network call)
- **Use Case**: Graceful degradation, ensures API never fails

## Architecture

```
User Request
     ↓
Try DeepSeek-R1 (15s timeout)
     ↓
  Success? → Return response
     ↓ No
Try Amazon Nova Micro (10s timeout)
     ↓
  Success? → Return response
     ↓ No
Rule-Based Fallback → Return generic response
```

## Implementation Details

### Configuration

```python
class TextGenerationService:
    def __init__(self):
        self.lambda_url = "https://hkeufmkvn7hvrutzxog4bzpijm0wpifk.lambda-url.eu-north-1.on.aws/"
        self.primary_model = "DeepSeek-R1"        # Primary for quality
        self.fallback_model = "Amazon Nova Micro" # Fallback for reliability
        self.timeout = 15.0                       # Primary timeout
        self.use_ai = True                        # Enable/disable AI
```

### Two-Tier Generation Method

```python
async def generate_text_with_model_info(
    self, context, query, max_tokens=500, temperature=0.7
) -> tuple[str, str]:
    """
    Returns: (generated_text, model_name)
    
    Model selection logic:
    1. Try DeepSeek-R1 first
    2. If fails, try Amazon Nova Micro
    3. If both fail, use rule-based fallback
    """
```

### Model Request Flow

```python
async def _try_generate_with_model(
    self, context, query, model, max_tokens, temperature, timeout=None
) -> str | None:
    """
    Try a specific model, return None if fails.
    
    Handles:
    - Timeout exceptions (returns None)
    - HTTP errors (returns None)
    - Empty responses (returns None)
    - Successful generation (returns text)
    """
```

## API Response Format

### Success Response

```json
{
  "modelUsed": "DeepSeek-R1",
  "reply": "Based on your recent performance, focus on..."
}
```

### Fallback Response (Amazon Nova Micro)

```json
{
  "modelUsed": "Amazon Nova Micro",
  "reply": "Your gameplay shows strengths in..."
}
```

### Emergency Fallback

```json
{
  "modelUsed": "Rule-based",
  "reply": "Analysis complete."
}
```

## Logging and Monitoring

### Success Logs

```
INFO: Text generation request using DeepSeek-R1: What champions...
INFO: Successfully generated text with DeepSeek-R1: Based on your...
```

### Fallback Logs

```
WARNING: DeepSeek-R1 request timed out after 15.0s
WARNING: DeepSeek-R1 failed, trying Amazon Nova Micro
INFO: Text generation request using Amazon Nova Micro: What champions...
INFO: Successfully generated text with Amazon Nova Micro: Your gameplay...
```

### Emergency Fallback Logs

```
WARNING: Amazon Nova Micro request timed out after 10.0s
ERROR: All AI models failed, using rule-based fallback
INFO: Using rule-based fallback text generation
```

## Model Characteristics

### DeepSeek-R1

**Strengths:**
- Advanced reasoning capabilities
- Detailed, nuanced responses
- Better context understanding
- More strategic insights

**Weaknesses:**
- Slower response time (up to 15s)
- Higher resource requirements
- May be unavailable during high load

**Best For:**
- Complex analysis (Faultlines, Signature Playstyle)
- Strategic recommendations
- In-depth player profiling
- Multi-factor decision making

### Amazon Nova Micro

**Strengths:**
- Fast response time (~2-5s)
- High availability
- Consistent performance
- Low latency

**Weaknesses:**
- Less detailed reasoning
- Shorter responses
- Simpler analysis

**Best For:**
- Quick insights (Echoes of Battle)
- Pattern recognition
- Simple recommendations
- Real-time chat responses

### Rule-Based Fallback

**Strengths:**
- Instant response (<1ms)
- 100% availability
- No external dependencies
- Predictable behavior

**Weaknesses:**
- Generic responses
- No personalization
- Limited insight quality
- Not context-aware

**Best For:**
- Emergency fallback
- Service degradation
- Testing/debugging
- API health checks

## Performance Expectations

### Response Times

| Scenario | Model Used | Expected Time | Notes |
|----------|-----------|---------------|-------|
| DeepSeek-R1 Success | DeepSeek-R1 | 5-15s | Full reasoning capability |
| DeepSeek-R1 Timeout | Amazon Nova Micro | 15s + 3-8s | Fallback after timeout |
| Both Models Fail | Rule-based | 15s + 10s + instant | All fallbacks exhausted |
| Lambda 502 Error | Amazon Nova Micro | <1s + 3-8s | Fast failover |
| All Services Down | Rule-based | <1s | Emergency response |

### Cache Impact (with player_id)

| Request | Profile | Text Gen | Total Time |
|---------|---------|----------|------------|
| First (DeepSeek) | 5-10s | 5-15s | 10-25s |
| Second (cached) | <1s | 5-15s | 5-15s |
| First (Nova) | 5-10s | 3-8s | 8-18s |
| Second (cached) | <1s | 3-8s | 3-8s |

## Configuration Options

### Enable/Disable AI

```python
# In text_generation.py
text_service.use_ai = False  # Use only rule-based fallback
text_service.use_ai = True   # Enable AI models (default)
```

### Adjust Timeouts

```python
# Primary model timeout
text_service.timeout = 20.0  # More time for DeepSeek-R1

# Fallback model timeout (in _try_generate_with_model)
await self._try_generate_with_model(..., timeout=15.0)
```

### Change Model Order

```python
# Swap primary and fallback
text_service.primary_model = "Amazon Nova Micro"
text_service.fallback_model = "DeepSeek-R1"
```

## Testing

### Test DeepSeek-R1 (if available)

```bash
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze my recent gameplay patterns"
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "modelUsed": "DeepSeek-R1",
  "reply": "Based on your recent matches, you demonstrate..."
}
```

### Test Amazon Nova Micro Fallback

```bash
# If DeepSeek-R1 is down, should auto-fallback
curl -X POST http://localhost:3000/api/voice-in-fog/general-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I focus on?"
  }' | python3 -m json.tool
```

**Expected Output:**
```json
{
  "modelUsed": "Amazon Nova Micro",
  "reply": "Focus on vision control and objective priority..."
}
```

### Test Rule-Based Fallback

```bash
# Disable AI to force rule-based fallback
# (Requires code change: text_service.use_ai = False)
```

**Expected Output:**
```json
{
  "modelUsed": "Rule-based",
  "reply": "Analysis complete."
}
```

## Troubleshooting

### Issue: All requests use Rule-based

**Possible Causes:**
1. Lambda function not deployed/available
2. Lambda URL incorrect
3. Lambda returns 502/504 errors
4. Network connectivity issues

**Solution:**
- Check AWS Lambda console
- Verify Lambda URL in code
- Check Lambda logs for errors
- Test Lambda endpoint directly

### Issue: DeepSeek-R1 always times out

**Possible Causes:**
1. Lambda cold start too long
2. Model loading takes time
3. Insufficient Lambda resources
4. Timeout too short (< 15s)

**Solution:**
- Increase timeout to 20-30s
- Use Lambda provisioned concurrency
- Increase Lambda memory/CPU
- Monitor Lambda execution time

### Issue: Amazon Nova Micro always fails

**Possible Causes:**
1. Lambda doesn't support this model
2. Model name mismatch
3. Lambda error handling issues

**Solution:**
- Check Lambda supported models
- Verify model name exact match
- Review Lambda implementation
- Test Lambda with curl directly

## Migration Guide

### From Old System

**Before:**
```python
# Single model, generic fallback
reply = await text_service.generate_text(context, query)
# Always returned "Amazon Nova Micro"
```

**After:**
```python
# Multi-model with intelligent fallback
reply, model = await text_service.generate_text_with_model_info(context, query)
# Returns actual model used: "DeepSeek-R1", "Amazon Nova Micro", or "Rule-based"
```

### Voice in Fog Service Update

**Before:**
```python
reply = await self.text_service.generate_text(context, query)
return {
    "modelUsed": "Amazon Nova Micro",  # Hardcoded, inaccurate
    "reply": reply
}
```

**After:**
```python
reply, model_used = await self.text_service.generate_text_with_model_info(context, query)
return {
    "modelUsed": model_used,  # Actual model used
    "reply": reply
}
```

## Benefits

✅ **Higher Quality**: DeepSeek-R1 provides better reasoning and insights

✅ **Reliability**: Multi-tier fallback ensures service never fails

✅ **Transparency**: Users see which model generated their response

✅ **Flexibility**: Easy to swap models or adjust priorities

✅ **Graceful Degradation**: Smooth fallback from best to good to basic

✅ **Monitoring**: Clear logs show which models are working/failing

## Future Enhancements

### Potential Improvements

1. **Smart Model Selection**
   - Use Nova Micro for simple queries
   - Use DeepSeek-R1 for complex analysis
   - Query classification before model selection

2. **Parallel Requests**
   - Call both models simultaneously
   - Use fastest response
   - Cancel slower request

3. **Model Performance Tracking**
   - Track success rates per model
   - Automatic circuit breaker for failing models
   - Adaptive timeout based on history

4. **Response Quality Scoring**
   - Validate response quality
   - Retry with different model if quality low
   - Learn from user feedback

5. **Custom Model Pool**
   - Support more models (GPT-4, Claude, etc.)
   - Dynamic model addition/removal
   - A/B testing different models

## Summary

The DeepSeek-R1 integration provides:
- **Primary**: DeepSeek-R1 for high-quality reasoning (15s timeout)
- **Fallback**: Amazon Nova Micro for reliability (10s timeout)
- **Emergency**: Rule-based for guaranteed response (instant)

This ensures the best possible insights while maintaining 100% service availability! 🚀
