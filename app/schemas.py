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


# ============================================================================
# Signature Playstyle Analysis Models
# ============================================================================

class AxisMetricModel(BaseModel):
    """Individual metric within a playstyle axis."""
    id: str = Field(description="Unique identifier for the metric")
    label: str = Field(description="Display label")
    unit: str | None = Field(default=None, description="Unit of measurement")
    value: float = Field(description="Raw metric value")
    display_value: str = Field(alias="displayValue", description="Formatted display value")
    direction: str = Field(description="positive, negative, or neutral")
    percent: int = Field(description="Percentile score 0-100")
    
    class Config:
        populate_by_name = True


class PlaystyleAxisModel(BaseModel):
    """A single playstyle axis with score and metrics."""
    key: str = Field(description="Axis identifier")
    label: str = Field(description="Display label")
    score: int = Field(description="Overall axis score 0-100")
    score_label: str = Field(alias="scoreLabel", description="Score interpretation label")
    metrics: list[AxisMetricModel] = Field(description="Individual metrics")
    evidence: dict[str, float] = Field(description="Raw evidence values")
    
    class Config:
        populate_by_name = True


class PlaystyleAxesModel(BaseModel):
    """All six playstyle axes."""
    aggression: PlaystyleAxisModel
    survivability: PlaystyleAxisModel
    skirmish_bias: PlaystyleAxisModel = Field(alias="skirmishBias")
    objective_impact: PlaystyleAxisModel = Field(alias="objectiveImpact")
    vision_discipline: PlaystyleAxisModel = Field(alias="visionDiscipline")
    utility: PlaystyleAxisModel
    
    class Config:
        populate_by_name = True


class EfficiencyModel(BaseModel):
    """Overall efficiency metrics."""
    kda: float = Field(description="Kill/Death/Assist ratio")
    kp: float = Field(description="Kill participation 0-1")
    damage_share: float = Field(alias="damageShare", description="Team damage share 0-1")
    gpm: int = Field(description="Gold per minute")
    vision_per_min: float = Field(alias="visionPerMin", description="Vision score per minute")
    
    class Config:
        populate_by_name = True


class TempoPhaseMetricModel(BaseModel):
    """Individual metric within a tempo phase."""
    id: str = Field(description="Metric identifier")
    label: str = Field(description="Display label")
    unit: str | None = Field(default=None, description="Unit of measurement")
    value: float = Field(description="Raw value")
    formatted_value: str = Field(alias="formattedValue", description="Formatted display")
    percent: int = Field(description="Relative strength 0-100")
    direction: str = Field(description="positive or negative")
    
    class Config:
        populate_by_name = True


class TempoPhaseModel(BaseModel):
    """Performance metrics for a game phase."""
    key: str = Field(description="Phase key: early, mid, or late")
    label: str = Field(description="Phase display label")
    role_label: str = Field(alias="roleLabel", description="Role interpretation")
    kills_per_10m: float = Field(alias="killsPer10m")
    deaths_per_10m: float = Field(alias="deathsPer10m")
    dpm: float = Field(description="Damage per minute")
    cs_per_min: float = Field(alias="csPerMin")
    kp: float = Field(description="Kill participation")
    metrics: list[TempoPhaseMetricModel] = Field(description="Phase metrics")
    
    class Config:
        populate_by_name = True


class TempoHighlightModel(BaseModel):
    """A highlighted tempo insight."""
    id: str = Field(description="Highlight identifier")
    title: str = Field(description="Highlight title")
    phase_label: str = Field(alias="phaseLabel", description="Game phase")
    metric_label: str = Field(alias="metricLabel", description="Metric display")
    description: str = Field(description="Insight description")
    
    class Config:
        populate_by_name = True


class TempoModel(BaseModel):
    """Game tempo analysis across phases."""
    best_phase: str = Field(alias="bestPhase", description="Early, Mid, or Late")
    by_phase: dict[str, TempoPhaseModel] = Field(alias="byPhase", description="Phase breakdown")
    highlights: list[TempoHighlightModel] = Field(description="Key tempo insights")
    
    class Config:
        populate_by_name = True


