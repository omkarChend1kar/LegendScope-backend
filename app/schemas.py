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
    riot_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Riot ID (e.g., 'Player#NA1')",
    )
    puuid: str | None = Field(
        default=None,
        min_length=1,
        description="Player UUID",
    )
    region: str = Field(
        min_length=2,
        max_length=10,
        description="Region code (e.g., 'na1', 'euw1', 'kr')",
    )


class ProfileResponse(BaseModel):
    """Player profile response with all data from Lambda/DynamoDB."""
    riot_id: str = Field(alias="riotId")
    puuid: str
    summoner_name: str = Field(alias="summonerName")
    tag_line: str = Field(alias="tagLine")
    region: str
    created_at: int = Field(alias="createdAt")
    updated_at: int = Field(alias="updatedAt")
    last_matches: str | None = Field(
        default=None,
        alias="lastMatches",
        description="Status of last matches: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED",
    )
    
    class Config:
        populate_by_name = True


class SummaryCardsModel(BaseModel):
    """Summary statistics for last 20 battles."""
    battles_fought: int = Field(alias="battlesFought")
    claims: int
    falls: int
    claim_fall_ratio: float = Field(alias="claimFallRatio")
    longest_claim_streak: int = Field(alias="longestClaimStreak")
    longest_fall_streak: int = Field(alias="longestFallStreak")
    clutch_games: int = Field(alias="clutchGames")
    surrender_rate: int = Field(alias="surrenderRate")
    average_match_duration: str = Field(alias="averageMatchDuration")
    
    class Config:
        populate_by_name = True


class RoleSummaryModel(BaseModel):
    """Performance summary for a specific role."""
    role: str
    games: int
    claims: int
    falls: int
    win_rate: int = Field(alias="winRate")
    average_kda: float = Field(alias="averageKda")
    first_blood_rate: int = Field(alias="firstBloodRate")
    vision_score: int = Field(alias="visionScore")
    gold_per_minute: int = Field(alias="goldPerMinute")
    
    class Config:
        populate_by_name = True


class ChampionSummaryModel(BaseModel):
    """Performance summary for a specific champion."""
    name: str
    games: int
    claims: int
    win_rate: int = Field(alias="winRate")
    color: str
    
    class Config:
        populate_by_name = True


class RiskProfileModel(BaseModel):
    """Risk profile analysis for last 20 battles."""
    early_aggression: int = Field(alias="earlyAggression")
    early_falls: int = Field(alias="earlyFalls")
    objective_control: int = Field(alias="objectiveControl")
    vision_commitment: int = Field(alias="visionCommitment")
    narrative: str
    
    class Config:
        populate_by_name = True


class NarrativeSummaryModel(BaseModel):
    """Narrative summary of player performance."""
    headline: str
    body: str


class StoreMatchesRequest(BaseModel):
    """Request to store player matches data."""
    puuid: str
    region: str = "na1"


class StoreMatchesResponse(BaseModel):
    """Response for match storage."""
    status: str
    message: str


# Battle Summary Response Wrappers with Status
class SummaryCardsResponse(BaseModel):
    """Response wrapper for summary cards with status."""
    status: str = Field(
        description="Match data status: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED"
    )
    data: SummaryCardsModel | None = Field(
        default=None,
        description="Summary cards data, null if status is not READY"
    )
    
    class Config:
        populate_by_name = True


class RoleSummariesResponse(BaseModel):
    """Response wrapper for role summaries with status."""
    status: str = Field(
        description="Match data status: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED"
    )
    data: list[RoleSummaryModel] | None = Field(
        default=None,
        description="Role summaries data, null if status is not READY"
    )
    
    class Config:
        populate_by_name = True


class ChampionSummariesResponse(BaseModel):
    """Response wrapper for champion summaries with status."""
    status: str = Field(
        description="Match data status: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED"
    )
    data: list[ChampionSummaryModel] | None = Field(
        default=None,
        description="Champion summaries data, null if status is not READY"
    )
    
    class Config:
        populate_by_name = True


class RiskProfileResponse(BaseModel):
    """Response wrapper for risk profile with status."""
    status: str = Field(
        description="Match data status: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED"
    )
    data: RiskProfileModel | None = Field(
        default=None,
        description="Risk profile data, null if status is not READY"
    )
    
    class Config:
        populate_by_name = True


class NarrativeSummaryResponse(BaseModel):
    """Response wrapper for narrative summary with status."""
    status: str = Field(
        description="Match data status: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED"
    )
    data: NarrativeSummaryModel | None = Field(
        default=None,
        description="Narrative summary data, null if status is not READY"
    )
    
    class Config:
        populate_by_name = True

