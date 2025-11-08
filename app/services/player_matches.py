from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.schemas import StoreMatchesResponse
from app.services.profile_status import profile_status_service

logger = logging.getLogger(__name__)


class PlayerMatchesService:
    """Service for handling player matches data creation."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def store_last_matches(self, puuid: str, region: str = "na1") -> StoreMatchesResponse:
        """
        Store PlayersLastMatches data for a player by fetching from Lambda.
        
        Args:
            puuid: Player's unique identifier
            region: Player's region (default: na1)
            
        Returns:
            StoreMatchesResponse with status and message
        """
        logger.info(f"Fetching last 20 matches for puuid: {puuid}, region: {region}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Step 1: Update profile status to FETCHING
                await profile_status_service.set_last_matches_status(puuid, "FETCHING")
                
                # Step 2: Fetch matches from the Lambda
                payload = {
                    "puuid": puuid,
                    "region": region,
                }
                
                response = await client.post(
                    self.settings.lambda_last_matches_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                
                matches = data.get("matches", [])
                matches_count = data.get("matchesFetched", 0)
                time_taken = data.get("timeTakenSec", 0)
                
                logger.info(
                    f"Successfully fetched {matches_count} matches for puuid: {puuid} "
                    f"in {time_taken} seconds"
                )
                
                # Step 3: Handle case when no matches found
                if not matches:
                    await profile_status_service.set_last_matches_status(
                        puuid, "NO_MATCHES"
                    )
                    logger.warning(f"No matches found for puuid: {puuid}")
                    return StoreMatchesResponse(
                        status="success",
                        message=f"No matches found for puuid: {puuid}",
                    )
                
                # Step 4: Store the fetched matches to DynamoDB via store Lambda
                try:
                    store_payload = {
                        "matches": matches,
                        "puuid": puuid,
                        "table": "last20"
                    }
                    
                    store_response = await client.post(
                        self.settings.lambda_store_matches_url,
                        json=store_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=60.0,
                    )
                    store_response.raise_for_status()
                    
                    logger.info(
                        f"Successfully stored {matches_count} matches to DynamoDB "
                        f"for puuid: {puuid}"
                    )
                    
                    # Step 5: Update profile status to READY
                    await profile_status_service.set_last_matches_status(puuid, "READY")
                    
                    return StoreMatchesResponse(
                        status="success",
                        message=(
                            f"Successfully stored {matches_count} matches "
                            f"for puuid: {puuid}"
                        ),
                    )
                    
                except httpx.HTTPStatusError as store_error:
                    # Store failed, update status to FAILED
                    await profile_status_service.set_last_matches_status(puuid, "FAILED")
                    error_detail = store_error.response.text
                    logger.error(
                        f"Failed to store matches: HTTP {store_error.response.status_code}\n"
                        f"Response: {error_detail}"
                    )
                    return StoreMatchesResponse(
                        status="error",
                        message=(
                            f"Failed to store matches: "
                            f"HTTP {store_error.response.status_code}. "
                            f"Error: {error_detail}"
                        ),
                    )
                
        except httpx.HTTPStatusError as e:
            # Fetch failed, update status to FAILED
            await profile_status_service.set_last_matches_status(puuid, "FAILED")
            error_detail = e.response.text
            logger.error(
                f"HTTP error fetching matches: {e}\n"
                f"Status Code: {e.response.status_code}\n"
                f"Response Body: {error_detail}"
            )
            return StoreMatchesResponse(
                status="error",
                message=(
                    f"Failed to fetch matches: HTTP {e.response.status_code}. "
                    f"Error: {error_detail}"
                ),
            )
        except Exception as e:
            # Unexpected error, update status to FAILED
            await profile_status_service.set_last_matches_status(puuid, "FAILED")
            logger.error(f"Unexpected error in store_last_matches: {e}")
            return StoreMatchesResponse(
                status="error",
                message=f"Failed to process matches: {str(e)}",
            )

    async def store_all_matches(self, puuid: str, region: str = "na1") -> StoreMatchesResponse:
        """
        Store PlayersAllMatches data for a player.
        
        Args:
            puuid: Player's unique identifier
            region: Player's region (default: na1)
            
        Returns:
            StoreMatchesResponse with status and message
        """
        logger.info(f"Storing all matches data for puuid: {puuid}, region: {region}")
        
        # TODO: Implement actual logic to fetch all matches
        # This would follow similar pattern to store_last_matches:
        # 1. Call a Lambda to fetch ALL matches (not just last 20)
        # 2. Store them using lambda_store_matches_url with table="all"
        
        return StoreMatchesResponse(
            status="error",
            message=(
                "store_all_matches not yet implemented. "
                "Use /matches/last for last 20 matches."
            ),
        )


player_matches_service = PlayerMatchesService()
