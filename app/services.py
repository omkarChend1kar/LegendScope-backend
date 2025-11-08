from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

import httpx

from app.core.config import get_settings
from app.schemas import (
    ChampionSummaryModel,
    Item,
    ItemCreate,
    NarrativeSummaryModel,
    ProfileRequest,
    ProfileResponse,
    RiskProfileModel,
    RoleSummaryModel,
    SummaryCardsModel,
)

logger = logging.getLogger(__name__)


@dataclass
class ItemStore:
    _lock: Lock = field(default_factory=Lock)
    _items: dict[int, Item] = field(default_factory=dict)
    _next_id: int = 1

    def list_items(self) -> list[Item]:
        with self._lock:
            return list(self._items.values())

    def get_item(self, item_id: int) -> Item | None:
        with self._lock:
            return self._items.get(item_id)

    def create_item(self, item_in: ItemCreate) -> Item:
        with self._lock:
            item = Item(
                id=self._next_id,
                name=item_in.name,
                description=item_in.description,
                price=item_in.price,
                created_at=datetime.utcnow(),
            )
            self._items[self._next_id] = item
            self._next_id += 1
            return item

    def delete_item(self, item_id: int) -> bool:
        with self._lock:
            if item_id not in self._items:
                return False
            del self._items[item_id]
            return True


store = ItemStore()


