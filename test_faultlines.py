"""Test script for Faultlines endpoint."""
import asyncio
import httpx
import json


async def test_faultlines():
    """Test the Faultlines analysis endpoint."""
    
    # Test PUUID - cant type#1998
    puuid = "AE6W6hK5V8cX9u7QgudTQsrYaGQQafYzONYl3EieQwtcZTkatRhVRLLRqAITJMKhy04eYi0vdPYPbA"
    url = f"http://localhost:3000/api/battles/{puuid}/faultlines/summary"
    
    print("Testing Faultlines: Strengths and Shadows")
    print("=" * 80)
    print(f"URL: {url}\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Print status
            status = data.get("status")
            print(f"Status: {status}\n")
            
            # If READY, print structure
            if status == "READY":
                data_obj = data.get("data", {})
                
                # Summary
                summary = data_obj.get("summary", {})
                print("Summary:")
                print(f"  Player Label: {summary.get('playerLabel')}")
                print(f"  Cohort Label: {summary.get('cohortLabel')}")
                print(f"  Window Label: {summary.get('windowLabel')}")
                print()
                
                # Axes
                axes = data_obj.get("axes", [])
                print(f"Axes ({len(axes)} total):")
                print("-" * 80)
                for axis in axes:
                    label = axis.get("label", "Unknown")
                    score = axis.get("score", 0)
                    metrics_count = len(axis.get("metrics", []))
                    trend = axis.get("trend", {})
                    has_series = len(trend.get("series", []))
                    charts = axis.get("charts", [])
                    narrative = axis.get("narrative", {})
                    
                    print(f"\n{label}: {score:.1f}/100")
                    print(f"  Metrics: {metrics_count}")
                    print(f"  Trend Series: {has_series}")
                    print(f"  Charts: {len(charts)}")
                    print(f"  Narrative: {narrative.get('headline', 'N/A')[:60]}...")
                
                # Insights
                insights = data_obj.get("insights", [])
                print(f"\n{'=' * 80}")
                print(f"Insights ({len(insights)} total):")
                print("-" * 80)
                for i, insight in enumerate(insights, 1):
                    if isinstance(insight, str):
                        print(f"\n{i}. {insight}")
                    else:
                        category = insight.get("category", "Unknown")
                        headline = insight.get("headline", "N/A")
                        print(f"\n{i}. {category}")
                        print(f"   {headline}")
                
                print(f"\n{'=' * 80}")
                print("✅ Faultlines endpoint is working correctly!")
                print("=" * 80)
                
                # Save full response for inspection
                with open("faultlines_response.json", "w") as f:
                    json.dump(data, f, indent=2)
                print("\n💾 Full response saved to: faultlines_response.json")
                
            else:
                print(f"Response: {json.dumps(data, indent=2)}")
                
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_faultlines())
