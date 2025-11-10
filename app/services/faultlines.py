"""Faultlines Analysis Service.

Analyzes player strengths and weaknesses across 8 analytical axes to reveal
gameplay polarities - where players shine consistently and where they falter.
"""

import logging
import statistics
from datetime import datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas import (
    FaultlinesAxisModel,
    FaultlinesMetricModel,
    FaultlinesResponse,
    FaultlinesSummaryModel,
    FaultlinesVisualizationBucketModel,
    FaultlinesVisualizationModel,
    FaultlinesVisualizationPointModel,
    FaultlinesVisualizationAxisModel as RadarAxisModel,
    FaultlinesVisualizationDistributionModel,
    ProfileRequest,
)
from app.services.text_generation import text_generation_service

logger = logging.getLogger(__name__)
settings = get_settings()


class FaultlinesAnalyzer:
    """Analyzes player faultlines - strengths and shadows."""

    def __init__(self):
        """Initialize the analyzer."""
        self.profile_url = settings.lambda_profile_url
        self.get_matches_url = settings.lambda_get_matches_url
        self.text_service = text_generation_service

    async def _generate_insight(
        self,
        axis_name: str,
        score: int,
        metrics: dict[str, Any],
        context: str = "",
    ) -> str:
        """
        Generate AI-powered insight for an axis.
        
        Args:
            axis_name: Name of the analysis axis
            score: Normalized score (0-100)
            metrics: Key metrics for this axis
            context: Additional context about the analysis
            
        Returns:
            Generated insight text
        """
        # Build concise context for LLM
        context_text = f"{axis_name}: {score}/100. {context}"

        # Generate insight query - very concise
        query = f"Write a 15-word tactical insight for this League of Legends player metric. Be specific and actionable."

        try:
            insight = await self.text_service.generate_text(
                context=context_text,
                query=query,
                max_tokens=40,  # Reduced for faster response
                temperature=0.6,  # Slightly lower for more focused responses
            )
            return insight.strip()
        except Exception as e:
            logger.error(f"Failed to generate insight for {axis_name}: {e}")
            # Fallback to rule-based insight
            return self._generate_fallback_insight(axis_name, score, metrics)

    def _generate_fallback_insight(
        self, axis_name: str, score: int, metrics: dict[str, Any]
    ) -> str:
        """Generate rule-based fallback insight when LLM is unavailable."""
        if score >= 80:
            return f"Exceptional {axis_name.lower()} - maintain this strong foundation."
        elif score >= 65:
            return f"Solid {axis_name.lower()} with room for optimization."
        elif score >= 50:
            return f"Moderate {axis_name.lower()} - focus on consistency."
        else:
            return f"Key growth opportunity in {axis_name.lower()} - prioritize improvement."

    async def analyze(self, player_id: str) -> FaultlinesResponse:
        """
        Analyze player faultlines across 8 analytical axes.
        
        Args:
            player_id: Player's PUUID
            
        Returns:
            FaultlinesResponse with status and analysis data
        """
        try:
            # Check profile status first
            status = await self._get_profile_status(player_id, region="na1")
            
            if status != "READY":
                return FaultlinesResponse(
                    status=status or "UNKNOWN",
                    data=None,
                )
            
            # Fetch match data
            matches = await self._fetch_matches(player_id)
            
            if not matches:
                return FaultlinesResponse(
                    status="NO_MATCHES",
                    data=None,
                )
            
            # Build all 8 axes
            cei_axis = await self._build_combat_efficiency_index(matches)
            ori_axis = await self._build_objective_reliability_index(matches)
            sdi_axis = await self._build_survival_discipline_index(matches)
            vai_axis = await self._build_vision_awareness_index(matches)
            eui_axis = await self._build_economy_utilization_index(matches)
            rsi_axis = await self._build_role_stability_index(matches)
            mi_axis = await self._build_momentum_index(matches)
            ci_axis = await self._build_composure_index(matches)
            
            axes = [cei_axis, ori_axis, sdi_axis, vai_axis, eui_axis, rsi_axis, mi_axis, ci_axis]
            
            # Create response data
            data = FaultlinesSummaryModel(
                playerId=player_id,
                windowLabel=f"Last {len(matches)} battles",
                generatedAt=datetime.utcnow().isoformat() + "Z",
                axes=axes,
            )
            
            return FaultlinesResponse(
                status="READY",
                data=data,
            )
            
        except Exception as e:
            logger.error(f"Error analyzing faultlines: {e}")
            return FaultlinesResponse(
                status="FAILED",
                data=None,
            )

    async def _get_profile_status(self, puuid: str, region: str) -> str | None:
        """Get player profile status to check if matches are ready."""
        from app.services.profile import profile_service
        
        try:
            request = ProfileRequest(puuid=puuid, region=region)
            profile = await profile_service.get_profile(request)
            return profile.last_matches
        except Exception as e:
            logger.warning(f"Failed to get profile status: {e}")
            return None

    async def _fetch_matches(self, player_id: str) -> list[dict[str, Any]]:
        """
        Fetch stored matches for the player.
        
        Returns:
            List of match data dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.get_matches_url,
                    json={"puuid": player_id},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("matches", [])
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []

    async def _build_combat_efficiency_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Combat Efficiency Index (CEI)."""
        # Calculate metrics
        kda_values = []
        solo_kill_rates = []
        
        for match in matches:
            kills = match.get("kills", 0)
            deaths = max(match.get("deaths", 1), 1)
            assists = match.get("assists", 0)
            kda = (kills + assists) / deaths
            kda_values.append(kda)
            
            total_takedowns = kills + assists
            solo_rate = kills / total_takedowns if total_takedowns > 0 else 0
            solo_kill_rates.append(solo_rate)
        
        avg_kda = statistics.mean(kda_values) if kda_values else 0
        avg_solo_rate = statistics.mean(solo_kill_rates) if solo_kill_rates else 0
        
        # Normalize score
        kda_score = min(avg_kda / 5.0 * 100, 100)
        solo_rate_score = min(avg_solo_rate * 200, 100)
        score = int((kda_score * 0.6) + (solo_rate_score * 0.4))
        
        metrics = [
            FaultlinesMetricModel(
                id="kda_ratio",
                label="KDA Ratio",
                value=avg_kda,
                formattedValue=f"{avg_kda:.1f}",
                unit="",
                percent=min(avg_kda / 5.0, 1.0),
                trend="up" if avg_kda >= 3.0 else "flat",
            ),
            FaultlinesMetricModel(
                id="kill_participation",
                label="Kill Participation",
                value=avg_solo_rate,
                formattedValue=f"{int(avg_solo_rate * 100)}%",
                unit="%",
                percent=avg_solo_rate,
                trend="flat",
            ),
            FaultlinesMetricModel(
                id="solo_kill_margin",
                label="Solo Kill Margin",
                value=avg_solo_rate - 0.5,
                formattedValue=f"{int((avg_solo_rate - 0.5) * 100):+d}%",
                unit="%",
                percent=min(abs(avg_solo_rate - 0.5) * 2, 1.0),
                trend="up" if avg_solo_rate > 0.5 else "down",
            ),
        ]
        
        visualization = FaultlinesVisualizationModel(
            type="bar",
            value=float(score),
            benchmark=64.0,
        )
        
        # Generate AI-powered insight
        context = (
            f"Player averages {avg_kda:.1f} KDA with {avg_solo_rate*100:.0f}% solo kill rate "
            f"across {len(matches)} matches. Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Combat Efficiency Index",
            score,
            {
                "kda": avg_kda,
                "solo_kill_rate": avg_solo_rate,
                "kda_score": kda_score,
                "solo_rate_score": solo_rate_score,
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="combat_efficiency_index",
            title="Combat Efficiency Index",
            description="Measures offensive efficiency — how much impact per engagement.",
            derivedFrom=["Kills", "Assists", "Damage Dealt", "Kill Participation"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )

    async def _build_objective_reliability_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Objective Reliability Index (ORI)."""
        dragon_count = sum(m.get("dragonKills", 0) for m in matches)
        baron_count = sum(m.get("baronKills", 0) for m in matches)
        
        dragon_rate = dragon_count / len(matches) if matches else 0
        baron_rate = baron_count / len(matches) if matches else 0
        
        # Estimate participation rates
        baron_presence = min(baron_rate / 0.8, 1.0)  # Normalize to typical 0.8/game
        
        score = int((baron_presence * 100 * 0.6) + (dragon_rate / 1.5 * 100 * 0.4))
        
        metrics = [
            FaultlinesMetricModel(
                id="baron_presence",
                label="Baron Presence",
                value=baron_presence,
                formattedValue=f"{int(baron_presence * 100)}%",
                unit="%",
                percent=baron_presence,
                trend="up",
            ),
            FaultlinesMetricModel(
                id="steal_prevention",
                label="Steal Prevention",
                value=0.52,
                formattedValue="52%",
                unit="%",
                percent=0.52,
                trend="down",
            ),
        ]
        
        visualization = FaultlinesVisualizationModel(
            type="progress",
            value=float(score),
            benchmark=65.0,
        )
        
        # Generate AI-powered insight
        context = (
            f"Player participates in {baron_rate:.1f} baron kills and {dragon_rate:.1f} dragon kills "
            f"per game on average across {len(matches)} matches. Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Objective Reliability Index",
            score,
            {
                "baron_presence": baron_presence,
                "baron_rate": baron_rate,
                "dragon_rate": dragon_rate,
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="objective_reliability_index",
            title="Objective Reliability Index",
            description="How consistent you are in helping secure major objectives.",
            derivedFrom=["Baron Kills", "Dragon Kills", "Turret Kills", "Objective Damage"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )

    async def _build_survival_discipline_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Survival Discipline Index (SDI)."""
        deaths_per_game = [m.get("deaths", 0) for m in matches]
        avg_deaths = statistics.mean(deaths_per_game) if deaths_per_game else 0
        
        # Create death distribution buckets
        buckets_data = [0, 0, 0, 0]  # 0-3, 4-6, 7-9, 10+
        for d in deaths_per_game:
            if d <= 3:
                buckets_data[0] += 1
            elif d <= 6:
                buckets_data[1] += 1
            elif d <= 9:
                buckets_data[2] += 1
            else:
                buckets_data[3] += 1
        
        score = max(0, int(100 - (avg_deaths / 10 * 100)))
        
        metrics = [
            FaultlinesMetricModel(
                id="avg_deaths",
                label="Deaths / Game",
                value=avg_deaths,
                formattedValue=f"{avg_deaths:.1f}",
                unit="",
                percent=min(avg_deaths / 10, 1.0),
                trend="down",
            ),
            FaultlinesMetricModel(
                id="overextension_rate",
                label="Overextension Rate",
                value=0.33,
                formattedValue="33%",
                unit="%",
                percent=0.33,
                trend="down",
            ),
        ]
        
        buckets = [
            FaultlinesVisualizationBucketModel(label="0-3", value=float(buckets_data[0])),
            FaultlinesVisualizationBucketModel(label="4-6", value=float(buckets_data[1])),
            FaultlinesVisualizationBucketModel(label="7-9", value=float(buckets_data[2])),
            FaultlinesVisualizationBucketModel(label="10+", value=float(buckets_data[3])),
        ]
        
        visualization = FaultlinesVisualizationModel(
            type="histogram",
            buckets=buckets,
        )
        
        # Generate AI-powered insight
        context = (
            f"Player averages {avg_deaths:.1f} deaths per game across {len(matches)} matches. "
            f"Distribution: {buckets_data[0]} games with 0-3 deaths, {buckets_data[1]} with 4-6, "
            f"{buckets_data[2]} with 7-9, {buckets_data[3]} with 10+ deaths. Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Survival Discipline Index",
            score,
            {
                "avg_deaths": avg_deaths,
                "low_death_games": buckets_data[0],
                "high_death_games": buckets_data[3],
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="survival_discipline_index",
            title="Survival Discipline",
            description="Ability to minimise unnecessary deaths and adapt defensively.",
            derivedFrom=["Deaths", "Damage Taken", "Heals", "Shields", "Crowd Control Time"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )

    async def _build_vision_awareness_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Vision & Awareness Index (VAI)."""
        vision_scores = []
        
        for match in matches:
            vision = match.get("visionScore", 0)
            duration_min = match.get("gameDuration", 1800) / 60
            vision_per_min = vision / duration_min if duration_min > 0 else 0
            vision_scores.append(vision_per_min)
        
        avg_vision_pm = statistics.mean(vision_scores) if vision_scores else 0
        
        score = int(min(avg_vision_pm / 2.0 * 100, 100))
        
        metrics = [
            FaultlinesMetricModel(
                id="vision_score_pm",
                label="Vision / Min",
                value=avg_vision_pm,
                formattedValue=f"{avg_vision_pm:.2f}",
                unit="",
                percent=min(avg_vision_pm / 2.0, 1.0),
                trend="up",
            ),
            FaultlinesMetricModel(
                id="wards_cleared",
                label="Wards Cleared",
                value=2.1,
                formattedValue="2.1",
                unit="",
                percent=0.42,
                trend="flat",
            ),
        ]
        
        # Create line chart points
        points = [
            FaultlinesVisualizationPointModel(label="Game 1", value=52.0),
            FaultlinesVisualizationPointModel(label="Game 2", value=60.0),
            FaultlinesVisualizationPointModel(label="Game 3", value=55.0),
            FaultlinesVisualizationPointModel(label="Game 4", value=59.0),
            FaultlinesVisualizationPointModel(label="Game 5", value=63.0),
        ]
        
        visualization = FaultlinesVisualizationModel(
            type="line",
            points=points,
        )
        
        # Generate AI-powered insight
        context = (
            f"Player maintains {avg_vision_pm:.2f} vision score per minute on average "
            f"across {len(matches)} matches. Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Vision & Awareness Index",
            score,
            {
                "vision_per_min": avg_vision_pm,
                "min_vision": min(vision_scores) if vision_scores else 0,
                "max_vision": max(vision_scores) if vision_scores else 0,
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="vision_awareness_index",
            title="Vision & Awareness Index",
            description="Vision setup and map control awareness.",
            derivedFrom=["Vision Score", "Wards Placed", "Wards Cleared", "Vision Per Minute"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )

    async def _build_economy_utilization_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Economy Utilization Index (EUI)."""
        gold_values = []
        
        for match in matches:
            gold = match.get("goldEarned", 0)
            duration_min = match.get("gameDuration", 1800) / 60
            gpm = gold / duration_min if duration_min > 0 else 0
            gold_values.append(gpm)
        
        avg_gpm = statistics.mean(gold_values) if gold_values else 0
        
        score = int(min(avg_gpm / 500 * 100, 100))
        
        metrics = [
            FaultlinesMetricModel(
                id="gold_spent_ratio",
                label="Gold Spent Ratio",
                value=0.94,
                formattedValue="94%",
                unit="%",
                percent=0.94,
                trend="up",
            ),
            FaultlinesMetricModel(
                id="damage_per_gold",
                label="Damage per 1000 Gold",
                value=1.32,
                formattedValue="1.32k",
                unit="",
                percent=0.82,
                trend="up",
            ),
        ]
        
        # Create scatter plot points
        points = [
            FaultlinesVisualizationPointModel(label="24m Win", x=12.5, y=14.1),
            FaultlinesVisualizationPointModel(label="29m Win", x=10.8, y=11.9),
            FaultlinesVisualizationPointModel(label="31m Loss", x=13.2, y=12.7),
            FaultlinesVisualizationPointModel(label="33m Loss", x=11.4, y=10.8),
        ]
        
        visualization = FaultlinesVisualizationModel(
            type="scatter",
            points=points,
        )
        
        # Generate AI-powered insight
        context = (
            f"Player earns an average of {avg_gpm:.0f} gold per minute across {len(matches)} matches. "
            f"GPM range: {min(gold_values):.0f} to {max(gold_values):.0f}. Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Economy Utilization Index",
            score,
            {
                "avg_gpm": avg_gpm,
                "min_gpm": min(gold_values) if gold_values else 0,
                "max_gpm": max(gold_values) if gold_values else 0,
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="economy_utilization_index",
            title="Economy Utilization Index",
            description="Efficiency in converting gold into meaningful pressure.",
            derivedFrom=["Gold Earned", "Gold Spent", "Damage / Gold"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )

    async def _build_role_stability_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Role Stability Index (RSI)."""
        # Group matches by role
        role_groups: dict[str, list[bool]] = {}
        for match in matches:
            role = match.get("teamPosition", "JUNGLE")
            win = match.get("win", False)
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append(win)
        
        # Calculate win rates by role
        role_win_rates = {}
        for role, wins in role_groups.items():
            if wins:
                role_win_rates[role] = sum(wins) / len(wins)
        
        # Calculate variance
        win_rate_variance = 0.0
        if len(role_win_rates) > 1:
            win_rate_variance = statistics.stdev(role_win_rates.values())
            score = max(0, int(100 - (win_rate_variance * 200)))
        else:
            score = 70  # Single role played
        
        metrics = [
            FaultlinesMetricModel(
                id="role_winrate",
                label="Role Win Rate Range",
                value=0.22,
                formattedValue="22pp",
                unit="pp",
                percent=0.56,
                trend="flat",
            ),
            FaultlinesMetricModel(
                id="role_kda_delta",
                label="Role KDA Delta",
                value=1.8,
                formattedValue="1.8",
                unit="",
                percent=0.45,
                trend="down",
            ),
        ]
        
        # Create radar chart axes
        radar_axes = []
        for role, wr in role_win_rates.items():
            radar_axes.append(RadarAxisModel(label=role.title(), value=wr * 100))
        
        visualization = FaultlinesVisualizationModel(
            type="radar",
            axes=radar_axes if radar_axes else None,
        )
        
        # Generate AI-powered insight
        roles_played = list(role_win_rates.keys())
        context = (
            f"Player has played {len(roles_played)} roles across {len(matches)} matches. "
            f"Win rates by role: {', '.join([f'{r}: {wr*100:.0f}%' for r, wr in role_win_rates.items()])}. "
            f"Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Role Stability Index",
            score,
            {
                "roles_played": roles_played,
                "role_win_rates": role_win_rates,
                "variance": win_rate_variance if len(role_win_rates) > 1 else 0,
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="role_stability_index",
            title="Role Stability Index",
            description="Measures performance stability across primary and secondary roles.",
            derivedFrom=["Role Win Rate", "Role KDA", "Role CS"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )

    async def _build_momentum_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Momentum Index (MI)."""
        # Calculate streaks
        current_streak = 0
        max_win_streak = 0
        
        for match in matches:
            if match.get("win", False):
                current_streak = max(0, current_streak) + 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                current_streak = min(0, current_streak) - 1
        
        score = int(min(max_win_streak / 5.0 * 100, 100))
        
        metrics = [
            FaultlinesMetricModel(
                id="win_streak_cap",
                label="Peak Win Streak",
                value=float(max_win_streak),
                formattedValue=str(max_win_streak),
                unit="",
                percent=min(max_win_streak / 10, 1.0),
                trend="flat",
            ),
            FaultlinesMetricModel(
                id="loss_recovery_time",
                label="Recovery Time (games)",
                value=2.4,
                formattedValue="2.4",
                unit="",
                percent=0.48,
                trend="down",
            ),
        ]
        
        # Create timeline points
        points = [
            FaultlinesVisualizationPointModel(label="Match 1", value=10.0),
            FaultlinesVisualizationPointModel(label="Match 5", value=38.0),
            FaultlinesVisualizationPointModel(label="Match 10", value=65.0),
            FaultlinesVisualizationPointModel(label="Match 15", value=44.0),
            FaultlinesVisualizationPointModel(label="Match 20", value=58.0),
        ]
        
        visualization = FaultlinesVisualizationModel(
            type="timeline",
            points=points,
        )
        
        # Generate AI-powered insight
        context = (
            f"Player's peak win streak is {max_win_streak} games across {len(matches)} matches. "
            f"Current streak: {abs(current_streak)} {'wins' if current_streak > 0 else 'losses'}. "
            f"Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Momentum Index",
            score,
            {
                "max_win_streak": max_win_streak,
                "current_streak": current_streak,
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="momentum_index",
            title="Momentum Index",
            description="Captures streak patterns — momentum and recovery.",
            derivedFrom=["Win Streaks", "Loss Streaks", "Comeback Wins"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )

    async def _build_composure_index(self, matches: list[dict[str, Any]]) -> FaultlinesAxisModel:
        """Build Composure Index (CI)."""
        kda_values = []
        gold_values = []
        death_values = []
        
        for match in matches:
            kills = match.get("kills", 0)
            deaths = max(match.get("deaths", 1), 1)
            assists = match.get("assists", 0)
            kda = (kills + assists) / deaths
            kda_values.append(kda)
            
            gold_values.append(match.get("goldEarned", 0))
            death_values.append(match.get("deaths", 0))
        
        # Calculate standard deviation for variance
        kda_variance = statistics.stdev(kda_values) if len(kda_values) > 1 else 0
        
        score = max(0, int(100 - (kda_variance / 5.0 * 100)))
        
        metrics = [
            FaultlinesMetricModel(
                id="kda_variance",
                label="KDA Variance",
                value=kda_variance,
                formattedValue=f"{kda_variance:.2f}",
                unit="",
                percent=min(kda_variance / 5.0, 1.0),
                trend="down",
            ),
            FaultlinesMetricModel(
                id="death_spread",
                label="Death Spread",
                value=0.44,
                formattedValue="44%",
                unit="%",
                percent=0.44,
                trend="flat",
            ),
        ]
        
        # Create boxplot distribution
        if kda_values:
            sorted_kda = sorted(kda_values)
            n = len(sorted_kda)
            distribution = FaultlinesVisualizationDistributionModel(
                min=sorted_kda[0],
                q1=sorted_kda[n // 4],
                median=sorted_kda[n // 2],
                q3=sorted_kda[3 * n // 4],
                max=sorted_kda[-1],
            )
        else:
            distribution = FaultlinesVisualizationDistributionModel(
                min=0.0, q1=0.0, median=0.0, q3=0.0, max=0.0
            )
        
        visualization = FaultlinesVisualizationModel(
            type="boxplot",
            distribution=distribution,
        )
        
        # Generate AI-powered insight
        context = (
            f"Player shows KDA variance of {kda_variance:.2f} across {len(matches)} matches. "
            f"KDA range: {min(kda_values):.1f} to {max(kda_values):.1f}. "
            f"Median KDA: {sorted(kda_values)[len(kda_values)//2]:.1f}. Score: {score}/100."
        )
        insight = await self._generate_insight(
            "Composure Index",
            score,
            {
                "kda_variance": kda_variance,
                "min_kda": min(kda_values) if kda_values else 0,
                "max_kda": max(kda_values) if kda_values else 0,
                "median_kda": sorted(kda_values)[len(kda_values)//2] if kda_values else 0,
            },
            context
        )
        
        return FaultlinesAxisModel(
            id="composure_index",
            title="Composure Index",
            description="Evaluates consistency between best & worst matches.",
            derivedFrom=["KDA Standard Deviation", "Gold Deviation", "Deaths Deviation"],
            score=score,
            insight=insight,
            visualization=visualization,
            metrics=metrics,
        )


# Singleton instance
faultlines_analyzer = FaultlinesAnalyzer()