class ProfileService:
    """Service for handling player profile operations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.http_client = httpx.Client(timeout=10.0)

    async def get_profile(self, request: ProfileRequest) -> ProfileResponse:
        """
        Fetch player profile by Riot ID and region.
        
        Flow:
        1. Query Lambda function (checks DynamoDB for cached profile)
        2. If found (200), return the cached profile
        3. If not found (404):
           a. Call get-uuid API to fetch profile data
           b. Fire-and-forget save to DynamoDB via create-profile API
           c. Return the profile data
        
        Args:
            request: ProfileRequest containing riot_id and region
            
        Returns:
            ProfileResponse with player profile data
            
        Raises:
            httpx.HTTPStatusError: If Lambda returns an error other than 404
            Exception: For other unexpected errors
        """
        try:
            try:
                cached_profile = await self._query_lambda(request)
                
                if cached_profile:
                    logger.info(f"Profile found in cache for {request.riot_id}")
                    return cached_profile
            except httpx.HTTPStatusError as e:
                logger.warning(f"Query Lambda failed: {e}, proceeding to get-uuid API")
            
            logger.info(
                f"Profile not found in cache for {request.riot_id}, "
                "fetching from get-uuid API"
            )
            try:
                profile = await self._fetch_from_get_uuid_api(request)
                asyncio.create_task(self._save_profile_to_dynamodb(profile))
                return profile
            except httpx.HTTPStatusError as e:
                logger.error(f"Get-UUID API failed: {e}")
                raise
            except Exception as e:
                logger.error(f"Error calling get-uuid API: {e}")
                raise
            
        except Exception as e:
            logger.error(f"Unexpected error fetching profile: {e}")
            raise

    async def _query_lambda(self, request: ProfileRequest) -> ProfileResponse | None:
        """
        Query the Lambda function to check if profile exists in DynamoDB.
        
        Returns:
            ProfileResponse if found (200 with profile data)
            None if not found (404 OR 200 with status="not_found")
            
        Raises:
            httpx.HTTPStatusError: For errors other than 404
        """
        payload = {
            "riotId": request.riot_id,
            "region": request.region,
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.settings.lambda_profile_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            
            print(f"Lambda query response status: {response.status_code} for {request.riot_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"Lambda query response data: {data} for {request.riot_id}")
                
                if data.get("status") == "not_found":
                    logger.info(
                        f"Profile not found in cache (status: not_found) for {request.riot_id}"
                    )
                    return None
                
                profile_data = data.get("profile", {})
                if profile_data:
                    return ProfileResponse(**profile_data)
                return None
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return None

    async def _fetch_from_get_uuid_api(self, request: ProfileRequest) -> ProfileResponse:
        """
        Fetch profile from get-uuid API when not found in DynamoDB cache.
        
        The get-uuid API returns profile data directly (not wrapped in a "profile" key).
        Response format: {"riotId": "...", "puuid": "...", "summonerName": "...", ...}
        
        Args:
            request: ProfileRequest containing riot_id and region
            
        Returns:
            ProfileResponse with player profile data
            
        Raises:
            httpx.HTTPStatusError: If get-uuid API returns an error
        """
        payload = {
            "riotId": request.riot_id,
            "region": request.region,
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.settings.lambda_get_uuid_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"Get-UUID API response data: {data} for {request.riot_id}")
            
            if "riotId" not in data:
                data["riotId"] = request.riot_id
            
            logger.info(
                f"Fetched profile from get-uuid API for {data.get('summonerName', 'unknown')}"
            )
            profile = ProfileResponse(**data)
            
            return profile

    async def _save_profile_to_dynamodb(self, profile: ProfileResponse) -> None:
        """
        Save profile data to DynamoDB via create-profile API (fire-and-forget).
        
        This method is called as a background task and doesn't need to be awaited.
        
        Args:
            profile: ProfileResponse containing profile data to save
        """
        try:
            payload = {
                "riotId": profile.riot_id,
                "puuid": profile.puuid,
                "summonerName": profile.summoner_name,
                "tagLine": profile.tag_line,
                "region": profile.region,
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.settings.lambda_create_profile_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                logger.info(f"Profile saved to DynamoDB for puuid: {profile.puuid}")
        except Exception as e:
            logger.error(f"Failed to save profile to DynamoDB: {e}")


profile_service = ProfileService()


class BattleSummaryService:
    """Service for handling battle summary analytics."""

    def get_last_twenty_summary_cards(self, player_id: str) -> SummaryCardsModel:
        """Get summary cards for last 20 battles."""
        battles_fought = 20
        claims = 11
        falls = 9
        ratio = claims if falls == 0 else claims / falls

        return SummaryCardsModel(
            battlesFought=battles_fought,
            claims=claims,
            falls=falls,
            claimFallRatio=round(ratio, 2),
            longestClaimStreak=3,
            longestFallStreak=2,
            clutchGames=4,
            surrenderRate=10,
            averageMatchDuration="28m 14s",
        )

    def get_last_twenty_role_summaries(self, player_id: str) -> list[RoleSummaryModel]:
        """Get role performance summaries for last 20 battles."""
        seed = [
            {
                "role": "Jungle",
                "games": 7,
                "claims": 5,
                "falls": 2,
                "averageKda": 3.8,
                "firstBloodRate": 64,
                "visionScore": 28,
                "goldPerMinute": 412,
            },
            {
                "role": "Mid Lane",
                "games": 5,
                "claims": 2,
                "falls": 3,
                "averageKda": 2.1,
                "firstBloodRate": 22,
                "visionScore": 18,
                "goldPerMinute": 385,
            },
            {
                "role": "Bot Lane",
                "games": 4,
                "claims": 3,
                "falls": 1,
                "averageKda": 4.2,
                "firstBloodRate": 58,
                "visionScore": 16,
                "goldPerMinute": 436,
            },
            {
                "role": "Support",
                "games": 3,
                "claims": 1,
                "falls": 2,
                "averageKda": 2.4,
                "firstBloodRate": 12,
                "visionScore": 31,
                "goldPerMinute": 255,
            },
            {
                "role": "Top Lane",
                "games": 1,
                "claims": 0,
                "falls": 1,
                "averageKda": 1.8,
                "firstBloodRate": 0,
                "visionScore": 14,
                "goldPerMinute": 362,
            },
        ]

        return [
            RoleSummaryModel(
                **role,
                winRate=0 if role["games"] == 0 else round((role["claims"] / role["games"]) * 100),
            )
            for role in seed
        ]

    def get_last_twenty_champion_summaries(self, player_id: str) -> list[ChampionSummaryModel]:
        """Get champion performance summaries for last 20 battles."""
        seed = [
            {"name": "Lee Sin", "games": 5, "claims": 4, "color": "#60a5fa"},
            {"name": "Ahri", "games": 4, "claims": 2, "color": "#8b5cf6"},
            {"name": "Kai'Sa", "games": 3, "claims": 2, "color": "#22d3ee"},
            {"name": "Thresh", "games": 3, "claims": 1, "color": "#f97316"},
            {"name": "Sejuani", "games": 2, "claims": 1, "color": "#facc15"},
            {"name": "Others", "games": 3, "claims": 1, "color": "#64748b"},
        ]

        return [
            ChampionSummaryModel(
                **champ,
                winRate=(
                    0 if champ["games"] == 0 else round((champ["claims"] / champ["games"]) * 100)
                ),
            )
            for champ in seed
        ]

    def get_last_twenty_risk_profile(self, player_id: str) -> RiskProfileModel:
        """Get risk profile analysis for last 20 battles."""
        roles = self.get_last_twenty_role_summaries(player_id)

        profile = {
            "earlyAggression": 68,
            "earlyFalls": 32,
            "objectiveControl": 58,
            "visionCommitment": 74,
        }

        highest_pressure_role = min(roles, key=lambda r: r.win_rate)

        aggression_phrase = (
            "You open with decisive strikes"
            if profile["earlyAggression"] >= 60
            else "You approach the opening moments with patience"
        )

        vulnerability_phrase = (
            "but early missteps risk surrendering tempo"
            if profile["earlyFalls"] >= 40
            else "while keeping early skirmishes largely under control"
        )

        strength_phrase = "— vision remains your lasting strength."
        role_phrase = (
            f" Guard your {highest_pressure_role.role.lower()} rotations to protect that edge."
        )

        narrative = f"{aggression_phrase} {vulnerability_phrase} {strength_phrase}{role_phrase}"

        return RiskProfileModel(**profile, narrative=narrative)

    def get_last_twenty_narrative(self, player_id: str) -> NarrativeSummaryModel:
        """Get narrative summary for last 20 battles."""
        summary_cards = self.get_last_twenty_summary_cards(player_id)
        roles = self.get_last_twenty_role_summaries(player_id)
        champions = self.get_last_twenty_champion_summaries(player_id)
        risk_profile = self.get_last_twenty_risk_profile(player_id)

        sorted_roles = sorted(roles, key=lambda r: r.win_rate, reverse=True)
        top_role = sorted_roles[0]
        struggling_role = sorted_roles[-1]

        sorted_champions = sorted(champions, key=lambda c: c.claims, reverse=True)
        primary_champion = sorted_champions[0]
        secondary_champion = (
            sorted_champions[1] if len(sorted_champions) > 1 else sorted_champions[0]
        )

        headline = f"Strategist of the {top_role.role}"

        body = " ".join(
            [
                f"Across {summary_cards.battles_fought} battles you carved "
                f"{summary_cards.claims} victories, leaning on {top_role.role.lower()} "
                f"at a {top_role.win_rate}% claim rate.",
                f"{struggling_role.role} remains the proving ground, but your arsenal of "
                f"{primary_champion.name} and {secondary_champion.name} keeps momentum "
                "within reach.",
                f"Channel the {risk_profile.vision_commitment}% vision commitment into "
                f"{struggling_role.role.lower()} resilience to seize the next front.",
            ]
        )

        return NarrativeSummaryModel(headline=headline, body=body)


battle_summary_service = BattleSummaryService()
