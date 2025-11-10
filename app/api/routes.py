from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas import (
    ChampionSummariesResponse,
    ChatMessage,
    FaultlinesResponse,
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
    TextGenerationRequest,
    TextGenerationResponse,
    VoiceInFogChatRequest,
    VoiceInFogChatResponse,
    VoiceInFogMatchChatRequest,
    VoiceInFogStarterResponse,
)
from app.services import (
    battle_summary_service,
    player_matches_service,
    profile_service,
    signature_playstyle_analyzer,
    store,
)
from app.services.faultlines import faultlines_analyzer
from app.services.text_generation import text_generation_service
from app.services.voice_in_fog import voice_in_fog_service

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


@router.post(
    "/text/generate",
    response_model=TextGenerationResponse,
    tags=["Text Generation"],
)
async def generate_text(request: TextGenerationRequest) -> TextGenerationResponse:
    """
    Generate text using LLM based on context and query.
    
    This is a common service endpoint that can be used by any service
    (battle_summary, signature_playstyle, etc.) to generate contextual
    text narratives, labels, insights, and descriptions.
    
    The service accepts:
    - **context**: Background information and data for the LLM
    - **query**: The specific question or task for the LLM
    - **max_tokens**: Maximum tokens in the response (10-2000)
    - **temperature**: Sampling temperature 0-1 (higher = more creative)
    
    Args:
        request: TextGenerationRequest with context, query, and parameters
        
    Returns:
        TextGenerationResponse with generated text or error message
        
    Example Request:
        {
            "context": "Player stats: KDA 5.89, KP 50%, Damage Share 20%",
            "query": "Generate a playstyle label and one-liner",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
    Example Response:
        {
            "text": "Frontline Anchor - Durable engagements with controlled death pace",
            "status": "success",
            "error": null
        }
    """
    try:
        generated_text = await text_generation_service.generate_text(
            context=request.context,
            query=request.query,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        return TextGenerationResponse(
            text=generated_text,
            status="success",
            error=None,
        )
    except Exception as e:
        return TextGenerationResponse(
            text="",
            status="error",
            error=str(e),
        )


@router.get("/battles/{player_id}/faultlines/summary", response_model=FaultlinesResponse, tags=["Battles"])
async def get_faultlines_summary(player_id: str) -> FaultlinesResponse:
    """
    Faultlines: Strengths and Shadows
    
    Analyze player performance across 8 core competency axes to identify
    top 3 strengths and bottom 3 weaknesses. Each axis includes normalized scores,
    key metrics, trends, telemetry, chart configurations, and AI-generated narratives.
    
    The 8 axes:
    - Combat Efficiency Index (CEI): KDA, Kill Participation, Damage Per Minute
    - Objective Reliability Index (ORI): Dragon/Baron/Turret participation
    - Survival Discipline Index (SDI): Death clustering and damage mitigation
    - Vision & Awareness Index (VAI): Vision score and ward control
    - Economy Utilization Index (EUI): Gold per minute and conversion efficiency
    - Role Stability Index (RSI): Win rate variance across roles
    - Momentum Index (MI): Win/loss streak patterns
    - Composure Index (CI): Performance variance and consistency
    
    Returns:
        FaultlinesResponse with status and data containing:
        - summary: Player/cohort/window labels
        - axes: All 8 axes with scores, metrics, trends, telemetry, charts, and narratives
        - insights: Top 3 actionable insights
    
    Status codes:
        - READY: Analysis complete with match data
        - NOT_STARTED: No profile exists for this player
        - FETCHING: Match data is being collected
        - NO_MATCHES: Profile exists but no matches found
        - FAILED: Error during analysis
    
    Example:
        GET /api/battles/{puuid}/faultlines/summary
    """
    try:
        result = await faultlines_analyzer.analyze(player_id)
        return result
    except Exception as e:
        return FaultlinesResponse(
            status="FAILED",
            data=None,
        )


@router.post(
    "/voice-in-fog/chat",
    response_model=VoiceInFogChatResponse,
    tags=["Voice in the Fog"],
    summary="Chat with Voice in the Fog (no context)"
)
async def voice_chat(request: VoiceInFogChatRequest) -> VoiceInFogChatResponse:
    """
    Chat with Voice in the Fog AI assistant without specific context.
    
    Args:
        request: Chat request with message and optional conversation history
    
    Returns:
        VoiceInFogChatResponse with AI reply
    
    Example:
        POST /api/voice-in-fog/chat
        {
          "message": "What's the meta right now?",
          "conversation_history": [],
          "model": "Claude 3.7 Sonnet"
        }
    """
    try:
        # Build messages list
        messages = []
        if request.conversation_history:
            messages.extend([
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ])
        messages.append({"role": "user", "content": request.message})
        
        result = await voice_in_fog_service.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens or 500,
        )
        
        return VoiceInFogChatResponse(
            modelUsed=result["modelUsed"],
            reply=result["reply"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/voice-in-fog/chat/matches/{player_id}",
    response_model=VoiceInFogChatResponse,
    tags=["Voice in the Fog"],
    summary="Chat about player matches with context"
)
async def voice_chat_with_matches(
    player_id: str,
    request: VoiceInFogChatRequest,
) -> VoiceInFogChatResponse:
    """
    Chat with Voice in the Fog about a player's matches with full context.
    
    Args:
        player_id: Player PUUID
        request: Chat request with message and optional conversation history
    
    Returns:
        VoiceInFogChatResponse with contextual AI reply
    
    Example:
        POST /api/voice-in-fog/chat/matches/{puuid}
        {
          "message": "What's my best champion?",
          "conversation_history": []
        }
    """
    try:
        # Build conversation history
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        # Fetch matches from Lambda
        settings = get_settings()
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.lambda_get_matches_url,
                json={"puuid": player_id},
            )
            response.raise_for_status()
            data = response.json()
            matches = data.get("matches", [])
        
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No matches found for this player"
            )
        
        # Use chat_with_match_context directly
        result = await voice_in_fog_service.chat_with_match_context(
            user_message=request.message,
            matches=matches,
            conversation_history=conversation_history,
            model=request.model,
        )
        
        return VoiceInFogChatResponse(
            modelUsed=result["modelUsed"],
            reply=result["reply"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/voice-in-fog/chat/playstyle/{player_id}",
    response_model=VoiceInFogChatResponse,
    tags=["Voice in the Fog"],
    summary="Chat about playstyle analysis with context"
)
async def voice_chat_with_playstyle(
    player_id: str,
    request: VoiceInFogChatRequest,
) -> VoiceInFogChatResponse:
    """
    Chat with Voice in the Fog about a player's playstyle analysis.
    
    Args:
        player_id: Player PUUID
        request: Chat request with message and optional conversation history
    
    Returns:
        VoiceInFogChatResponse with contextual AI reply about playstyle
    
    Example:
        POST /api/voice-in-fog/chat/playstyle/{puuid}
        {
          "message": "How can I improve my aggression?",
          "conversation_history": []
        }
    """
    try:
        # Get playstyle analysis
        playstyle_response = await signature_playstyle_analyzer.analyze(player_id)
        
        if playstyle_response.status != "READY" or not playstyle_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Playstyle analysis not available: {playstyle_response.status}",
            )
        
        # Build conversation history
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        result = await voice_in_fog_service.chat_with_playstyle_context(
            user_message=request.message,
            playstyle_data=playstyle_response.data.model_dump(),
            conversation_history=conversation_history,
            model=request.model,
        )
        
        return VoiceInFogChatResponse(
            modelUsed=result["modelUsed"],
            reply=result["reply"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/voice-in-fog/chat/faultlines/{player_id}",
    response_model=VoiceInFogChatResponse,
    tags=["Voice in the Fog"],
    summary="Chat about Faultlines analysis with context"
)
async def voice_chat_with_faultlines(
    player_id: str,
    request: VoiceInFogChatRequest,
) -> VoiceInFogChatResponse:
    """
    Chat with Voice in the Fog about a player's Faultlines (strengths/weaknesses).
    
    Args:
        player_id: Player PUUID
        request: Chat request with message and optional conversation history
    
    Returns:
        VoiceInFogChatResponse with contextual AI reply about Faultlines
    
    Example:
        POST /api/voice-in-fog/chat/faultlines/{puuid}
        {
          "message": "Why is my survival discipline low?",
          "conversation_history": []
        }
    """
    try:
        # Get faultlines analysis
        faultlines_response = await faultlines_analyzer.analyze(player_id)
        
        if faultlines_response.status != "READY" or not faultlines_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Faultlines analysis not available: {faultlines_response.status}",
            )
        
        # Build conversation history
        conversation_history = None
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        result = await voice_in_fog_service.chat_with_faultlines_context(
            user_message=request.message,
            faultlines_data=faultlines_response.model_dump(),
            conversation_history=conversation_history,
            model=request.model,
        )
        
        return VoiceInFogChatResponse(
            modelUsed=result["modelUsed"],
            reply=result["reply"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )



# ==================== Dedicated Starter Topic APIs ====================

@router.post(
    "/voice-in-fog/general-chat",
    response_model=VoiceInFogChatResponse,
    tags=["Voice in the Fog"],
    summary="General chat without specific context"
)
async def voice_general_chat(
    request: VoiceInFogChatRequest,
) -> VoiceInFogChatResponse:
    """
    General chat endpoint for broad gameplay questions.
    
    Optional: Provide player_id to fetch match history and get personalized advice.
    """
    try:
        conversation_history = []
        if request.conversation_history:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        conversation_history.append({"role": "user", "content": request.message})
        
        result = await voice_in_fog_service.chat(
            messages=conversation_history,
            context_prompt="You are an AI strategist embedded in LegendScope. Provide clear, actionable League of Legends advice.",
            player_id=request.player_id,  # Pass player_id if provided
            model=request.model,
        )
        
        return VoiceInFogChatResponse(
            modelUsed=result["modelUsed"],
            reply=result["reply"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/voice-in-fog/echoes-of-battle/{player_id}",
    response_model=VoiceInFogStarterResponse,
    tags=["Voice in the Fog"],
    summary="Echoes of Battle - Battle history insights"
)
async def voice_echoes_of_battle(
    player_id: str,
    starter_topic: str,
) -> VoiceInFogStarterResponse:
    """
    Get Echoes of Battle insights for a specific starter topic.
    
    Valid starter topics:
    - "Battles Fought"
    - "Claim / Fall Ratio"
    - "Longest Claim & Fall Streaks"
    - "Clutch Battles"
    - "Role Influence"
    """
    try:
        valid_topics = [
            "Battles Fought",
            "Claim / Fall Ratio",
            "Longest Claim & Fall Streaks",
            "Clutch Battles",
            "Role Influence"
        ]
        
        if starter_topic not in valid_topics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid starter topic. Must be one of: {', '.join(valid_topics)}"
            )
        
        result = await voice_in_fog_service.get_echoes_of_battle_insight(
            player_id=player_id,
            starter_topic=starter_topic,
        )
        
        return VoiceInFogStarterResponse(
            starterTopic=result["starterTopic"],
            insight=result["insight"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/voice-in-fog/patterns-beneath-chaos/{player_id}",
    response_model=VoiceInFogStarterResponse,
    tags=["Voice in the Fog"],
    summary="Patterns Beneath Chaos - Playstyle axis analysis"
)
async def voice_patterns_beneath_chaos(
    player_id: str,
    starter_topic: str,
) -> VoiceInFogStarterResponse:
    """
    Get Patterns Beneath Chaos insights for a specific playstyle axis.
    
    Valid starter topics:
    - "Aggression"
    - "Survivability"
    - "Skirmish Bias"
    - "Objective Impact"
    - "Vision Discipline"
    - "Utility"
    - "Tempo Profile"
    """
    try:
        valid_topics = [
            "Aggression",
            "Survivability",
            "Skirmish Bias",
            "Objective Impact",
            "Vision Discipline",
            "Utility",
            "Tempo Profile"
        ]
        
        if starter_topic not in valid_topics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid starter topic. Must be one of: {', '.join(valid_topics)}"
            )
        
        result = await voice_in_fog_service.get_patterns_beneath_chaos_insight(
            player_id=player_id,
            starter_topic=starter_topic,
        )
        
        return VoiceInFogStarterResponse(
            starterTopic=result["starterTopic"],
            insight=result["insight"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/voice-in-fog/faultlines-analysis/{player_id}",
    response_model=VoiceInFogStarterResponse,
    tags=["Voice in the Fog"],
    summary="Faultlines - Performance index analysis"
)
async def voice_faultlines_analysis(
    player_id: str,
    starter_topic: str,
) -> VoiceInFogStarterResponse:
    """
    Get Faultlines insights for a specific performance index.
    
    Valid starter topics:
    - "Combat Efficiency Index"
    - "Objective Reliability Index"
    - "Survival Discipline Index"
    - "Vision & Awareness Index"
    - "Economy Utilization Index"
    - "Momentum Index"
    - "Composure Index"
    """
    try:
        valid_topics = [
            "Combat Efficiency Index",
            "Objective Reliability Index",
            "Survival Discipline Index",
            "Vision & Awareness Index",
            "Economy Utilization Index",
            "Momentum Index",
            "Composure Index"
        ]
        
        if starter_topic not in valid_topics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid starter topic. Must be one of: {', '.join(valid_topics)}"
            )
        
        result = await voice_in_fog_service.get_faultlines_insight(
            player_id=player_id,
            starter_topic=starter_topic,
        )
        
        return VoiceInFogStarterResponse(
            starterTopic=result["starterTopic"],
            insight=result["insight"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

