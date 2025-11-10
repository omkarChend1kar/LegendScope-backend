#!/usr/bin/env python3
"""
Test script for Voice in the Fog starter topics endpoints.
Tests the simplified GET-based APIs.
"""

import requests
import json
from urllib.parse import quote

BASE_URL = "http://localhost:3000/api"

# Test player IDs (example)
TEST_PLAYER_ID = "aWFn0-gfxZx9P8jvOjYNXexP-EhyDFXW7kEeD1m7Dca-w72x8ggJdnv3FQKHRBc1S99Xq0Xc-zx50w"

# Starter topics for each endpoint
ECHOES_TOPICS = [
    "Battles Fought",
    "Claim / Fall Ratio",
    "Longest Claim & Fall Streaks",
    "Clutch Battles",
    "Role Influence"
]

PATTERNS_TOPICS = [
    "Aggression",
    "Survivability",
    "Skirmish Bias",
    "Objective Impact",
    "Vision Discipline",
    "Utility",
    "Tempo Profile"
]

FAULTLINES_TOPICS = [
    "Combat Efficiency Index",
    "Objective Reliability Index",
    "Survival Discipline Index",
    "Vision & Awareness Index",
    "Economy Utilization Index",
    "Momentum Index",
    "Composure Index"
]


def test_endpoint(endpoint_name: str, player_id: str, topic: str):
    """Test a single endpoint with a topic."""
    url = f"{BASE_URL}/voice-in-fog/{endpoint_name}/{player_id}"
    params = {"starter_topic": topic}
    
    print(f"\n{'='*80}")
    print(f"Testing: {endpoint_name}")
    print(f"Topic: {topic}")
    print(f"URL: {url}?starter_topic={quote(topic)}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Starter Topic: {data.get('starterTopic', 'N/A')}")
            print(f"Insight (first 200 chars): {data.get('insight', 'N/A')[:200]}...")
            return True
        else:
            print(f"Error Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False


def main():
    """Run tests for all endpoints."""
    print("=" * 80)
    print("Voice in the Fog Starter Topics - API Test Suite")
    print("=" * 80)
    
    results = {
        "echoes": [],
        "patterns": [],
        "faultlines": []
    }
    
    # Test one topic from each category
    print("\n\n### Testing Echoes of Battle ###")
    results["echoes"].append(
        test_endpoint("echoes-of-battle", TEST_PLAYER_ID, ECHOES_TOPICS[0])
    )
    
    print("\n\n### Testing Patterns Beneath Chaos ###")
    results["patterns"].append(
        test_endpoint("patterns-beneath-chaos", TEST_PLAYER_ID, PATTERNS_TOPICS[0])
    )
    
    print("\n\n### Testing Faultlines ###")
    results["faultlines"].append(
        test_endpoint("faultlines-analysis", TEST_PLAYER_ID, FAULTLINES_TOPICS[0])
    )
    
    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Echoes of Battle: {'✅ PASS' if all(results['echoes']) else '❌ FAIL'}")
    print(f"Patterns Beneath Chaos: {'✅ PASS' if all(results['patterns']) else '❌ FAIL'}")
    print(f"Faultlines: {'✅ PASS' if all(results['faultlines']) else '❌ FAIL'}")
    
    total_tests = sum(len(v) for v in results.values())
    passed_tests = sum(sum(v) for v in results.values())
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")


if __name__ == "__main__":
    main()
