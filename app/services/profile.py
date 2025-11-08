from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import get_settings
from app.schemas import ProfileRequest, ProfileResponse

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for handling player profile operations."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_profile(self, request: ProfileRequest) -> ProfileResponse:
        """
        Fetch player profile by Riot ID or PUUID and region.
        
        Flow:
        1. Query Lambda function (checks DynamoDB for cached profile)
        2. If found (200), return the cached profile
        3. If not found (404):
           a. Call get-uuid API to fetch profile data (requires riot_id)
           b. Fire-and-forget save to DynamoDB via create-profile API
           c. Return the profile data
        
        Args:
            request: ProfileRequest containing riot_id (or puuid) and region
            
        Returns:
            ProfileResponse with player profile data
            
        Raises:
            ValueError: If neither riot_id nor puuid is provided
            httpx.HTTPStatusError: If Lambda returns an error other than 404
            Exception: For other unexpected errors
        """
        if not request.riot_id and not request.puuid:
            raise ValueError("Either riot_id or puuid must be provided")
        
        try:
            try:
                cached_profile = await self._query_lambda(request)
                
                if cached_profile:
                    identifier = request.riot_id or request.puuid
                    logger.info(f"Profile found in cache for {identifier}")
                    return cached_profile
            except httpx.HTTPStatusError as e:
                logger.warning(f"Query Lambda failed: {e}, proceeding to get-uuid API")
            
            # If no riot_id provided, we can't fetch from get-uuid API
            if not request.riot_id:
                raise ValueError(
                    "riot_id is required to fetch profile when not found in cache"
                )
            
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
        
        Supports querying by either riot_id or puuid.
        
        Returns:
            ProfileResponse if found (200 with profile data)
            None if not found (404 OR 200 with status="not_found")
            
        Raises:
            httpx.HTTPStatusError: For errors other than 404
        """
        payload = {}
        if request.riot_id:
            payload["riotId"] = request.riot_id
        if request.puuid:
            payload["puuid"] = request.puuid
        payload["region"] = request.region
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.settings.lambda_profile_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            
            identifier = request.riot_id or request.puuid
            logger.debug(
                f"Lambda query response status: {response.status_code} "
                f"for {identifier}"
            )
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Lambda query response data: {data} for {identifier}")
                
                if data.get("status") == "not_found":
                    logger.info(
                        f"Profile not found in cache (status: not_found) for {identifier}"
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
            
            logger.debug(f"Get-UUID API response data: {data} for {request.riot_id}")
            
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
        Also sets the last_matches status to NOT_STARTED and triggers match fetching.
        
        This method is called as a background task and doesn't need to be awaited.
        
        Args:
            profile: ProfileResponse containing profile data to save
        """
        # Import here to avoid circular imports
        from app.services.player_matches import player_matches_service
        from app.services.profile_status import profile_status_service
        
        try:
            payload = {
                "riotId": profile.riot_id,
                "puuid": profile.puuid,
                "summonerName": profile.summoner_name,
                "tagLine": profile.tag_line,
                "region": profile.region,
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Step 1: Create the profile
                try:
                    response = await client.post(
                        self.settings.lambda_create_profile_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()
                    logger.info(f"Profile saved to DynamoDB for puuid: {profile.puuid}")
                except httpx.HTTPStatusError as e:
                    # Profile might already exist, log and continue
                    if e.response.status_code == 409:
                        logger.warning(
                            f"Profile already exists for puuid: {profile.puuid}, continuing..."
                        )
                    else:
                        logger.error(
                            f"Failed to create profile: HTTP {e.response.status_code}. "
                            f"Response: {e.response.text}"
                        )
                        return  # Don't continue if profile creation fails
                
                # Step 2: Set last_matches status to NOT_STARTED
                try:
                    success = await profile_status_service.set_last_matches_status(
                        profile.puuid, "NOT_STARTED"
                    )
                    if not success:
                        logger.warning(
                            f"Failed to set last_matches status for puuid: {profile.puuid}"
                        )
                except Exception as status_error:
                    logger.error(
                        f"Error setting last_matches status: {status_error}"
                    )
                
                # Step 3: Trigger store_last_matches (fire-and-forget)
                try:
                    asyncio.create_task(
                        player_matches_service.store_last_matches(
                            profile.puuid, profile.region
                        )
                    )
                    logger.info(
                        f"Triggered store_last_matches for puuid: {profile.puuid}"
                    )
                except Exception as match_error:
                    logger.error(
                        f"Error triggering store_last_matches: {match_error}"
                    )
                    
        except Exception as e:
            logger.error(
                f"Unexpected error in _save_profile_to_dynamodb: {e}", 
                exc_info=True
            )


profile_service = ProfileService()
