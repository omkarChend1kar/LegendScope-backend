from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ProfileStatusService:
    """Service for updating player profile status columns in DynamoDB."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def update_status(
        self,
        puuid: str,
        column_name: str,
        column_value: str,
    ) -> bool:
        """
        Update a specific status column in player_profile table.
        
        Args:
            puuid: Player's unique identifier
            column_name: Name of the column to update (e.g., "last_matches")
            column_value: Value to set (e.g., "NOT_STARTED", "FETCHING", "READY")
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            payload = {
                "puuid": puuid,
                "columnName": column_name,
                "columnValue": column_value,
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.settings.lambda_update_profile_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                
                logger.info(
                    f"Updated {column_name} to {column_value} for puuid: {puuid}"
                )
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error updating {column_name} for puuid {puuid}: {e}\n"
                f"Status Code: {e.response.status_code}\n"
                f"Response: {e.response.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Error updating {column_name} for puuid {puuid}: {e}")
            return False

    async def set_last_matches_status(
        self,
        puuid: str,
        status: str,
    ) -> bool:
        """
        Update the last_matches status column.
        
        Args:
            puuid: Player's unique identifier
            status: Status value ("NOT_STARTED", "FETCHING", "READY", "ERROR")
            
        Returns:
            True if update was successful, False otherwise
        """
        return await self.update_status(puuid, "last_matches", status)


profile_status_service = ProfileStatusService()
