"""Debug script to inspect match data structure from Lambda API."""
import asyncio
import httpx
import json


async def fetch_and_inspect_matches():
    """Fetch matches and print the data structure."""
    
    # Test PUUID
    puuid = "tSKLz_gpZSezbacJloeJRLAv3lik91-wVU6UGa0BzOjnsdqVtIPe3yqENCGD5CT-0xsJI_KjbPLbRQ"
    lambda_url = "https://4x454duo26y5k7lkblp2sfvgq40xrcpn.lambda-url.eu-north-1.on.aws/"
    
    print(f"Fetching matches for PUUID: {puuid}")
    print(f"Lambda URL: {lambda_url}\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            lambda_url,
            json={"puuid": puuid},
        )
        response.raise_for_status()
        
        data = response.json()
        
        print("=" * 80)
        print("RESPONSE STRUCTURE")
        print("=" * 80)
        print(f"Response type: {type(data)}")
        print(f"Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        print()
        
        # Handle wrapped response
        if "matches" in data:
            matches = data.get("matches", [])
        elif isinstance(data, dict) and "body" in data:
            body_data = data["body"]
            body = json.loads(body_data) if isinstance(body_data, str) else body_data
            matches = body.get("matches", [])
        else:
            matches = []
        
        print(f"Number of matches: {len(matches)}")
        print()
        
        if matches:
            print("=" * 80)
            print("FIRST MATCH STRUCTURE")
            print("=" * 80)
            first_match = matches[0]
            print(f"Match type: {type(first_match)}")
            print(f"\nAvailable keys ({len(first_match.keys())} total):")
            for key in sorted(first_match.keys()):
                value = first_match[key]
                value_type = type(value).__name__
                value_preview = str(value)[:50] if value is not None else "None"
                print(f"  {key:30s} = {value_preview:50s} ({value_type})")
            
            print("\n" + "=" * 80)
            print("KEY FIELDS FOR BATTLE SUMMARY")
            print("=" * 80)
            key_fields = [
                "win", "kills", "deaths", "assists", "championName",
                "teamPosition", "gameDuration", "kdaRatio", "visionScore",
                "goldPerMinute", "firstBloodKill", "dragonKills", "baronKills",
                "riftHeraldKills", "teamEarlySurrendered"
            ]
            
            for field in key_fields:
                value = first_match.get(field)
                print(f"  {field:30s} = {value}")
            
            print("\n" + "=" * 80)
            print("SAMPLE OF WINS/LOSSES")
            print("=" * 80)
            for i, match in enumerate(matches[:5]):
                win = match.get("win")
                champ = match.get("championName", "Unknown")
                kda = match.get("kdaRatio", 0)
                print(f"  Match {i+1}: {'WIN' if win else 'LOSS':4s} - {champ:15s} (KDA: {kda})")
            
            print("\n" + "=" * 80)
            print("FULL FIRST MATCH DATA")
            print("=" * 80)
            print(json.dumps(first_match, indent=2))
        else:
            print("No matches found!")


if __name__ == "__main__":
    asyncio.run(fetch_and_inspect_matches())
