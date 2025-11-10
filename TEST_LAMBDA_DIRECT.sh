#!/bin/bash

# Direct Lambda Testing Script
# Tests the text generation Lambda endpoint with various models and prompts

LAMBDA_URL="https://hkeufmkvn7hvrutzxog4bzpijm0wpifk.lambda-url.eu-north-1.on.aws/"

echo "================================================"
echo "Lambda Text Generation Direct Testing"
echo "URL: $LAMBDA_URL"
echo "================================================"
echo ""

# Test 1: Simple prompt with DeepSeek-R1
echo "Test 1: DeepSeek-R1 - Simple Prompt"
echo "------------------------------------"
echo "Request: DeepSeek-R1 model with simple question"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "What is 2+2? Answer in one sentence.",
    "model": "DeepSeek-R1",
    "temperature": 0.7,
    "maxTokens": 100
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Test 2: Simple prompt with Amazon Nova Micro
echo "Test 2: Amazon Nova Micro - Simple Prompt"
echo "------------------------------------------"
echo "Request: Amazon Nova Micro model with simple question"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "What is 2+2? Answer in one sentence.",
    "model": "Amazon Nova Micro",
    "temperature": 0.7,
    "maxTokens": 100
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Test 3: League of Legends analysis with DeepSeek-R1
echo "Test 3: DeepSeek-R1 - LoL Analysis"
echo "-----------------------------------"
echo "Request: Complex LoL gameplay analysis"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "You are an expert League of Legends analyst.\n\nContext: Player has 65% win rate, 4.2 KDA, plays mostly ADC with Jinx (70% WR) and Caitlyn (60% WR). Recent matches show strong late game but weak early laning.\n\nTask: Provide 2 specific tips to improve early game performance.\n\nRequirements:\n- Keep response under 3 sentences\n- Be specific and actionable\n- Use League of Legends terminology",
    "model": "DeepSeek-R1",
    "temperature": 0.7,
    "maxTokens": 500
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Test 4: League of Legends analysis with Amazon Nova Micro
echo "Test 4: Amazon Nova Micro - LoL Analysis"
echo "-----------------------------------------"
echo "Request: Same LoL analysis with fallback model"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "You are an expert League of Legends analyst.\n\nContext: Player has 65% win rate, 4.2 KDA, plays mostly ADC with Jinx (70% WR) and Caitlyn (60% WR). Recent matches show strong late game but weak early laning.\n\nTask: Provide 2 specific tips to improve early game performance.\n\nRequirements:\n- Keep response under 3 sentences\n- Be specific and actionable\n- Use League of Legends terminology",
    "model": "Amazon Nova Micro",
    "temperature": 0.7,
    "maxTokens": 500
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Test 5: Long response test with DeepSeek-R1
echo "Test 5: DeepSeek-R1 - Long Response"
echo "------------------------------------"
echo "Request: Request with higher max tokens"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "Analyze this League of Legends match:\n- Champion: Yasuo\n- Result: Win\n- KDA: 12/3/8\n- CS: 245 in 32 minutes\n- Vision Score: 15\n- Damage: 35,000\n\nProvide comprehensive analysis covering:\n1. Overall performance\n2. Strengths demonstrated\n3. Areas for improvement\n4. Specific recommendations",
    "model": "DeepSeek-R1",
    "temperature": 0.7,
    "maxTokens": 1000
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Test 6: Invalid model test
echo "Test 6: Invalid Model Test"
echo "---------------------------"
echo "Request: Testing with non-existent model"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "Hello, world!",
    "model": "GPT-4-Turbo",
    "temperature": 0.7,
    "maxTokens": 100
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Test 7: Temperature variations
echo "Test 7: Temperature Test (Creative vs Conservative)"
echo "---------------------------------------------------"
echo "Request A: Low temperature (0.3) - Conservative"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "Describe an aggressive ADC playstyle in one sentence.",
    "model": "Amazon Nova Micro",
    "temperature": 0.3,
    "maxTokens": 100
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "Request B: High temperature (0.9) - Creative"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "Describe an aggressive ADC playstyle in one sentence.",
    "model": "Amazon Nova Micro",
    "temperature": 0.9,
    "maxTokens": 100
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Test 8: Minimal payload test
echo "Test 8: Minimal Payload"
echo "-----------------------"
echo "Request: Only required fields"
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -w "\n\n📊 HTTP Status: %{http_code} | Time: %{time_total}s\n" \
  -d '{
    "prompt": "Hello"
  }' 2>&1 | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "================================================"
echo ""

# Summary
echo "🎯 Test Summary"
echo "==============="
echo "✅ Test 1: DeepSeek-R1 simple prompt"
echo "✅ Test 2: Amazon Nova Micro simple prompt"
echo "✅ Test 3: DeepSeek-R1 complex LoL analysis"
echo "✅ Test 4: Amazon Nova Micro LoL analysis"
echo "✅ Test 5: DeepSeek-R1 long response (1000 tokens)"
echo "✅ Test 6: Invalid model handling"
echo "✅ Test 7: Temperature variations"
echo "✅ Test 8: Minimal payload"
echo ""
echo "📝 Key Observations:"
echo "- Check if Lambda actually uses DeepSeek-R1 or falls back"
echo "- Compare response quality between models"
echo "- Verify response times stay under 30s"
echo "- Check if temperature affects output variation"
echo ""
echo "================================================"
