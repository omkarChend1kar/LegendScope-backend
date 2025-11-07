from datetime import datetime

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(gt=0)


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    created_at: datetime


class ProfileRequest(BaseModel):
    riot_id: str = Field(min_length=3, max_length=50, description="Riot ID (e.g., 'Player#NA1')")
    region: str = Field(
        min_length=2,
        max_length=10,
        description="Region code (e.g., 'na1', 'euw1', 'kr')",
    )


class ProfileResponse(BaseModel):
    riot_id: str
    region: str
    summoner_name: str
    level: int
    profile_icon_id: int
    message: str = "Profile retrieved successfully"


class LambdaProfileResponse(BaseModel):
    """Response from Lambda/DynamoDB with stored profile data."""
    puuid: str
    summoner_name: str = Field(alias="summonerName")
    tag_line: str = Field(alias="tagLine")
    region: str
    created_at: int = Field(alias="createdAt")
    updated_at: int = Field(alias="updatedAt")
    
    class Config:
        populate_by_name = True

