from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas import (
    ChampionSummariesResponse,
    Item,
    ItemCreate,
    NarrativeSummaryResponse,
    PlaystyleSummaryResponse,
    ProfileRequest,
    ProfileResponse,
    RiskProfileResponse,
    RoleSummariesResponse,
    StoreMatchesRequest,
    StoreMatchesResponse,
    SummaryCardsResponse,
)
from app.services import (
    battle_summary_service,
    player_matches_service,
    profile_service,
    signature_playstyle_analyzer,
    store,
)

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "project": settings.project_name,
    }


@router.get("/items", response_model=list[Item], tags=["Items"])
def list_items() -> list[Item]:
    return list(store.list_items())


@router.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item_in: ItemCreate) -> Item:
    return store.create_item(item_in)


@router.get("/items/{item_id}", response_model=Item, tags=["Items"])
def get_item(item_id: int) -> Item:
    item = store.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Items"])
def delete_item(item_id: int) -> None:
    deleted = store.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@router.post("/profile", response_model=ProfileResponse, tags=["Profile"])
async def get_profile(request: ProfileRequest) -> ProfileResponse:
    """
    Get player profile by Riot ID or PUUID and region.
    
    Flow:
    1. Queries Lambda function which checks DynamoDB for cached profile
    2. If found (200), returns the cached data (includes last_matches status)
    3. If not found (404):
       - Calls get-uuid API to fetch profile data (requires riot_id)
       - Saves to DynamoDB asynchronously (fire-and-forget)
       - Returns profile information
    
    Args:
        request: ProfileRequest containing:
            - riot_id: (Optional) Player's Riot ID (e.g., 'cant type#1998')
            - puuid: (Optional) Player's UUID (at least one of riot_id or puuid required)
            - region: Server region (e.g., 'na1', 'euw1', 'kr')
    
    Returns:
        ProfileResponse with player profile information including last_matches status
        
    Example:
        POST /api/profile
        {
            "riot_id": "cant type#1998",
            "region": "na1"
        }
        
        OR
        
        {
            "puuid": "PcymtY31rEewJXMEZRv4HpbAVTPNMR3PRN9ANAUFc8iPo8GB9UKo4iIv...",
            "region": "na1"
        }
    """
    return await profile_service.get_profile(request)


@router.get(
    "/battles/{player_id}/summary/last-20/cards",
    response_model=SummaryCardsResponse,
    tags=["Battle Summary"],
)
async def get_last_twenty_summary_cards(player_id: str) -> SummaryCardsResponse:
    """
    Get summary statistics cards for last 20 battles.
    
    Returns overview statistics including battles fought, claims, falls,
    claim/fall ratio, streaks, clutch games, and average match duration.
    
    Note: This endpoint checks the player's profile status first. If the
    last_matches status is not "READY", it returns null data with the status.
    Valid statuses: NOT_STARTED, FETCHING, READY, NO_MATCHES, FAILED.
    
    Args:
        player_id: Player's PUUID
        
    Returns:
        SummaryCardsResponse with status and data (null if not READY)
    """
    return await battle_summary_service.get_last_twenty_summary_cards(player_id)


@router.get(
    "/battles/{player_id}/summary/last-20/roles",
    response_model=RoleSummariesResponse,
    tags=["Battle Summary"],
)
async def get_last_twenty_role_summaries(player_id: str) -> RoleSummariesResponse:
    """
    Get role performance summaries for last 20 battles.
    
    Returns performance statistics for each role including games played,
    win rate, KDA, first blood rate, vision score, and gold per minute.
    
    Note: Returns null data with status if last_matches status is not "READY".
    
    Args:
        player_id: Player's PUUID
        
    Returns:
        RoleSummariesResponse with status and data (null if not READY)
    """
    return await battle_summary_service.get_last_twenty_role_summaries(player_id)


@router.get(
    "/battles/{player_id}/summary/last-20/champions",
    response_model=ChampionSummariesResponse,
    tags=["Battle Summary"],
)
async def get_last_twenty_champion_summaries(player_id: str) -> ChampionSummariesResponse:
    """
    Get champion performance summaries for last 20 battles.
    
    Returns statistics for most played champions including games played,
    claims, and win rate.
    
    Note: Returns null data with status if last_matches status is not "READY".
    
    Args:
        player_id: Player's PUUID
        
    Returns:
        ChampionSummariesResponse with status and data (null if not READY)
    """
    return await battle_summary_service.get_last_twenty_champion_summaries(player_id)