class ConsistencyModel(BaseModel):
    """Consistency analysis across metrics."""
    kda_cv: float = Field(alias="kdaCV", description="KDA coefficient of variation")
    dpm_cv: float = Field(alias="dpmCV", description="DPM coefficient of variation")
    kp_cv: float = Field(alias="kpCV", description="KP coefficient of variation")
    cs_cv: float = Field(alias="csCV", description="CS coefficient of variation")
    vision_cv: float = Field(alias="visionCV", description="Vision coefficient of variation")
    label: str = Field(description="Stable, Streaky, or Volatile")
    
    class Config:
        populate_by_name = True


class ChampionComfortAxesDeltaModel(BaseModel):
    """Axis score deltas for a champion compared to overall."""
    aggression: int | None = None
    survivability: int | None = None
    skirmish_bias: int | None = Field(default=None, alias="skirmishBias")
    objective_impact: int | None = Field(default=None, alias="objectiveImpact")
    vision_discipline: int | None = Field(default=None, alias="visionDiscipline")
    utility: int | None = None
    
    class Config:
        populate_by_name = True


class ChampionComfortModel(BaseModel):
    """Champion comfort pick analysis."""
    champion: str = Field(description="Champion name")
    games: int = Field(description="Games played")
    wr: int = Field(description="Win rate percentage")
    kda: float = Field(description="Average KDA")
    axes_delta: ChampionComfortAxesDeltaModel = Field(
        alias="axesDelta",
        description="Axis differences from overall playstyle"
    )
    
    class Config:
        populate_by_name = True


class ChampPoolModel(BaseModel):
    """Champion pool diversity."""
    unique: int = Field(description="Number of unique champions")
    entropy: float = Field(description="Pool diversity score 0-1")
    
    class Config:
        populate_by_name = True


class RoleAndChampsModel(BaseModel):
    """Role distribution and champion comfort."""
    role_mix: dict[str, int] = Field(alias="roleMix", description="Role percentages")
    champ_pool: ChampPoolModel = Field(alias="champPool", description="Champion pool stats")
    comfort_picks: list[ChampionComfortModel] = Field(
        alias="comfortPicks",
        description="Top comfort champions"
    )
    
    class Config:
        populate_by_name = True


class RecordModel(BaseModel):
    """Win/loss record."""
    games: int
    wins: int
    losses: int
    
    class Config:
        populate_by_name = True


class PlaystyleSummaryHeaderModel(BaseModel):
    """Summary header with playstyle label and record."""
    primary_role: str = Field(alias="primaryRole", description="Most played role")
    playstyle_label: str = Field(alias="playstyleLabel", description="Playstyle archetype")
    one_liner: str = Field(alias="oneLiner", description="One-line summary")
    record: RecordModel = Field(description="Win/loss record")
    window_label: str = Field(alias="windowLabel", description="Time window description")
    
    class Config:
        populate_by_name = True


class PlaystyleSummaryModel(BaseModel):
    """Complete signature playstyle analysis."""
    summary: PlaystyleSummaryHeaderModel = Field(description="Header summary")
    axes: PlaystyleAxesModel = Field(description="Six playstyle axes")
    efficiency: EfficiencyModel = Field(description="Efficiency metrics")
    tempo: TempoModel = Field(description="Tempo analysis")
    consistency: ConsistencyModel = Field(description="Consistency analysis")
    role_and_champs: RoleAndChampsModel = Field(
        alias="roleAndChamps",
        description="Role and champion analysis"
    )
    insights: list[str] = Field(description="Key insights")
    generated_at: str = Field(alias="generatedAt", description="ISO timestamp")
    
    class Config:
        populate_by_name = True


class PlaystyleSummaryResponse(BaseModel):
    """Response wrapper for playstyle summary with status."""
    status: str = Field(
        description="Match data status: NOT_STARTED, FETCHING, READY, NO_MATCHES, or FAILED"
    )
    data: PlaystyleSummaryModel | None = Field(
        default=None,
        description="Playstyle summary data, null if status is not READY"
    )
    
    class Config:
        populate_by_name = True

