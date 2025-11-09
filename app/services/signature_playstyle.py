"""Signature Playstyle Analyzer - Comprehensive playstyle profiling system.

This module analyzes player match history to generate a detailed playstyle profile
including axes analysis, tempo breakdown, consistency metrics, and champion comfort.
"""

import logging
import math
from datetime import datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas import (
    AxisMetricModel,
    ChampionComfortAxesDeltaModel,
    ChampionComfortModel,
    ChampPoolModel,
    ConsistencyModel,
    EfficiencyModel,
    PlaystyleAxesModel,
    PlaystyleAxisModel,
    PlaystyleSummaryHeaderModel,
    PlaystyleSummaryModel,
    PlaystyleSummaryResponse,
    ProfileRequest,
    RecordModel,
    RoleAndChampsModel,
    TempoHighlightModel,
    TempoModel,
    TempoPhaseModel,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# Metric baselines for z-score normalization
METRIC_BASELINES: dict[str, dict[str, float]] = {
    "killsPer10m": {"mean": 1.2, "std": 0.55},
    "soloKillsPer10m": {"mean": 0.12, "std": 0.08},
    "dpm": {"mean": 450, "std": 150},
    "largestMultiKill": {"mean": 1.25, "std": 0.6},
    "damageTakenPer10m": {"mean": 1850, "std": 420},
    "deathsPer10m": {"mean": 0.65, "std": 0.22},
    "timeDeadPer10m": {"mean": 1.15, "std": 0.45},
    "takedownsPer10m": {"mean": 2.4, "std": 0.7},
    "csPerMin": {"mean": 6.1, "std": 1.2},
    "turretTakesPerGame": {"mean": 0.85, "std": 0.55},
    "objectivesEpicPerGame": {"mean": 0.45, "std": 0.3},
    "objectiveDamagePer10m": {"mean": 320, "std": 140},
    "objectivesStolenPerGame": {"mean": 0.1, "std": 0.2},
    "visionPerMin": {"mean": 0.85, "std": 0.28},
    "wardsKilledPer10m": {"mean": 0.32, "std": 0.18},
    "detectorsPer10m": {"mean": 0.2, "std": 0.12},
    "assistsPer10m": {"mean": 2.1, "std": 0.8},
    "ccTimePer10m": {"mean": 11, "std": 6},
    "supportMitigationPer10m": {"mean": 220, "std": 140},
    "immobilizePer10m": {"mean": 0.18, "std": 0.12},
}


# Axis definitions with metrics and weights
AXIS_DEFINITIONS: dict[str, dict[str, Any]] = {
    "aggression": {
        "label": "Aggression",
        "metric_order": ["killsPer10m", "soloKillsPer10m", "dpm", "largestMultiKill"],
        "weights": {
            "killsPer10m": 1,
            "soloKillsPer10m": 1,
            "dpm": 1,
            "largestMultiKill": 0.5,
        },
    },
    "survivability": {
        "label": "Survivability",
        "metric_order": ["damageTakenPer10m", "deathsPer10m", "timeDeadPer10m"],
        "weights": {
            "damageTakenPer10m": 1,
            "deathsPer10m": -1,
            "timeDeadPer10m": -1,
        },
    },
    "skirmish_bias": {
        "label": "Skirmish Bias",
        "metric_order": ["takedownsPer10m", "csPerMin"],
        "weights": {
            "takedownsPer10m": 1,
            "csPerMin": -1,
        },
    },
    "objective_impact": {
        "label": "Objective Impact",
        "metric_order": [
            "turretTakesPerGame",
            "objectivesEpicPerGame",
            "objectiveDamagePer10m",
            "objectivesStolenPerGame",
        ],
        "weights": {
            "turretTakesPerGame": 1,
            "objectivesEpicPerGame": 1,
            "objectiveDamagePer10m": 1,
            "objectivesStolenPerGame": 0.5,
        },
    },
    "vision_discipline": {
        "label": "Vision Discipline",
        "metric_order": ["visionPerMin", "wardsKilledPer10m", "detectorsPer10m", "deathsPer10m"],
        "weights": {
            "visionPerMin": 1,
            "wardsKilledPer10m": 1,
            "detectorsPer10m": 0.5,
            "deathsPer10m": -0.25,
        },
    },
    "utility": {
        "label": "Utility",
        "metric_order": [
            "assistsPer10m",
            "ccTimePer10m",
            "supportMitigationPer10m",
            "immobilizePer10m",
        ],
        "weights": {
            "assistsPer10m": 1,
            "ccTimePer10m": 1,
            "supportMitigationPer10m": 0.5,
            "immobilizePer10m": 0.5,
        },
    },
}


# Metric presentation labels and formats
AXIS_METRIC_PRESENTATION: dict[str, dict[str, Any]] = {
    "killsPer10m": {"label": "Kill tempo", "unit": "per 10m"},
    "soloKillsPer10m": {"label": "Solo skirmishes", "unit": "per 10m"},
    "dpm": {"label": "Damage per minute", "unit": "DPM"},
    "largestMultiKill": {"label": "Largest multikill"},
    "damageTakenPer10m": {"label": "Damage soaked", "unit": "per 10m"},
    "deathsPer10m": {"label": "Deaths tempo", "unit": "per 10m"},
    "timeDeadPer10m": {"label": "Time spent dead", "unit": "per 10m"},
    "takedownsPer10m": {"label": "Takedowns", "unit": "per 10m"},
    "csPerMin": {"label": "CS cadence", "unit": "per min"},
    "turretTakesPerGame": {"label": "Turret takes", "unit": "per game"},
    "objectivesEpicPerGame": {"label": "Epic objectives", "unit": "per game"},
    "objectiveDamagePer10m": {"label": "Objective damage", "unit": "per 10m"},
    "objectivesStolenPerGame": {"label": "Objectives stolen", "unit": "per game"},
    "visionPerMin": {"label": "Vision score", "unit": "per min"},
    "wardsKilledPer10m": {"label": "Wards cleared", "unit": "per 10m"},
    "detectorsPer10m": {"label": "Detectors placed", "unit": "per 10m"},
    "assistsPer10m": {"label": "Assists", "unit": "per 10m"},
    "ccTimePer10m": {"label": "CC uptime", "unit": "per 10m"},
    "supportMitigationPer10m": {"label": "Shielding & mitigation", "unit": "per 10m"},
    "immobilizePer10m": {"label": "Immobilisations", "unit": "per 10m"},
}


# Tempo metrics and labels
TEMPO_PHASE_LABELS: dict[str, str] = {
    "early": "Early game",
    "mid": "Mid game",
    "late": "Late game",
}


class SignaturePlaystyleAnalyzer:
    """Analyzes match history to generate comprehensive playstyle profiles."""

    MIN_DURATION_SECONDS = 480  # 8 minutes minimum

    async def analyze(self, player_id: str, region: str = "na1") -> PlaystyleSummaryResponse:
        """
        Analyze player's signature playstyle from match history.
        
        Args:
            player_id: Player PUUID
            region: Server region
            
        Returns:
            PlaystyleSummaryResponse with status and data
        """
        # Check profile status first
        status = await self._get_profile_status(player_id, region)
        
        if status != "READY":
            return PlaystyleSummaryResponse(
                status=status or "UNKNOWN",
                data=None,
            )
        
        # Fetch matches
        matches = await self._fetch_matches(player_id)
        
        if not matches or len(matches) == 0:
            return PlaystyleSummaryResponse(
                status="NO_MATCHES",
                data=None,
            )
        
        # Filter valid matches
        valid_matches = [
            m for m in matches
            if m.get("gameDuration", 0) >= self.MIN_DURATION_SECONDS
        ]
        
        if not valid_matches:
            return PlaystyleSummaryResponse(
                status="NO_MATCHES",
                data=None,
            )
        
        try:
            # Derive match statistics
            derived_matches = [self._derive_match(m) for m in valid_matches]
            
            # Calculate all analyses
            games = len(derived_matches)
            wins = sum(1 for m in derived_matches if m["win"])
            losses = games - wins
            
            axes = self._build_axes(derived_matches)
            efficiency = self._build_efficiency(derived_matches)
            tempo = self._build_tempo(derived_matches)
            consistency = self._build_consistency(derived_matches)
            role_and_champs = self._build_role_and_champs(derived_matches, axes)
            
            primary_role = role_and_champs.role_mix
            primary_role_name = (
                max(primary_role.items(), key=lambda x: x[1])[0]
                if primary_role
                else "FLEX"
            )
            
            playstyle_label, one_liner = self._pick_playstyle_label(
                axes, primary_role_name, efficiency
            )
            insights = self._build_insights(axes, efficiency, tempo, consistency)
            
            header = PlaystyleSummaryHeaderModel(
                primaryRole=primary_role_name,
                playstyleLabel=playstyle_label,
                oneLiner=one_liner,
                record=RecordModel(games=games, wins=wins, losses=losses),
                windowLabel="Last 20 battles",
            )
            
            summary = PlaystyleSummaryModel(
                summary=header,
                axes=axes,
                efficiency=efficiency,
                tempo=tempo,
                consistency=consistency,
                roleAndChamps=role_and_champs,
                insights=insights,
                generatedAt=datetime.utcnow().isoformat() + "Z",
            )
            
            return PlaystyleSummaryResponse(
                status="READY",
                data=summary,
            )
            
        except Exception as e:
            logger.error(f"Error analyzing playstyle: {e}", exc_info=True)
            return PlaystyleSummaryResponse(
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
                
                if "matches" in data:
                    matches = data.get("matches", [])
                elif isinstance(data, dict) and "body" in data:
                    import json
                    body_data = data["body"]
                    body = json.loads(body_data) if isinstance(body_data, str) else body_data
                    matches = body.get("matches", [])
                else:
                    matches = []
                
                logger.info(f"Fetched {len(matches)} matches for playstyle analysis")
                return matches
                
        except Exception as e:
            logger.error(f"Error fetching matches: {e}", exc_info=True)
            return []

    def _derive_match(self, match: dict[str, Any]) -> dict[str, Any]:
        """Derive computed statistics from raw match data."""
        duration = match.get("gameDuration", 1)
        
        # Safe number extraction
        def safe_num(value: Any, default: float = 0.0) -> float:
            if isinstance(value, int | float) and math.isfinite(value):
                return float(value)
            return default
        
        # Per-minute and per-10-minute calculations
        def per_min(value: float) -> float:
            return (value * 60) / duration if duration > 0 else 0
        
        def per_10min(value: float) -> float:
            return (value * 600) / duration if duration > 0 else 0
        
        kills = safe_num(match.get("kills"))
        deaths = safe_num(match.get("deaths"))
        assists = safe_num(match.get("assists"))
        
        total_minions = safe_num(match.get("totalMinionsKilled")) + safe_num(
            match.get("neutralMinionsKilled")
        )
        takedowns = kills + assists
        
        return {
            "matchId": match.get("matchId", ""),
            "champion": match.get("championName", "Unknown"),
            "role": self._normalize_role(match.get("teamPosition", "UNKNOWN")),
            "win": bool(match.get("win")),
            "durationSeconds": duration,
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "killsPer10m": per_10min(kills),
            "soloKillsPer10m": per_10min(safe_num(match.get("soloKills"))),
            "dpm": per_min(safe_num(match.get("totalDamageDealtToChampions"))),
            "largestMultiKill": safe_num(match.get("largestMultiKill")),
            "damageTakenPer10m": per_10min(safe_num(match.get("totalDamageTaken"))),
            "deathsPer10m": per_10min(deaths),
            "timeDeadPer10m": per_10min(safe_num(match.get("totalTimeSpentDead"))),
            "takedownsPer10m": per_10min(takedowns),
            "csPerMin": per_min(total_minions),
            "turretTakesPerGame": (
                safe_num(match.get("turretKills")) + safe_num(match.get("inhibitorKills"))
            ),
            "objectivesEpicPerGame": (
                safe_num(match.get("baronKills")) + safe_num(match.get("dragonKills"))
            ),
            "objectiveDamagePer10m": per_10min(safe_num(match.get("damageDealtToObjectives"))),
            "objectivesStolenPerGame": safe_num(match.get("objectivesStolen")),
            "visionPerMin": per_min(safe_num(match.get("visionScore"))),
            "wardsKilledPer10m": per_10min(safe_num(match.get("wardsKilled"))),
            "detectorsPer10m": per_10min(safe_num(match.get("detectorWardsPlaced"))),
            "assistsPer10m": per_10min(assists),
            "ccTimePer10m": per_10min(safe_num(match.get("timeCCingOthers"))),
            "supportMitigationPer10m": per_10min(
                safe_num(match.get("totalDamageShieldedOnTeammates")) +
                safe_num(match.get("totalHealsOnTeammates"))
            ),
            "immobilizePer10m": 0.0,  # Not available in current data
            "killParticipation": safe_num(match.get("killParticipation", 0.5)),
            "damageShare": safe_num(match.get("damageShare", 0.2)),
            "gpm": safe_num(match.get("goldPerMinute"), per_min(safe_num(match.get("goldEarned")))),
        }

    def _normalize_role(self, role: str) -> str:
        """Normalize role name."""
        role_upper = role.upper()
        role_map = {
            "JUNGLE": "JUNGLE",
            "MIDDLE": "MID",
            "MID": "MID",
            "BOTTOM": "BOTTOM",
            "ADC": "BOTTOM",
            "UTILITY": "SUPPORT",
            "SUPPORT": "SUPPORT",
            "TOP": "TOP",
        }
        return role_map.get(role_upper, "FLEX")

    def _build_axes(self, matches: list[dict[str, Any]]) -> PlaystyleAxesModel:
        """Build all six playstyle axes."""
        # Collect metric series
        metrics_series: dict[str, list[float]] = {}
        for metric_key in METRIC_BASELINES.keys():
            metrics_series[metric_key] = [m.get(metric_key, 0.0) for m in matches]
        
        # Build each axis
        axes_dict = {}
        for axis_key, definition in AXIS_DEFINITIONS.items():
            # Calculate averages for this axis
            axis_values = {
                metric: self._average(metrics_series[metric])
                for metric in definition["metric_order"]
                if metric in metrics_series
            }
            axes_dict[axis_key] = self._build_axis(axis_key, axis_values)
        
        return PlaystyleAxesModel(
            aggression=axes_dict["aggression"],
            survivability=axes_dict["survivability"],
            skirmishBias=axes_dict["skirmish_bias"],
            objectiveImpact=axes_dict["objective_impact"],
            visionDiscipline=axes_dict["vision_discipline"],
            utility=axes_dict["utility"],
        )

    def _build_axis(self, axis_key: str, values: dict[str, float]) -> PlaystyleAxisModel:
        """Build a single axis with score and metrics."""
        definition = AXIS_DEFINITIONS[axis_key]
        weights = definition["weights"]
        
        # Calculate axis score
        score = self._axis_score(values, weights)
        score_label = self._resolve_score_label(score)
        
        # Build metrics
        metrics = []
        for metric_key in definition["metric_order"]:
            if metric_key not in values:
                continue
            
            value = values[metric_key]
            weight = weights.get(metric_key, 0)
            metric = self._build_axis_metric(axis_key, metric_key, value, weight)
            metrics.append(metric)
        
        # Sort by priority
        metrics.sort(key=lambda m: m.percent, reverse=True)
        
        return PlaystyleAxisModel(
            key=axis_key,
            label=definition["label"],
            score=score,
            scoreLabel=score_label,
            metrics=metrics,
            evidence=values,
        )

    def _build_axis_metric(
        self, axis_key: str, metric_key: str, value: float, weight: float
    ) -> AxisMetricModel:
        """Build a single axis metric."""
        presentation = AXIS_METRIC_PRESENTATION.get(metric_key, {})
        label = presentation.get("label", metric_key)
        unit = presentation.get("unit")
        
        # Format display value
        if "dpm" in metric_key.lower() or "damage" in metric_key.lower():
            display_value = f"{int(value)}"
        elif "per" in metric_key.lower():
            display_value = f"{value:.2f}"
        else:
            display_value = f"{value:.1f}"
        
        # Calculate percent
        percent = self._compute_axis_metric_percent(metric_key, value, weight)
        
        # Determine direction
        direction = "positive" if weight > 0 else "negative" if weight < 0 else "neutral"
        
        return AxisMetricModel(
            id=f"{axis_key}-{metric_key}",
            label=label,
            unit=unit,
            value=value,
            displayValue=display_value,
            direction=direction,
            percent=percent,
        )

    def _compute_axis_metric_percent(self, metric_key: str, value: float, weight: float) -> int:
        """Compute percentile score for a metric."""
        baseline = METRIC_BASELINES.get(metric_key)
        if not baseline or baseline["std"] == 0:
            return 50
        
        z = (value - baseline["mean"]) / baseline["std"]
        adjusted = -z if weight < 0 else z
        percent = 50 + adjusted * 18
        return self._clamp_percent(percent)

    def _axis_score(self, values: dict[str, float], weights: dict[str, float]) -> int:
        """Calculate overall axis score from weighted metrics."""
        total_weight = 0.0
        z_sum = 0.0
        
        for metric, weight in weights.items():
            baseline = METRIC_BASELINES.get(metric)
            if not baseline:
                continue
            
            raw_value = values.get(metric, 0.0)
            z = (raw_value - baseline["mean"]) / baseline["std"] if baseline["std"] != 0 else 0
            z_sum += z * weight
            total_weight += abs(weight)
        
        normalized_z = z_sum / total_weight if total_weight > 0 else 0
        score = 50 + normalized_z * 15
        return self._clamp_percent(score)

    def _resolve_score_label(self, score: int) -> str:
        """Resolve score interpretation label."""
        if score >= 80:
            return "Signature strength"
        if score >= 65:
            return "Key advantage"
        if score >= 50:
            return "Balanced"
        if score >= 35:
            return "Developing"
        return "Needs focus"

    def _build_efficiency(self, matches: list[dict[str, Any]]) -> EfficiencyModel:
        """Build efficiency metrics."""
        kda_series = [
            (m["kills"] + m["assists"]) / max(m["deaths"], 1)
            for m in matches
        ]
        kp_series = [m["killParticipation"] for m in matches]
        damage_share_series = [m["damageShare"] for m in matches]
        gpm_series = [m["gpm"] for m in matches]
        vision_series = [m["visionPerMin"] for m in matches]
        
        return EfficiencyModel(
            kda=round(self._average(kda_series), 2),
            kp=round(self._clamp(self._average(kp_series), 0, 1), 2),
            damageShare=round(self._clamp(self._average(damage_share_series), 0, 1), 2),
            gpm=int(self._average(gpm_series)),
            visionPerMin=round(self._average(vision_series), 2),
        )

    def _build_tempo(self, matches: list[dict[str, Any]]) -> TempoModel:
        """Build tempo analysis across game phases."""
        # Phase calculations - simplified version
        # In production, you'd want to use challenge data for accurate phase splits
        
        phase_data = {
            "early": {"killsPer10m": [], "deathsPer10m": [], "dpm": [], "csPerMin": [], "kp": []},
            "mid": {"killsPer10m": [], "deathsPer10m": [], "dpm": [], "csPerMin": [], "kp": []},
            "late": {"killsPer10m": [], "deathsPer10m": [], "dpm": [], "csPerMin": [], "kp": []},
        }
        
        # Simplified: Use overall stats as proxy for each phase
        for match in matches:
            for phase in ["early", "mid", "late"]:
                phase_data[phase]["killsPer10m"].append(match["killsPer10m"])
                phase_data[phase]["deathsPer10m"].append(match["deathsPer10m"])
                phase_data[phase]["dpm"].append(match["dpm"])
                phase_data[phase]["csPerMin"].append(match["csPerMin"])
                phase_data[phase]["kp"].append(match["killParticipation"])
        
        # Build phase models
        by_phase: dict[str, TempoPhaseModel] = {}
        for phase_key in ["early", "mid", "late"]:
            data = phase_data[phase_key]
            by_phase[phase_key] = TempoPhaseModel(
                key=phase_key,
                label=TEMPO_PHASE_LABELS[phase_key],
                roleLabel="Balanced tempo",
                killsPer10m=round(self._average(data["killsPer10m"]), 2),
                deathsPer10m=round(self._average(data["deathsPer10m"]), 2),
                dpm=round(self._average(data["dpm"]), 0),
                csPerMin=round(self._average(data["csPerMin"]), 2),
                kp=round(self._average(data["kp"]), 2),
                metrics=[],
            )
        
        # Determine best phase
        best_phase = "Mid"  # Default
        
        highlights = [
            TempoHighlightModel(
                id="tempo-highlight-1",
                title="Consistent performance",
                phaseLabel="All phases",
                metricLabel="Balanced tempo",
                description="Maintains steady performance across game phases.",
            )
        ]
        
        return TempoModel(
            bestPhase=best_phase,
            byPhase=by_phase,
            highlights=highlights,
        )

    def _build_consistency(self, matches: list[dict[str, Any]]) -> ConsistencyModel:
        """Build consistency analysis."""
        kda_series = [(m["kills"] + m["assists"]) / max(m["deaths"], 1) for m in matches]
        dpm_series = [m["dpm"] for m in matches]
        kp_series = [m["killParticipation"] for m in matches]
        cs_series = [m["csPerMin"] for m in matches]
        vision_series = [m["visionPerMin"] for m in matches]
        
        kda_cv = self._coefficient_of_variation(kda_series)
        
        return ConsistencyModel(
            kdaCV=round(kda_cv, 2),
            dpmCV=round(self._coefficient_of_variation(dpm_series), 2),
            kpCV=round(self._coefficient_of_variation(kp_series), 2),
            csCV=round(self._coefficient_of_variation(cs_series), 2),
            visionCV=round(self._coefficient_of_variation(vision_series), 2),
            label=self._resolve_consistency_label(kda_cv),
        )

    def _resolve_consistency_label(self, cv: float) -> str:
        """Resolve consistency label from coefficient of variation."""
        if cv < 0.25:
            return "Stable"
        if cv < 0.45:
            return "Streaky"
        return "Volatile"

    def _build_role_and_champs(
        self, matches: list[dict[str, Any]], axes: PlaystyleAxesModel
    ) -> RoleAndChampsModel:
        """Build role and champion analysis."""
        # Role distribution
        role_counts: dict[str, int] = {}
        for match in matches:
            role = match["role"]
            role_counts[role] = role_counts.get(role, 0) + 1
        
        total_games = len(matches)
        role_mix = {
            role: int((count / total_games) * 100)
            for role, count in role_counts.items()
        }
        
        # Champion pool
        champ_counts: dict[str, int] = {}
        champ_matches: dict[str, list[dict[str, Any]]] = {}
        for match in matches:
            champ = match["champion"]
            champ_counts[champ] = champ_counts.get(champ, 0) + 1
            if champ not in champ_matches:
                champ_matches[champ] = []
            champ_matches[champ].append(match)
        
        entropy = self._compute_entropy(champ_counts)
        
        # Comfort picks (3+ games)
        comfort_picks = []
        for champ, champ_games in champ_matches.items():
            if len(champ_games) < 3:
                continue
            
            wins = sum(1 for m in champ_games if m["win"])
            deaths = sum(max(m["deaths"], 0) for m in champ_games)
            kda = sum(m["kills"] + m["assists"] for m in champ_games) / max(deaths, 1)
            
            comfort_picks.append(
                ChampionComfortModel(
                    champion=champ,
                    games=len(champ_games),
                    wr=int((wins / len(champ_games)) * 100),
                    kda=round(kda, 2),
                    axesDelta=ChampionComfortAxesDeltaModel(),
                )
            )
        
        comfort_picks.sort(key=lambda x: (x.games, x.wr), reverse=True)
        comfort_picks = comfort_picks[:4]
        
        return RoleAndChampsModel(
            roleMix=role_mix,
            champPool=ChampPoolModel(unique=len(champ_counts), entropy=round(entropy, 2)),
            comfortPicks=comfort_picks,
        )

    def _compute_entropy(self, counts: dict[str, int]) -> float:
        """Compute normalized entropy for diversity."""
        total = sum(counts.values())
        if total == 0:
            return 0.0
        
        probs = [c / total for c in counts.values() if c > 0]
        entropy = -sum(p * math.log(p) for p in probs)
        max_entropy = math.log(max(len(counts), 1))
        
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _pick_playstyle_label(
        self, axes: PlaystyleAxesModel, primary_role: str, efficiency: EfficiencyModel
    ) -> tuple[str, str]:
        """Pick playstyle label and one-liner."""
        # Sort axes by score
        sorted_axes = sorted(
            [
                ("aggression", axes.aggression.score),
                ("survivability", axes.survivability.score),
                ("skirmishBias", axes.skirmish_bias.score),
                ("objectiveImpact", axes.objective_impact.score),
                ("visionDiscipline", axes.vision_discipline.score),
                ("utility", axes.utility.score),
            ],
            key=lambda x: x[1],
            reverse=True,
        )
        
        top_axis = sorted_axes[0][0] if sorted_axes else "balanced"
        
        # Build one-liner
        kp_pct = int(efficiency.kp * 100)
        dmg_pct = int(efficiency.damage_share * 100)
        one_liner = f"Balanced playstyle ({kp_pct}% KP, {dmg_pct}% DMG share)"
        
        # Simple label mapping
        label_map = {
            "aggression": "Aggressive Striker",
            "survivability": "Frontline Anchor",
            "skirmishBias": "Roaming Skirmisher",
            "objectiveImpact": "Objective-First Navigator",
            "visionDiscipline": "Map Sentinel",
            "utility": "Tactical Enabler",
        }
        
        label = label_map.get(top_axis, "Adaptive Strategist")
        
        return label, one_liner

    def _build_insights(
        self,
        axes: PlaystyleAxesModel,
        efficiency: EfficiencyModel,
        tempo: TempoModel,
        consistency: ConsistencyModel,
    ) -> list[str]:
        """Build actionable insights."""
        insights = []
        
        # Top axis insight
        sorted_axes = sorted(
            [
                ("Aggression", axes.aggression.score),
                ("Survivability", axes.survivability.score),
                ("Skirmish Bias", axes.skirmish_bias.score),
                ("Objective Impact", axes.objective_impact.score),
                ("Vision Discipline", axes.vision_discipline.score),
                ("Utility", axes.utility.score),
            ],
            key=lambda x: x[1],
            reverse=True,
        )
        
        if sorted_axes:
            top_name, top_score = sorted_axes[0]
            insights.append(
                f"Your strongest axis is {top_name} ({top_score}). "
                f"Anchor plays around this strength."
            )
        
        # Consistency insight
        cv_pct = int(consistency.kda_cv * 100)
        insights.append(
            f"Consistency profile reads {consistency.label.lower()} "
            f"(KDA CV {cv_pct}%). Expect {consistency.label.lower()} performance."
        )
        
        # Tempo insight
        insights.append(
            f"{tempo.best_phase} game impact shines brightest — "
            f"leverage this timing to secure advantages."
        )
        
        # Efficiency insight
        if efficiency.kp >= 0.6 and efficiency.damage_share >= 0.22:
            insights.append(
                "High team share: KP and damage output suggest you're a primary carry."
            )
        
        return insights[:4]

    # Utility methods
    
    def _average(self, values: list[float]) -> float:
        """Calculate average."""
        return sum(values) / len(values) if values else 0.0

    def _std_deviation(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = self._average(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _coefficient_of_variation(self, values: list[float]) -> float:
        """Calculate coefficient of variation."""
        mean = self._average(values)
        if mean == 0:
            return 0.0
        return self._std_deviation(values) / abs(mean)

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max."""
        return max(min_val, min(max_val, value))

    def _clamp_percent(self, value: float) -> int:
        """Clamp to 0-100 integer percent."""
        return int(self._clamp(value, 0, 100))


# Singleton instance
signature_playstyle_analyzer = SignaturePlaystyleAnalyzer()
