from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

import httpx

from app.core.config import get_settings
from app.schemas import Item, ItemCreate, LambdaProfileResponse, ProfileRequest, ProfileResponse

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
            # Step 1: Call Lambda function to check DynamoDB
            try:
                lambda_response = await self._query_lambda(request)
                
                if lambda_response:
                    # Profile found in DynamoDB
                    logger.info(f"Profile found in cache for {request.riot_id}")
                    return self._convert_lambda_response(lambda_response, request)
            except httpx.HTTPStatusError as e:
                # If query Lambda fails (500, etc.), log and continue to get-uuid API
                logger.warning(f"Query Lambda failed: {e}, proceeding to get-uuid API")
            
            # Step 2: Profile not found (404) or query failed - fetch from get-uuid API
            logger.info(
                f"Profile not found in cache for {request.riot_id}, "
                "fetching from get-uuid API"
            )
            try:
                lambda_profile, profile_response = await self._fetch_from_get_uuid_api(request)
                
                # Fire-and-forget: Save profile to DynamoDB (don't await)
                asyncio.create_task(self._save_profile_to_dynamodb(lambda_profile))
                
                return profile_response
            except httpx.HTTPStatusError as e:
                logger.error(f"Get-UUID API failed: {e}")
                raise
            except Exception as e:
                logger.error(f"Error calling get-uuid API: {e}")
                raise
            
        except Exception as e:
            logger.error(f"Unexpected error fetching profile: {e}")
            # Return mock data only if all APIs fail
            return self._mock_profile_response(request)

    async def _query_lambda(self, request: ProfileRequest) -> LambdaProfileResponse | None:
        """
        Query the Lambda function to check if profile exists in DynamoDB.
        
        Returns:
            LambdaProfileResponse if found (200), None if not found (404)
            
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
            
            if response.status_code == 200:
                data = response.json()
                # Lambda returns: {"message": "Profile found", "profile": {...}}
                profile_data = data.get("profile", {})
                return LambdaProfileResponse(**profile_data)
            
            if response.status_code == 404:
                # Profile not found in DynamoDB
                return None
            
            # Other errors
            response.raise_for_status()
            return None

    async def _fetch_from_get_uuid_api(
        self, request: ProfileRequest
    ) -> tuple[LambdaProfileResponse, ProfileResponse]:
        """
        Fetch profile from get-uuid API when not found in DynamoDB cache.
        
        The get-uuid API returns the same format as the query Lambda (LambdaProfileResponse).
        
        Args:
            request: ProfileRequest containing riot_id and region
            
        Returns:
            Tuple of (LambdaProfileResponse, ProfileResponse) - raw data and converted response
            
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
            
            # The get-uuid API returns: {"message": "...", "profile": {...}}
            # Same format as the query Lambda
            profile_data = data.get("profile", {})
            lambda_profile = LambdaProfileResponse(**profile_data)
            
            # Convert to ProfileResponse format
            profile_response = self._convert_lambda_response(lambda_profile, request)
            
            return lambda_profile, profile_response

    async def _save_profile_to_dynamodb(self, lambda_profile: LambdaProfileResponse) -> None:
        """
        Save profile data to DynamoDB via create-profile API (fire-and-forget).
        
        This method is called as a background task and doesn't need to be awaited.
        
        Args:
            lambda_profile: LambdaProfileResponse containing profile data to save
        """
        try:
            # Convert LambdaProfileResponse to dict for the API
            payload = {
                "puuid": lambda_profile.puuid,
                "summonerName": lambda_profile.summoner_name,
                "tagLine": lambda_profile.tag_line,
                "region": lambda_profile.region,
                "createdAt": lambda_profile.created_at,
                "updatedAt": lambda_profile.updated_at,
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.settings.lambda_create_profile_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                logger.info(f"Profile saved to DynamoDB for puuid: {lambda_profile.puuid}")
        except Exception as e:
            # Log error but don't propagate since this is fire-and-forget
            logger.error(f"Failed to save profile to DynamoDB: {e}")

    def _convert_lambda_response(
        self, lambda_profile: LambdaProfileResponse, request: ProfileRequest
    ) -> ProfileResponse:
        """Convert Lambda/DynamoDB response to API response format."""
        return ProfileResponse(
            riot_id=request.riot_id,
            region=lambda_profile.region,
            summoner_name=lambda_profile.summoner_name,
            level=100,  # TODO: Add level to DynamoDB schema
            profile_icon_id=4608,  # TODO: Add icon ID to DynamoDB schema
            message=f"Profile retrieved from cache (updated: {lambda_profile.updated_at})",
        )

    def _mock_profile_response(self, request: ProfileRequest) -> ProfileResponse:
        """Generate mock profile response (fallback)."""
        parts = request.riot_id.split("#")
        game_name = parts[0] if len(parts) > 0 else "Unknown"
        
        return ProfileResponse(
            riot_id=request.riot_id,
            region=request.region.lower(),
            summoner_name=game_name,
            level=150,
            profile_icon_id=4608,
            message=f"Profile for {request.riot_id} (mock data - API integration pending)",
        )


profile_service = ProfileService()