@router.get(
    "/battles/{player_id}/summary/last-20/risk-profile",
    response_model=RiskProfileResponse,
    tags=["Battle Summary"],
)
async def get_last_twenty_risk_profile(player_id: str) -> RiskProfileResponse:
    """
    Get risk profile analysis for last 20 battles.
    
    Returns analysis of player's aggression, early falls, objective control,
    vision commitment, and a narrative summary of their playstyle.
    
    Note: Returns null data with status if last_matches status is not "READY".
    
    Args:
        player_id: Player's PUUID
        
    Returns:
        RiskProfileResponse with status and data (null if not READY)
    """
    return await battle_summary_service.get_last_twenty_risk_profile(player_id)


@router.get(
    "/battles/{player_id}/summary/last-20/narrative",
    response_model=NarrativeSummaryResponse,
    tags=["Battle Summary"],
)
async def get_last_twenty_narrative(player_id: str) -> NarrativeSummaryResponse:
    """
    Get narrative summary for last 20 battles.
    
    Returns a personalized narrative summary with headline and body text
    describing the player's overall performance and playstyle.
    
    Note: Returns null data with status if last_matches status is not "READY".
    
    Args:
        player_id: Player's PUUID
        
    Returns:
        NarrativeSummaryResponse with status and data (null if not READY)
    """
    return await battle_summary_service.get_last_twenty_narrative(player_id)


@router.post(
    "/matches/last",
    response_model=StoreMatchesResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Player Matches"],
)
async def create_players_last_matches(request: StoreMatchesRequest) -> StoreMatchesResponse:
    """
    Store PlayersLastMatches data for a player by fetching from Lambda.
    
    This endpoint fetches the last 20 matches for a player from the external
    Lambda function using the player's PUUID and region.
    
    Args:
        request: StoreMatchesRequest containing the player's puuid and region (default: na1)
        
    Returns:
        StoreMatchesResponse with status "stored" and number of matches fetched
    """
    return await player_matches_service.store_last_matches(request.puuid, request.region)


@router.post(
    "/matches/all",
    response_model=StoreMatchesResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Player Matches"],
)
async def create_players_all_matches(request: StoreMatchesRequest) -> StoreMatchesResponse:
    """
    Store PlayersAllMatches data for a player.
    
    This endpoint stores all matches data for a player identified by their PUUID.
    Currently not fully implemented.
    
    Args:
        request: StoreMatchesRequest containing the player's puuid and region (default: na1)
        
    Returns:
        StoreMatchesResponse with status "stored" and success message
    """
    return await player_matches_service.store_all_matches(request.puuid, request.region)


@router.get(
    "/battles/{player_id}/signature-playstyle/summary",
    response_model=PlaystyleSummaryResponse,
    tags=["Signature Playstyle"],
)
async def get_signature_playstyle_summary(player_id: str) -> PlaystyleSummaryResponse:
    """
    Get comprehensive signature playstyle analysis for a player.
    
    Analyzes the player's last 20 matches to generate a detailed playstyle profile
    including six axes (aggression, survivability, skirmish bias, objective impact,
    vision discipline, and utility), efficiency metrics, tempo analysis across game
    phases, consistency metrics, role distribution, and champion comfort picks.
    
    The analysis provides:
    - **Playstyle Axes**: Six dimensional analysis with scores 0-100
    - **Efficiency**: KDA, kill participation, damage share, GPM, vision
    - **Tempo**: Performance breakdown by early/mid/late game phases
    - **Consistency**: Coefficient of variation across key metrics
    - **Role & Champions**: Role distribution and top comfort picks
    - **Insights**: Actionable recommendations based on the analysis
    
    Note: Returns null data with status if last_matches status is not "READY".
    Valid statuses: NOT_STARTED, FETCHING, READY, NO_MATCHES, FAILED.
    
    Args:
        player_id: Player's PUUID
        
    Returns:
        PlaystyleSummaryResponse with status and comprehensive playstyle data
        
    Example Response:
        {
            "status": "READY",
            "data": {
                "summary": {
                    "primaryRole": "JUNGLE",
                    "playstyleLabel": "Aggressive Striker",
                    "oneLiner": "High aggression playstyle (71% KP, 23% DMG share)",
                    "record": {"games": 20, "wins": 12, "losses": 8},
                    "windowLabel": "Last 20 battles"
                },
                "axes": { ... },
                "efficiency": { ... },
                "tempo": { ... },
                "consistency": { ... },
                "roleAndChamps": { ... },
                "insights": [ ... ]
            }
        }
    """
    return await signature_playstyle_analyzer.analyze(player_id)

