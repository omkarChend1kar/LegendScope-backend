"""Compare Faultlines responses for different UUIDs."""
import asyncio
import httpx
import json


async def test_uuid(puuid: str, name: str):
    """Test a specific UUID and show response stats."""
    print(f"\n{'=' * 80}")
    print(f"Testing: {name}")
    print(f"PUUID: {puuid}")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check profile status
        profile_resp = await client.post(
            "http://localhost:3000/api/profile",
            json={"puuid": puuid, "region": "na1"}
        )
        profile_data = profile_resp.json()
        print(f"\n1. Profile Status:")
        print(f"   Riot ID: {profile_data.get('riotId', 'N/A')}")
        print(f"   Last Matches: {profile_data.get('lastMatches', 'N/A')}")
        
        # Test Faultlines
        faultlines_resp = await client.get(
            f"http://localhost:3000/api/battles/{puuid}/faultlines/summary"
        )
        faultlines_data = faultlines_resp.json()
        
        print(f"\n2. Faultlines Response:")
        print(f"   Status: {faultlines_data.get('status')}")
        
        data = faultlines_data.get('data')
        if data:
            print(f"   Has Data: ✅ YES")
            
            summary = data.get('summary', {})
            print(f"\n3. Summary:")
            print(f"   Player Label: {summary.get('playerLabel')}")
            print(f"   Sample Size: {summary.get('sampleSize')} games")
            
            axes = data.get('axes', [])
            print(f"\n4. Axes ({len(axes)} total):")
            for axis in axes:
                label = axis.get('label')
                score = axis.get('score')
                metrics = axis.get('metrics', [])
                print(f"   • {label}: {score}/100 ({len(metrics)} metrics)")
                
                # Check for null values in metrics
                null_count = sum(1 for m in metrics if m.get('value') is None)
                if null_count > 0:
                    print(f"     ⚠️  {null_count} metrics have null values")
            
            insights = data.get('insights', [])
            print(f"\n5. Insights: {len(insights)} generated")
            
            # Save full response
            filename = f"faultlines_{name.replace(' ', '_').replace('#', '')}.json"
            with open(filename, 'w') as f:
                json.dump(faultlines_data, f, indent=2)
            print(f"\n💾 Saved to: {filename}")
        else:
            print(f"   Has Data: ❌ NO")
            print(f"   Reason: Check if matches are stored in DynamoDB")


async def main():
    """Test multiple UUIDs."""
    uuids = [
        ("AE6W6hK5V8cX9u7QgudTQsrYaGQQafYzONYl3EieQwtcZTkatRhVRLLRqAITJMKhy04eYi0vdPYPbA", "cant type#1998"),
        ("Ek_8y5Wv6CdHbxVIsUhh-Jo_ADM3PAzmrar8_MICAU4V8hbKKu5cxwQnJRj-azp4n7wGBs4902nfug", "STEPZ #NA7"),
    ]
    
    for puuid, name in uuids:
        await test_uuid(puuid, name)
    
    print(f"\n{'=' * 80}")
    print("✅ Comparison Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
