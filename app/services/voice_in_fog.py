"""Voice in the Fog Service - Chat Inference with Match Context.

This service provides chat capabilities with context from player matches,
allowing users to ask questions about their gameplay and receive AI-powered insights.
"""

import logging
from typing import Any
from datetime import datetime, timedelta

from app.services.text_generation import text_generation_service

logger = logging.getLogger(__name__)


class VoiceInFogService:
    """Service for chat inference with match context."""

    def __init__(self):
        """Initialize the Voice in the Fog service."""
        self.text_service = text_generation_service
        # Simple in-memory cache for gameplay profiles (expires after 5 minutes)
        self._profile_cache: dict[str, tuple[str, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)

    async def chat(
        self,
        messages: list[dict[str, str]],
        context_prompt: str = "",
        player_id: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> dict[str, Any]:
        """
        Send a chat message with context and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Example: [{"role": "user", "content": "What's my best champion?"}]
            context_prompt: Optional system/context prompt with player data
            player_id: Optional player PUUID to fetch matches and build gameplay profile
                      Profile is cached for 5 minutes to improve performance
            model: Model to use (ignored, uses text generation service)
            temperature: Sampling temperature (ignored, uses text generation service defaults)
            max_tokens: Maximum tokens in response (ignored, uses text generation service defaults)

        Returns:
            Dict with 'modelUsed' and 'reply' keys

        Raises:
            Exception: If the text generation call fails
        """
        try:
            # Build the full prompt from context and conversation
            context_parts = []
            
            # If player_id provided, try to get gameplay profile (with caching)
            if player_id:
                gameplay_profile = await self._get_cached_gameplay_profile(player_id)
                if gameplay_profile:
                    context_parts.append(gameplay_profile)
            
            if context_prompt:
                context_parts.append(context_prompt)
            
            # Add conversation history to context
            if messages and len(messages) > 1:
                context_parts.append("\n# Previous Conversation:")
                for msg in messages[:-1]:  # All but last message
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        context_parts.append(f"User: {content}")
                    elif role == "assistant":
                        context_parts.append(f"Assistant: {content}")
            
            # Last message is the query
            query = messages[-1].get("content", "Hello") if messages else "Hello"
            context = "\n".join(context_parts) if context_parts else "You are an AI strategist analyzing gameplay."
            
            logger.info(f"Voice in the Fog chat request: {len(messages)} messages, player_id: {player_id is not None}")
            
            # Use text generation service with model info
            reply, model_used = await self.text_service.generate_text_with_model_info(
                context=context,
                query=query,
            )
            
            return {
                "modelUsed": model_used,
                "reply": reply,
            }

        except Exception as e:
            logger.error(f"Voice in the Fog error: {e}", exc_info=True)
            raise
    
    async def _get_cached_gameplay_profile(self, player_id: str) -> str | None:
        """
        Get gameplay profile with caching to improve performance.
        
        Cache expires after 5 minutes. If cache is fresh, return cached profile.
        Otherwise fetch new profile and update cache.
        
        Args:
            player_id: Player PUUID
            
        Returns:
            Gameplay profile string or None if fetch fails
        """
        now = datetime.now()
        
        # Check if we have a fresh cached profile
        if player_id in self._profile_cache:
            profile, cached_at = self._profile_cache[player_id]
            if now - cached_at < self._cache_ttl:
                logger.info(f"Using cached gameplay profile for {player_id[:8]}...")
                return profile
        
        # Cache miss or expired - fetch new profile
        try:
            logger.info(f"Fetching gameplay profile for {player_id[:8]}...")
            profile = await self._fetch_and_build_gameplay_profile(player_id)
            self._profile_cache[player_id] = (profile, now)
            
            # Clean up old cache entries (keep only last 50 players)
            if len(self._profile_cache) > 50:
                # Remove oldest entries
                sorted_cache = sorted(
                    self._profile_cache.items(),
                    key=lambda x: x[1][1]
                )
                self._profile_cache = dict(sorted_cache[-50:])
            
            return profile
        except Exception as e:
            logger.warning(f"Failed to fetch gameplay profile for {player_id[:8]}: {e}")
            return None

    # ==================== Dedicated Starter Topic APIs ====================
    
    async def get_echoes_of_battle_insight(
        self,
        player_id: str,
        starter_topic: str,
    ) -> dict[str, Any]:
        """
        Generate Echoes of Battle insight for a starter topic.
        
        Simple flow: Fetch matches → Build context → Generate insight
        No conversation history - just one-shot analysis.
        
        Args:
            player_id: Player PUUID
            starter_topic: One of the 5 starter topics
            
        Returns:
            Dict with 'starterTopic' and 'insight' keys
        """
        # Fetch last 20 matches
        from app.core.config import get_settings
        import httpx
        
        settings = get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.lambda_get_matches_url,
                json={"puuid": player_id},
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle both direct and wrapped response formats
            if "matches" in data:
                matches = data.get("matches", [])
            elif isinstance(data, dict) and "body" in data:
                import json as json_lib
                body_data = data["body"]
                body = json_lib.loads(body_data) if isinstance(body_data, str) else body_data
                matches = body.get("matches", [])
            else:
                matches = []
        
        if not matches:
            raise Exception("No matches found for this player")
        
        # Build context based on starter topic
        context = self._build_echoes_context(matches, starter_topic)
        
        # Create comprehensive query
        query = f"""Analyze the player's {starter_topic} from their last 20 matches.

Provide a comprehensive analysis that includes:
1. Current performance summary with specific numbers
2. Key patterns and trends identified
3. Notable strengths to leverage
4. Areas for improvement with specific examples
5. 2-3 actionable recommendations

Be specific, data-driven, and provide concrete examples from their matches."""
        
        # Generate insight using text service with higher token limit
        insight = await self.text_service.generate_text(
            context=context,
            query=query,
            max_tokens=1000,  # Increased for comprehensive responses
            temperature=0.7,
        )
        
        return {
            "starterTopic": starter_topic,
            "insight": insight,
        }
    
    async def get_patterns_beneath_chaos_insight(
        self,
        player_id: str,
        starter_topic: str,
    ) -> dict[str, Any]:
        """
        Generate Patterns Beneath Chaos insight for a playstyle axis.
        
        Simple flow: Fetch matches → Build context → Generate insight
        No conversation history - just one-shot analysis.
        
        Args:
            player_id: Player PUUID
            starter_topic: One of the 7 playstyle axes
            
        Returns:
            Dict with 'starterTopic' and 'insight' keys
        """
        # Fetch last 20 matches
        from app.core.config import get_settings
        import httpx
        
        settings = get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.lambda_get_matches_url,
                json={"puuid": player_id},
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle both direct and wrapped response formats
            if "matches" in data:
                matches = data.get("matches", [])
            elif isinstance(data, dict) and "body" in data:
                import json as json_lib
                body_data = data["body"]
                body = json_lib.loads(body_data) if isinstance(body_data, str) else body_data
                matches = body.get("matches", [])
            else:
                matches = []
        
        if not matches:
            raise Exception("No matches found for this player")
        
        # Build context based on starter topic
        context = self._build_patterns_context(matches, starter_topic)
        
        # Create comprehensive query
        query = f"""Analyze the player's {starter_topic} playstyle axis from their last 20 matches.

Provide a detailed analysis covering:
1. Current playstyle profile with metrics
2. How they compare to typical players in this axis
3. Situational patterns (when they excel vs struggle)
4. Playstyle strengths to maintain
5. Adjustments that could improve their effectiveness
6. Specific in-game scenarios where they should adapt

Use concrete numbers and examples from their match data."""
        
        # Generate insight using text service with higher token limit
        insight = await self.text_service.generate_text(
            context=context,
            query=query,
            max_tokens=1000,  # Increased for comprehensive responses
            temperature=0.7,
        )
        
        return {
            "starterTopic": starter_topic,
            "insight": insight,
        }
    
    async def get_faultlines_insight(
        self,
        player_id: str,
        starter_topic: str,
    ) -> dict[str, Any]:
        """
        Generate Faultlines insight for a performance index.
        
        Simple flow: Fetch matches → Build context → Generate insight
        No conversation history - just one-shot analysis.
        
        Args:
            player_id: Player PUUID
            starter_topic: One of the 7 indices
            
        Returns:
            Dict with 'starterTopic' and 'insight' keys
        """
        # Fetch last 20 matches
        from app.core.config import get_settings
        import httpx
        
        settings = get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.lambda_get_matches_url,
                json={"puuid": player_id},
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle both direct and wrapped response formats
            if "matches" in data:
                matches = data.get("matches", [])
            elif isinstance(data, dict) and "body" in data:
                import json as json_lib
                body_data = data["body"]
                body = json_lib.loads(body_data) if isinstance(body_data, str) else body_data
                matches = body.get("matches", [])
            else:
                matches = []
        
        if not matches:
            raise Exception("No matches found for this player")
        
        # Build context based on starter topic
        context = self._build_faultlines_topic_context(matches, starter_topic)
        
        # Create comprehensive query
        query = f"""Perform a deep analysis of the player's {starter_topic} across their last 20 matches.

Provide a thorough performance assessment including:
1. Index score interpretation with benchmarks
2. Performance breakdown by game phase/situation
3. Comparison to role/rank expectations
4. Critical weaknesses impacting this index
5. Hidden strengths they're not fully utilizing
6. Step-by-step improvement plan with priorities

Reference specific stats and match examples to support your analysis."""
        
        # Generate insight using text service with higher token limit
        insight = await self.text_service.generate_text(
            context=context,
            query=query,
            max_tokens=1200,  # Even higher for deep analytical insights
            temperature=0.7,
        )
        
        return {
            "starterTopic": starter_topic,
            "insight": insight,
        }

    # ==================== Original Context Methods ====================

    async def chat_with_match_context(
        self,
        user_message: str,
        matches: list[dict[str, Any]],
        player_stats: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Chat about player matches with full context.

        Args:
            user_message: The user's question/message
            matches: List of match data to provide as context
            player_stats: Optional aggregated player statistics
            conversation_history: Optional previous messages in conversation
            model: Optional model override

        Returns:
            Dict with 'modelUsed' and 'reply' keys
        """
        # Build context prompt from match data
        context_prompt = self._build_match_context(matches, player_stats)

        # Build message history
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        return await self.chat(
            messages=messages,
            context_prompt=context_prompt,
            model=model,
        )
    
    async def chat_with_player_matches(
        self,
        user_message: str,
        player_id: str,
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Chat about player's matches by fetching them first.

        Args:
            user_message: The user's question/message
            player_id: Player PUUID
            conversation_history: Optional previous messages
            model: Optional model override

        Returns:
            Dict with 'modelUsed' and 'reply' keys
        """
        # Note: This method expects matches to be fetched by the route handler
        # For now, return error message suggesting to use chat_with_match_context directly
        raise Exception(
            "Please fetch matches first and use chat_with_match_context. "
            "This endpoint requires match data to be provided by the caller."
        )

    async def chat_with_playstyle_context(
        self,
        user_message: str,
        playstyle_data: dict[str, Any],
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Chat about playstyle analysis with context.

        Args:
            user_message: The user's question/message
            playstyle_data: Playstyle analysis data
            conversation_history: Optional previous messages
            model: Optional model override

        Returns:
            Dict with 'modelUsed' and 'reply' keys
        """
        # Build context from playstyle data
        context_prompt = self._build_playstyle_context(playstyle_data)

        # Build message history
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        return await self.chat(
            messages=messages,
            context_prompt=context_prompt,
            model=model,
        )

    async def chat_with_faultlines_context(
        self,
        user_message: str,
        faultlines_data: dict[str, Any],
        conversation_history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Chat about Faultlines analysis with context.

        Args:
            user_message: The user's question/message
            faultlines_data: Faultlines analysis data
            conversation_history: Optional previous messages
            model: Optional model override

        Returns:
            Dict with 'modelUsed' and 'reply' keys
        """
        # Build context from faultlines data
        context_prompt = self._build_faultlines_context(faultlines_data)

        # Build message history
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        return await self.chat(
            messages=messages,
            context_prompt=context_prompt,
            model=model,
        )

    def _build_match_context(
        self, matches: list[dict[str, Any]], player_stats: dict[str, Any] | None = None
    ) -> str:
        """Build context prompt from match data."""
        context_lines = [
            "You are an AI strategist embedded in a gaming analytics platform called LegendScope. "
            "You have access to battle summaries, player stats, and historical performance data. "
            "Always respond with deep reasoning and clear tactical suggestions based on the provided context.",
            "",
            "# Player Match Data",
        ]

        # Add aggregated stats if provided
        if player_stats:
            context_lines.append("\n## Overall Statistics:")
            for key, value in player_stats.items():
                context_lines.append(f"- {key}: {value}")

        # Add recent matches summary
        context_lines.append(f"\n## Recent Matches ({len(matches)} games):")
        for i, match in enumerate(matches[:10], 1):  # Limit to 10 matches for context
            champion = match.get("championName", "Unknown")
            role = match.get("teamPosition", "Unknown")
            win = "Win" if match.get("win") else "Loss"
            kda = f"{match.get('kills', 0)}/{match.get('deaths', 0)}/{match.get('assists', 0)}"
            context_lines.append(f"{i}. {champion} ({role}) - {win} - {kda}")

        context_lines.append("\nProvide clear, actionable insights based on this data.")
        context_lines.append("Be conversational but precise. Use League of Legends terminology.")

        return "\n".join(context_lines)

    def _build_playstyle_context(self, playstyle_data: dict[str, Any]) -> str:
        """Build context prompt from playstyle analysis."""
        context_lines = [
            "You are an AI strategist embedded in a gaming analytics platform called LegendScope. "
            "You have analyzed this player's signature playstyle across multiple matches.",
            "",
            "# Player Playstyle Analysis",
        ]

        summary = playstyle_data.get("summary", {})
        axes = playstyle_data.get("axes", {})
        efficiency = playstyle_data.get("efficiency", {})

        # Add summary info
        if summary:
            context_lines.append(f"\n## Profile:")
            context_lines.append(f"- Role: {summary.get('primaryRole', 'Unknown')}")
            context_lines.append(f"- Style: {summary.get('playstyleLabel', 'Unknown')}")
            context_lines.append(f"- Summary: {summary.get('oneLiner', '')}")
            record = summary.get("record", {})
            if record:
                context_lines.append(
                    f"- Record: {record.get('wins', 0)}W - {record.get('losses', 0)}L"
                )

        # Add axis scores
        if axes:
            context_lines.append("\n## Playstyle Axes:")
            for axis_key, axis_data in axes.items():
                if isinstance(axis_data, dict):
                    score = axis_data.get("score", 0)
                    label = axis_data.get("label", axis_key)
                    context_lines.append(f"- {label}: {score}/100")

        # Add efficiency metrics
        if efficiency:
            context_lines.append("\n## Efficiency Metrics:")
            for key, value in efficiency.items():
                context_lines.append(f"- {key}: {value}")

        context_lines.append("\nProvide insights based on this playstyle analysis.")
        context_lines.append("Be conversational, actionable, and use League terminology.")

        return "\n".join(context_lines)

    def _build_faultlines_context(self, faultlines_data: dict[str, Any]) -> str:
        """Build context prompt from Faultlines analysis."""
        context_lines = [
            "You are an AI strategist embedded in a gaming analytics platform called LegendScope. "
            "You have performed deep Faultlines analysis to identify the player's strengths and weaknesses across 8 key dimensions.",
            "",
            "# Player Faultlines Analysis (Strengths & Weaknesses)",
        ]

        data = faultlines_data.get("data", {})
        axes = data.get("axes", [])

        if axes:
            context_lines.append("\n## Analytical Axes:")
            for axis in axes:
                axis_id = axis.get("id", "unknown")
                title = axis.get("title", "Unknown")
                score = axis.get("score", 0)
                insight = axis.get("insight", "")

                context_lines.append(f"\n### {title} (Score: {score}/100)")
                context_lines.append(f"ID: {axis_id}")
                if insight:
                    context_lines.append(f"Insight: {insight}")

                # Add metrics
                metrics = axis.get("metrics", [])
                if metrics:
                    context_lines.append("Metrics:")
                    for metric in metrics[:3]:  # Top 3 metrics
                        label = metric.get("label", "")
                        value = metric.get("formattedValue", "")
                        if label and value:
                            context_lines.append(f"  - {label}: {value}")

        context_lines.append("\nUse this Faultlines data to provide tactical advice on what to improve.")
        context_lines.append("Be specific, reference exact metrics, and suggest actionable improvements.")

        return "\n".join(context_lines)

    # ==================== Starter Topic Context Builders ====================
    
    def _build_echoes_context(self, matches: list[dict[str, Any]], starter_topic: str) -> str:
        """Build context for Echoes of Battle based on starter topic."""
        context_lines = [
            "You are an AI strategist embedded in LegendScope analyzing battle history.",
            "",
            f"# Echoes of Battle: {starter_topic}",
            f"Analyzing last {len(matches)} matches for patterns and insights.",
            ""
        ]
        
        if starter_topic == "Battles Fought":
            # Total matches and overall patterns
            total_wins = sum(1 for m in matches if m.get("win"))
            total_losses = len(matches) - total_wins
            context_lines.append(f"## Match Overview:")
            context_lines.append(f"- Total Matches: {len(matches)}")
            context_lines.append(f"- Record: {total_wins}W - {total_losses}L")
            context_lines.append(f"- Win Rate: {(total_wins/len(matches)*100):.1f}%")
            
            # Champion variety
            champions = {}
            for m in matches:
                champ = m.get("championName", "Unknown")
                champions[champ] = champions.get(champ, 0) + 1
            context_lines.append(f"\n## Champion Pool: {len(champions)} unique champions")
            
        elif starter_topic == "Claim / Fall Ratio":
            # Win/loss patterns
            wins = [m for m in matches if m.get("win")]
            losses = [m for m in matches if not m.get("win")]
            
            context_lines.append(f"## Win/Loss Analysis:")
            context_lines.append(f"- Wins: {len(wins)} ({len(wins)/len(matches)*100:.1f}%)")
            context_lines.append(f"- Losses: {len(losses)} ({len(losses)/len(matches)*100:.1f}%)")
            
            if wins:
                avg_win_kda = sum(m.get("kills", 0) + m.get("assists", 0) for m in wins) / len(wins)
                context_lines.append(f"- Avg K+A in Wins: {avg_win_kda:.1f}")
            if losses:
                avg_loss_deaths = sum(m.get("deaths", 0) for m in losses) / len(losses)
                context_lines.append(f"- Avg Deaths in Losses: {avg_loss_deaths:.1f}")
                
        elif starter_topic == "Longest Claim & Fall Streaks":
            # Calculate streaks
            current_streak = 0
            max_win_streak = 0
            max_loss_streak = 0
            current_is_win = None
            
            for m in matches:
                is_win = m.get("win")
                if is_win == current_is_win:
                    current_streak += 1
                else:
                    current_streak = 1
                    current_is_win = is_win
                
                if is_win:
                    max_win_streak = max(max_win_streak, current_streak)
                else:
                    max_loss_streak = max(max_loss_streak, current_streak)
            
            context_lines.append(f"## Streak Analysis:")
            context_lines.append(f"- Longest Win Streak: {max_win_streak} games")
            context_lines.append(f"- Longest Loss Streak: {max_loss_streak} games")
            
        elif starter_topic == "Clutch Battles":
            # Identify close games (based on game duration or KDA)
            clutch_games = []
            for m in matches:
                duration = m.get("gameDuration", 0)
                kills = m.get("kills", 0)
                deaths = m.get("deaths", 0)
                assists = m.get("assists", 0)
                
                # Clutch = long game (>30min) or close KDA
                if duration > 1800 or (deaths > 0 and (kills + assists) / deaths < 2):
                    clutch_games.append(m)
            
            context_lines.append(f"## Clutch Game Analysis:")
            context_lines.append(f"- Clutch Games: {len(clutch_games)}/{len(matches)}")
            clutch_wins = sum(1 for m in clutch_games if m.get("win"))
            if clutch_games:
                context_lines.append(f"- Clutch Win Rate: {clutch_wins/len(clutch_games)*100:.1f}%")
                
        elif starter_topic == "Role Influence":
            # Performance by role
            roles = {}
            for m in matches:
                role = m.get("teamPosition", "Unknown")
                if role not in roles:
                    roles[role] = {"wins": 0, "total": 0, "kills": 0, "deaths": 0, "assists": 0}
                roles[role]["total"] += 1
                if m.get("win"):
                    roles[role]["wins"] += 1
                roles[role]["kills"] += m.get("kills", 0)
                roles[role]["deaths"] += m.get("deaths", 0)
                roles[role]["assists"] += m.get("assists", 0)
            
            context_lines.append(f"## Role Performance:")
            for role, stats in roles.items():
                wr = stats["wins"] / stats["total"] * 100 if stats["total"] > 0 else 0
                context_lines.append(f"- {role}: {stats['wins']}W-{stats['total']-stats['wins']}L ({wr:.1f}% WR)")
        
        # Add recent matches
        context_lines.append(f"\n## Recent Matches (last 5):")
        for i, m in enumerate(matches[:5], 1):
            win_str = "Win" if m.get("win") else "Loss"
            kda = f"{m.get('kills', 0)}/{m.get('deaths', 0)}/{m.get('assists', 0)}"
            champ = m.get("championName", "Unknown")
            context_lines.append(f"{i}. {champ} - {win_str} - {kda}")
        
        return "\n".join(context_lines)
    
    def _build_patterns_context(self, matches: list[dict[str, Any]], starter_topic: str) -> str:
        """Build context for Patterns Beneath Chaos based on playstyle axis."""
        context_lines = [
            "You are an AI strategist embedded in LegendScope analyzing playstyle patterns.",
            "",
            f"# Patterns Beneath Chaos: {starter_topic}",
            f"Analyzing {len(matches)} matches to identify {starter_topic.lower()} patterns.",
            ""
        ]
        
        if starter_topic == "Aggression":
            # Kill participation and early game aggression
            total_kills = sum(m.get("kills", 0) for m in matches)
            avg_kills = total_kills / len(matches)
            first_bloods = sum(1 for m in matches if m.get("firstBloodKill", False))
            
            context_lines.append(f"## Aggression Metrics:")
            context_lines.append(f"- Avg Kills/Game: {avg_kills:.1f}")
            context_lines.append(f"- First Bloods: {first_bloods}/{len(matches)}")
            context_lines.append(f"- Total Takedowns: {sum(m.get('kills', 0) + m.get('assists', 0) for m in matches)}")
            
        elif starter_topic == "Survivability":
            # Death analysis
            total_deaths = sum(m.get("deaths", 0) for m in matches)
            avg_deaths = total_deaths / len(matches)
            low_death_games = sum(1 for m in matches if m.get("deaths", 0) <= 3)
            
            context_lines.append(f"## Survivability Metrics:")
            context_lines.append(f"- Avg Deaths/Game: {avg_deaths:.1f}")
            context_lines.append(f"- Low Death Games (≤3): {low_death_games}/{len(matches)}")
            context_lines.append(f"- Perfect Games (0 deaths): {sum(1 for m in matches if m.get('deaths', 0) == 0)}")
            
        elif starter_topic == "Skirmish Bias":
            # Small fights vs teamfights (assists ratio)
            total_kills = sum(m.get("kills", 0) for m in matches)
            total_assists = sum(m.get("assists", 0) for m in matches)
            
            context_lines.append(f"## Skirmish Analysis:")
            context_lines.append(f"- Total Kills: {total_kills}")
            context_lines.append(f"- Total Assists: {total_assists}")
            if total_kills > 0:
                assist_ratio = total_assists / total_kills
                context_lines.append(f"- Assist/Kill Ratio: {assist_ratio:.2f}")
                
        elif starter_topic == "Objective Impact":
            # Objectives taken
            turrets = sum(m.get("turretTakedowns", 0) for m in matches)
            inhibs = sum(m.get("inhibitorTakedowns", 0) for m in matches)
            
            context_lines.append(f"## Objective Metrics:")
            context_lines.append(f"- Tower Takedowns: {turrets} (avg {turrets/len(matches):.1f}/game)")
            context_lines.append(f"- Inhibitor Takedowns: {inhibs}")
            
        elif starter_topic == "Vision Discipline":
            # Vision score
            total_vision = sum(m.get("visionScore", 0) for m in matches)
            avg_vision = total_vision / len(matches)
            wards_placed = sum(m.get("wardsPlaced", 0) for m in matches)
            
            context_lines.append(f"## Vision Metrics:")
            context_lines.append(f"- Avg Vision Score: {avg_vision:.1f}")
            context_lines.append(f"- Total Wards Placed: {wards_placed}")
            context_lines.append(f"- Avg Wards/Game: {wards_placed/len(matches):.1f}")
            
        elif starter_topic == "Utility":
            # Healing, shielding, CC
            total_healing = sum(m.get("totalHealsOnTeammates", 0) for m in matches)
            total_damage_mitigated = sum(m.get("damageSelfMitigated", 0) for m in matches)
            
            context_lines.append(f"## Utility Metrics:")
            context_lines.append(f"- Total Team Healing: {total_healing:,}")
            context_lines.append(f"- Damage Mitigated: {total_damage_mitigated:,}")
            
        elif starter_topic == "Tempo Profile":
            # Game duration and performance
            durations = [m.get("gameDuration", 0) for m in matches]
            avg_duration = sum(durations) / len(durations) if durations else 0
            short_games = sum(1 for d in durations if d < 1500)  # <25min
            long_games = sum(1 for d in durations if d > 2100)  # >35min
            
            context_lines.append(f"## Tempo Metrics:")
            context_lines.append(f"- Avg Game Duration: {avg_duration/60:.1f} minutes")
            context_lines.append(f"- Short Games (<25min): {short_games}/{len(matches)}")
            context_lines.append(f"- Long Games (>35min): {long_games}/{len(matches)}")
        
        # Add sample matches
        context_lines.append(f"\n## Sample Matches:")
        for i, m in enumerate(matches[:3], 1):
            win_str = "Win" if m.get("win") else "Loss"
            kda = f"{m.get('kills', 0)}/{m.get('deaths', 0)}/{m.get('assists', 0)}"
            context_lines.append(f"{i}. {m.get('championName', 'Unknown')} - {win_str} - {kda}")
        
        return "\n".join(context_lines)
    
    def _build_faultlines_topic_context(self, matches: list[dict[str, Any]], starter_topic: str) -> str:
        """Build context for Faultlines based on index topic."""
        context_lines = [
            "You are an AI strategist embedded in LegendScope performing Faultlines analysis.",
            "",
            f"# Faultlines: {starter_topic}",
            f"Deep analysis of {len(matches)} matches to identify strengths and weaknesses.",
            ""
        ]
        
        if "Combat Efficiency" in starter_topic:
            # KDA, damage, kills
            total_kills = sum(m.get("kills", 0) for m in matches)
            total_deaths = sum(m.get("deaths", 0) for m in matches)
            total_assists = sum(m.get("assists", 0) for m in matches)
            avg_damage = sum(m.get("totalDamageDealtToChampions", 0) for m in matches) / len(matches)
            
            context_lines.append(f"## Combat Efficiency Metrics:")
            context_lines.append(f"- KDA: {total_kills}/{total_deaths}/{total_assists}")
            if total_deaths > 0:
                kda_ratio = (total_kills + total_assists) / total_deaths
                context_lines.append(f"- KDA Ratio: {kda_ratio:.2f}")
            context_lines.append(f"- Avg Damage to Champions: {avg_damage:,.0f}")
            
        elif "Objective Reliability" in starter_topic:
            # Dragon, Baron, towers
            turrets = sum(m.get("turretTakedowns", 0) for m in matches)
            dragons = sum(m.get("dragonTakedowns", 0) for m in matches)
            barons = sum(m.get("baronTakedowns", 0) for m in matches)
            
            context_lines.append(f"## Objective Reliability Metrics:")
            context_lines.append(f"- Tower Takedowns: {turrets} (avg {turrets/len(matches):.1f}/game)")
            context_lines.append(f"- Dragon Takedowns: {dragons} (avg {dragons/len(matches):.1f}/game)")
            context_lines.append(f"- Baron Takedowns: {barons}")
            
        elif "Survival Discipline" in starter_topic:
            # Death patterns
            total_deaths = sum(m.get("deaths", 0) for m in matches)
            avg_deaths = total_deaths / len(matches)
            perfect_games = sum(1 for m in matches if m.get("deaths", 0) == 0)
            high_death_games = sum(1 for m in matches if m.get("deaths", 0) > 7)
            
            context_lines.append(f"## Survival Discipline Metrics:")
            context_lines.append(f"- Avg Deaths: {avg_deaths:.1f}")
            context_lines.append(f"- Perfect Games (0 deaths): {perfect_games}/{len(matches)}")
            context_lines.append(f"- High Death Games (>7): {high_death_games}/{len(matches)}")
            
        elif "Vision" in starter_topic or "Awareness" in starter_topic:
            # Vision metrics
            total_vision = sum(m.get("visionScore", 0) for m in matches)
            avg_vision = total_vision / len(matches)
            wards_placed = sum(m.get("wardsPlaced", 0) for m in matches)
            wards_killed = sum(m.get("wardsKilled", 0) for m in matches)
            
            context_lines.append(f"## Vision & Awareness Metrics:")
            context_lines.append(f"- Avg Vision Score: {avg_vision:.1f}")
            context_lines.append(f"- Wards Placed: {wards_placed} (avg {wards_placed/len(matches):.1f}/game)")
            context_lines.append(f"- Wards Killed: {wards_killed} (avg {wards_killed/len(matches):.1f}/game)")
            
        elif "Economy" in starter_topic:
            # Gold and CS
            total_gold = sum(m.get("goldEarned", 0) for m in matches)
            avg_gold = total_gold / len(matches)
            total_cs = sum(m.get("totalMinionsKilled", 0) for m in matches)
            avg_cs = total_cs / len(matches)
            
            context_lines.append(f"## Economy Utilization Metrics:")
            context_lines.append(f"- Avg Gold Earned: {avg_gold:,.0f}")
            context_lines.append(f"- Avg CS: {avg_cs:.1f}")
            context_lines.append(f"- CS/Min: {avg_cs/25:.1f}")  # Assuming 25min avg
            
        elif "Momentum" in starter_topic:
            # Early vs late game
            first_bloods = sum(1 for m in matches if m.get("firstBloodKill", False))
            early_leads = sum(1 for m in matches if m.get("goldEarned", 0) > 10000)
            
            context_lines.append(f"## Momentum Metrics:")
            context_lines.append(f"- First Bloods: {first_bloods}/{len(matches)}")
            context_lines.append(f"- Strong Economy Games (>10k gold): {early_leads}/{len(matches)}")
            
        elif "Composure" in starter_topic:
            # Performance under pressure (close games)
            wins = sum(1 for m in matches if m.get("win"))
            close_games = [m for m in matches if m.get("gameDuration", 0) > 1800]  # >30min
            close_wins = sum(1 for m in close_games if m.get("win"))
            
            context_lines.append(f"## Composure Metrics:")
            context_lines.append(f"- Overall Win Rate: {wins/len(matches)*100:.1f}%")
            context_lines.append(f"- Close Games (>30min): {len(close_games)}/{len(matches)}")
            if close_games:
                context_lines.append(f"- Close Game Win Rate: {close_wins/len(close_games)*100:.1f}%")
        
        # Add recent matches
        context_lines.append(f"\n## Recent Match Data:")
        for i, m in enumerate(matches[:5], 1):
            win_str = "Win" if m.get("win") else "Loss"
            kda = f"{m.get('kills', 0)}/{m.get('deaths', 0)}/{m.get('assists', 0)}"
            champ = m.get("championName", "Unknown")
            context_lines.append(f"{i}. {champ} - {win_str} - {kda}")
        
        return "\n".join(context_lines)
    
    async def _fetch_and_build_gameplay_profile(self, player_id: str) -> str:
        """
        Fetch last 20 matches and build comprehensive gameplay profile.
        
        This profile gives the AI context about the player's overall performance,
        playstyle, champion pool, and patterns across matches.
        
        Args:
            player_id: Player PUUID
            
        Returns:
            Formatted context string with gameplay profile
        """
        from app.core.config import get_settings
        import httpx
        
        settings = get_settings()
        
        # Fetch matches
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.lambda_get_matches_url,
                json={"puuid": player_id},
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle both direct and wrapped response formats
            if "matches" in data:
                matches = data.get("matches", [])
            elif isinstance(data, dict) and "body" in data:
                import json as json_lib
                body_data = data["body"]
                body = json_lib.loads(body_data) if isinstance(body_data, str) else body_data
                matches = body.get("matches", [])
            else:
                matches = []
        
        if not matches:
            return "No recent match history available for this player."
        
        # Build comprehensive profile
        context_lines = [
            "You are an AI strategist embedded in LegendScope. You have access to this player's gameplay profile.",
            "",
            f"# Player Gameplay Profile (Last {len(matches)} Matches)",
            ""
        ]
        
        # === Overall Performance ===
        wins = sum(1 for m in matches if m.get("win"))
        losses = len(matches) - wins
        win_rate = (wins / len(matches) * 100) if matches else 0
        
        context_lines.append("## Overall Performance")
        context_lines.append(f"- Record: {wins}W - {losses}L ({win_rate:.1f}% Win Rate)")
        
        # === KDA Analysis ===
        total_kills = sum(m.get("kills", 0) for m in matches)
        total_deaths = sum(m.get("deaths", 0) for m in matches)
        total_assists = sum(m.get("assists", 0) for m in matches)
        avg_kills = total_kills / len(matches)
        avg_deaths = total_deaths / len(matches)
        avg_assists = total_assists / len(matches)
        kda_ratio = ((total_kills + total_assists) / total_deaths) if total_deaths > 0 else total_kills + total_assists
        
        context_lines.append(f"- Average KDA: {avg_kills:.1f}/{avg_deaths:.1f}/{avg_assists:.1f} (Ratio: {kda_ratio:.2f})")
        
        # === Champion Pool ===
        champion_stats = {}
        for m in matches:
            champ = m.get("championName", "Unknown")
            if champ not in champion_stats:
                champion_stats[champ] = {"games": 0, "wins": 0}
            champion_stats[champ]["games"] += 1
            if m.get("win"):
                champion_stats[champ]["wins"] += 1
        
        # Sort by games played
        top_champs = sorted(champion_stats.items(), key=lambda x: x[1]["games"], reverse=True)[:5]
        
        context_lines.append(f"\n## Champion Pool ({len(champion_stats)} unique champions)")
        for champ, stats in top_champs:
            champ_wr = (stats["wins"] / stats["games"] * 100) if stats["games"] > 0 else 0
            context_lines.append(f"- {champ}: {stats['games']} games ({stats['wins']}W-{stats['games']-stats['wins']}L, {champ_wr:.0f}% WR)")
        
        # === Role Performance ===
        role_stats = {}
        for m in matches:
            role = m.get("teamPosition", "UNKNOWN")
            if role not in role_stats:
                role_stats[role] = {"games": 0, "wins": 0}
            role_stats[role]["games"] += 1
            if m.get("win"):
                role_stats[role]["wins"] += 1
        
        context_lines.append("\n## Role Distribution")
        for role, stats in sorted(role_stats.items(), key=lambda x: x[1]["games"], reverse=True):
            role_wr = (stats["wins"] / stats["games"] * 100) if stats["games"] > 0 else 0
            context_lines.append(f"- {role}: {stats['games']} games ({role_wr:.0f}% WR)")
        
        # === Playstyle Indicators ===
        context_lines.append("\n## Playstyle Indicators")
        
        # Aggression
        first_bloods = sum(1 for m in matches if m.get("firstBloodKill", False) or m.get("firstBloodAssist", False))
        context_lines.append(f"- First Blood Participation: {first_bloods}/{len(matches)} games ({first_bloods/len(matches)*100:.0f}%)")
        
        # Vision
        avg_vision = sum(m.get("visionScore", 0) for m in matches) / len(matches)
        avg_wards = sum(m.get("wardsPlaced", 0) for m in matches) / len(matches)
        context_lines.append(f"- Vision Score: {avg_vision:.1f} avg ({avg_wards:.1f} wards/game)")
        
        # Objectives
        avg_towers = sum(m.get("turretTakedowns", 0) for m in matches) / len(matches)
        total_dragons = sum(m.get("dragonTakedowns", 0) for m in matches)
        total_barons = sum(m.get("baronTakedowns", 0) for m in matches)
        context_lines.append(f"- Objectives: {avg_towers:.1f} towers/game, {total_dragons} dragons, {total_barons} barons total")
        
        # Economy
        avg_gold = sum(m.get("goldEarned", 0) for m in matches) / len(matches)
        avg_cs = sum(m.get("totalMinionsKilled", 0) for m in matches) / len(matches)
        context_lines.append(f"- Economy: {avg_gold:,.0f} gold/game, {avg_cs:.0f} CS/game")
        
        # Damage
        avg_damage = sum(m.get("totalDamageDealtToChampions", 0) for m in matches) / len(matches)
        context_lines.append(f"- Damage: {avg_damage:,.0f} to champions/game")
        
        # === Recent Form ===
        recent_5 = matches[:5]
        recent_wins = sum(1 for m in recent_5 if m.get("win"))
        context_lines.append(f"\n## Recent Form")
        context_lines.append(f"- Last 5 Games: {recent_wins}W-{len(recent_5)-recent_wins}L")
        
        # Show last 3 matches
        context_lines.append("\n## Recent Matches")
        for i, m in enumerate(matches[:3], 1):
            win_str = "Win" if m.get("win") else "Loss"
            kda = f"{m.get('kills', 0)}/{m.get('deaths', 0)}/{m.get('assists', 0)}"
            champ = m.get("championName", "Unknown")
            role = m.get("teamPosition", "?")
            duration = m.get("gameDuration", 0)
            duration_min = int(duration / 60)
            context_lines.append(f"{i}. {champ} ({role}) - {win_str} - {kda} - {duration_min}min")
        
        context_lines.append("\n---")
        context_lines.append("Use this profile to provide personalized, data-driven advice.")
        context_lines.append("Reference specific stats when relevant to the player's question.")
        
        return "\n".join(context_lines)


# Singleton instance
voice_in_fog_service = VoiceInFogService()
