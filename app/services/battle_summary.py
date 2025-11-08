from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas import (
    ChampionSummariesResponse,
    ChampionSummaryModel,
    NarrativeSummaryModel,
    NarrativeSummaryResponse,
    ProfileRequest,
    RiskProfileModel,
    RiskProfileResponse,
    RoleSummariesResponse,
    RoleSummaryModel,
    SummaryCardsModel,
    SummaryCardsResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Role mapping
ROLE_MAPPING = {
    "TOP": "Top Lane",
    "JUNGLE": "Jungle",
    "MIDDLE": "Mid Lane",
    "MID": "Mid Lane",
    "BOTTOM": "Bot Lane",
    "UTILITY": "Support",
}

# Champion colors for visualization
CHAMPION_COLORS = [
    "#60a5fa",
    "#8b5cf6",
    "#22d3ee",
    "#f97316",
    "#facc15",
    "#ec4899",
    "#10b981",
    "#f59e0b",
    "#6366f1",
    "#14b8a6",
]


class BattleSummaryService:
    """Service for handling battle summary analytics."""

    async def _get_profile_status(self, puuid: str, region: str = "na1") -> str | None:
        """
        Get the last_matches status from player profile.
        
        Args:
            puuid: Player UUID
            region: Server region (default: na1)
            
        Returns:
            Status string (NOT_STARTED, FETCHING, READY, NO_MATCHES, FAILED) or None
        """
        from app.services.profile import profile_service
        
        try:
            request = ProfileRequest(puuid=puuid, region=region)
            profile = await profile_service.get_profile(request)
            return profile.last_matches
        except Exception as e:
            logger.warning(f"Failed to get profile status for {puuid}: {e}")
            return None

    async def _fetch_matches(self, puuid: str) -> list[dict[str, Any]]:
        """Fetch match data from Lambda API."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    settings.lambda_get_matches_url,
                    json={"puuid": puuid},
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Handle both direct response and wrapped response formats
                if "matches" in data:
                    # Direct format: {"puuid": "...", "count": 20, "matches": [...]}
                    matches = data.get("matches", [])
                elif isinstance(data, dict) and "body" in data:
                    # Wrapped format: {"statusCode": 200, "body": "{...}"}
                    import json
                    body_data = data["body"]
                    body = json.loads(body_data) if isinstance(body_data, str) else body_data
                    matches = body.get("matches", [])
                else:
                    matches = []
                
                logger.info(f"Fetched {len(matches)} matches for puuid: {puuid}")
                return matches
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching matches: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching matches: {e}", exc_info=True)
            return []

    def _format_duration(self, seconds: int) -> str:
        """Format game duration in seconds to 'XXm YYs' format."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"

    def _get_role_display_name(self, team_position: str) -> str:
        """Convert API role to display name."""
        return ROLE_MAPPING.get(team_position, team_position)

    async def get_last_twenty_summary_cards(self, player_id: str) -> SummaryCardsResponse:
        """Get summary cards for last 20 battles."""
        # Check profile status first
        status = await self._get_profile_status(player_id)
        
        if status != "READY":
            # Return response with status and no data
            return SummaryCardsResponse(
                status=status or "UNKNOWN",
                data=None,
            )
        
        matches = await self._fetch_matches(player_id)
        
        if not matches:
            # Return default values if no matches
            data = SummaryCardsModel(
                battlesFought=0,
                claims=0,
                falls=0,
                claimFallRatio=0.0,
                longestClaimStreak=0,
                longestFallStreak=0,
                clutchGames=0,
                surrenderRate=0,
                averageMatchDuration="0m 0s",
            )
            return SummaryCardsResponse(status="READY", data=data)
        
        battles_fought = len(matches)
        claims = sum(1 for m in matches if m.get("win"))
        falls = battles_fought - claims
        ratio = claims if falls == 0 else round(claims / falls, 2)
        
        # Calculate streaks
        longest_claim_streak = 0
        longest_fall_streak = 0
        current_claim_streak = 0
        current_fall_streak = 0
        
        for match in matches:
            if match.get("win"):
                current_claim_streak += 1
                current_fall_streak = 0
                longest_claim_streak = max(longest_claim_streak, current_claim_streak)
            else:
                current_fall_streak += 1
                current_claim_streak = 0
                longest_fall_streak = max(longest_fall_streak, current_fall_streak)
        
        # Calculate clutch games (comeback wins with K/D < 1.0 but still won)
        clutch_games = sum(
            1 for m in matches
            if m.get("win") and (m.get("kills") or 0) < (m.get("deaths") or 1)
        )
        
        # Calculate surrender rate
        surrenders = sum(1 for m in matches if m.get("teamEarlySurrendered", False))
        surrender_rate = round((surrenders / battles_fought) * 100) if battles_fought > 0 else 0
        
        # Calculate average match duration
        total_duration = sum(m.get("gameDuration") or 0 for m in matches)
        avg_duration_seconds = total_duration // battles_fought if battles_fought > 0 else 0
        avg_duration = self._format_duration(avg_duration_seconds)
        
        data = SummaryCardsModel(
            battlesFought=battles_fought,
            claims=claims,
            falls=falls,
            claimFallRatio=ratio,
            longestClaimStreak=longest_claim_streak,
            longestFallStreak=longest_fall_streak,
            clutchGames=clutch_games,
            surrenderRate=surrender_rate,
            averageMatchDuration=avg_duration,
        )
        
        return SummaryCardsResponse(status="READY", data=data)

    async def get_last_twenty_role_summaries(
        self, player_id: str
    ) -> RoleSummariesResponse:
        """Get role performance summaries for last 20 battles."""
        # Check profile status first
        status = await self._get_profile_status(player_id)
        
        if status != "READY":
            return RoleSummariesResponse(
                status=status or "UNKNOWN",
                data=None,
            )
        
        matches = await self._fetch_matches(player_id)
        
        if not matches:
            return RoleSummariesResponse(status="READY", data=[])
        
        # Aggregate data by role
        role_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "games": 0,
                "claims": 0,
                "total_kda": 0.0,
                "first_bloods": 0,
                "total_vision": 0,
                "total_gold_per_min": 0.0,
            }
        )
        
        for match in matches:
            role = self._get_role_display_name(match.get("teamPosition", "Unknown"))
            stats = role_stats[role]
            
            stats["games"] += 1
            stats["claims"] += 1 if match.get("win") else 0
            stats["total_kda"] += match.get("kdaRatio") or 0.0
            stats["first_bloods"] += 1 if match.get("firstBloodKill") else 0
            stats["total_vision"] += match.get("visionScore") or 0
            stats["total_gold_per_min"] += match.get("goldPerMinute") or 0.0
        
        # Calculate averages and create models
        role_summaries = []
        for role, stats in role_stats.items():
            games = stats["games"]
            claims = stats["claims"]
            falls = games - claims
            
            role_summaries.append(
                RoleSummaryModel(
                    role=role,
                    games=games,
                    claims=claims,
                    falls=falls,
                    winRate=round((claims / games) * 100) if games > 0 else 0,
                    averageKda=round(stats["total_kda"] / games, 1) if games > 0 else 0.0,
                    firstBloodRate=round((stats["first_bloods"] / games) * 100) if games > 0 else 0,
                    visionScore=round(stats["total_vision"] / games) if games > 0 else 0,
                    goldPerMinute=round(stats["total_gold_per_min"] / games) if games > 0 else 0,
                )
            )
        
        # Sort by number of games played
        sorted_summaries = sorted(role_summaries, key=lambda r: r.games, reverse=True)
        return RoleSummariesResponse(status="READY", data=sorted_summaries)

    async def get_last_twenty_champion_summaries(
        self, player_id: str
    ) -> ChampionSummariesResponse:
        """Get champion performance summaries for last 20 battles."""
        # Check profile status first
        status = await self._get_profile_status(player_id)
        
        if status != "READY":
            return ChampionSummariesResponse(
                status=status or "UNKNOWN",
                data=None,
            )
        
        matches = await self._fetch_matches(player_id)
        
        if not matches:
            return ChampionSummariesResponse(status="READY", data=[])
        
        # Aggregate data by champion
        champion_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"games": 0, "claims": 0}
        )
        
        for match in matches:
            champion = match.get("championName", "Unknown")
            champion_stats[champion]["games"] += 1
            champion_stats[champion]["claims"] += 1 if match.get("win") else 0
        
        # Create models
        champion_summaries = []
        for idx, (champion, stats) in enumerate(
            sorted(champion_stats.items(), key=lambda x: x[1]["games"], reverse=True)
        ):
            games = stats["games"]
            claims = stats["claims"]
            
            # Limit to top 5 + "Others"
            if idx < 5:
                champion_summaries.append(
                    ChampionSummaryModel(
                        name=champion,
                        games=games,
                        claims=claims,
                        winRate=round((claims / games) * 100) if games > 0 else 0,
                        color=CHAMPION_COLORS[idx % len(CHAMPION_COLORS)],
                    )
                )
            else:
                # Aggregate remaining into "Others"
                if not champion_summaries or champion_summaries[-1].name != "Others":
                    champion_summaries.append(
                        ChampionSummaryModel(
                            name="Others",
                            games=games,
                            claims=claims,
                            winRate=round((claims / games) * 100) if games > 0 else 0,
                            color="#64748b",
                        )
                    )
                else:
                    # Add to existing "Others"
                    others = champion_summaries[-1]
                    new_games = others.games + games
                    new_claims = others.claims + claims
                    champion_summaries[-1] = ChampionSummaryModel(
                        name="Others",
                        games=new_games,
                        claims=new_claims,
                        winRate=round((new_claims / new_games) * 100) if new_games > 0 else 0,
                        color="#64748b",
                    )
        
        return ChampionSummariesResponse(status="READY", data=champion_summaries)

    async def get_last_twenty_risk_profile(self, player_id: str) -> RiskProfileResponse:
        """Get risk profile analysis for last 20 battles."""
        # Check profile status first
        status = await self._get_profile_status(player_id)
        
        if status != "READY":
            return RiskProfileResponse(
                status=status or "UNKNOWN",
                data=None,
            )
        
        matches = await self._fetch_matches(player_id)
        
        if not matches:
            data = RiskProfileModel(
                earlyAggression=0,
                earlyFalls=0,
                objectiveControl=0,
                visionCommitment=0,
                narrative="Insufficient data to generate risk profile.",
            )
            return RiskProfileResponse(status="READY", data=data)
        
        roles_response = await self.get_last_twenty_role_summaries(player_id)
        roles = roles_response.data if roles_response.data else []
        
        # Calculate metrics
        total_matches = len(matches)
        
        # Early aggression: first blood rate
        first_bloods = sum(1 for m in matches if m.get("firstBloodKill"))
        early_aggression = round((first_bloods / total_matches) * 100) if total_matches > 0 else 0
        
        # Early falls: deaths in first 10 minutes (approximation: high early deaths)
        early_deaths = sum(1 for m in matches if (m.get("deaths") or 0) >= 3 and not m.get("win"))
        early_falls = round((early_deaths / total_matches) * 100) if total_matches > 0 else 0
        
        # Objective control: dragon + baron + rift herald kills
        total_objectives = sum(
            (m.get("dragonKills") or 0)
            + (m.get("baronKills") or 0)
            + (m.get("riftHeraldKills") or 0)
            for m in matches
        )
        objective_control = min(100, round((total_objectives / total_matches) * 20))
        
        # Vision commitment: average vision score normalized to 0-100
        total_vision = sum(m.get("visionScore") or 0 for m in matches)
        avg_vision = total_vision / total_matches if total_matches > 0 else 0
        vision_commitment = min(100, round(avg_vision * 1.5))
        
        # Generate narrative
        highest_pressure_role = min(roles, key=lambda r: r.win_rate) if roles else None
        
        aggression_phrase = (
            "You open with decisive strikes"
            if early_aggression >= 60
            else "You approach the opening moments with patience"
        )
        
        vulnerability_phrase = (
            "but early missteps risk surrendering tempo"
            if early_falls >= 40
            else "while keeping early skirmishes largely under control"
        )
        
        strength_phrase = "— vision remains your lasting strength."
        role_phrase = (
            f" Guard your {highest_pressure_role.role.lower()} rotations to protect that edge."
            if highest_pressure_role
            else ""
        )
        
        narrative = f"{aggression_phrase} {vulnerability_phrase} {strength_phrase}{role_phrase}"
        
        data = RiskProfileModel(
            earlyAggression=early_aggression,
            earlyFalls=early_falls,
            objectiveControl=objective_control,
            visionCommitment=vision_commitment,
            narrative=narrative,
        )
        
        return RiskProfileResponse(status="READY", data=data)

    async def get_last_twenty_narrative(
        self, player_id: str
    ) -> NarrativeSummaryResponse:
        """Get narrative summary for last 20 battles."""
        summary_cards_response = await self.get_last_twenty_summary_cards(player_id)
        roles_response = await self.get_last_twenty_role_summaries(player_id)
        champions_response = await self.get_last_twenty_champion_summaries(player_id)
        risk_profile_response = await self.get_last_twenty_risk_profile(player_id)
        
        # Check if data is ready
        if summary_cards_response.status != "READY" or not summary_cards_response.data:
            return NarrativeSummaryResponse(
                status=summary_cards_response.status,
                data=None,
            )
        
        summary_cards = summary_cards_response.data
        roles = roles_response.data if roles_response.data else []
        champions = champions_response.data if champions_response.data else []
        risk_profile = risk_profile_response.data if risk_profile_response.data else None
        
        if not roles or not champions or not risk_profile:
            data = NarrativeSummaryModel(
                headline="Awaiting Battle Data",
                body="Insufficient match history to generate narrative summary.",
            )
            return NarrativeSummaryResponse(status="READY", data=data)

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

        data = NarrativeSummaryModel(headline=headline, body=body)
        return NarrativeSummaryResponse(status="READY", data=data)


battle_summary_service = BattleSummaryService()
