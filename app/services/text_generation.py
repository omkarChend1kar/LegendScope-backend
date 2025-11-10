"""Text Generation Service for AI-powered narrative generation.

This service provides LLM-based text generation capabilities for creating
contextual summaries, insights, and descriptions across all analysis services.
Uses AWS Lambda + Amazon Bedrock for text generation.
"""

import logging
import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TextGenerationService:
    """Service for generating text using AWS Lambda + Bedrock."""

    def __init__(self):
        """Initialize the text generation service."""
        self.lambda_url = "https://hkeufmkvn7hvrutzxog4bzpijm0wpifk.lambda-url.eu-north-1.on.aws/"
        self.primary_model = "DeepSeek-R1"  # Primary model for high-quality insights
        self.fallback_model = "Amazon Nova Micro"  # Fallback for speed/reliability
        self.timeout = 30.0  # Increased timeout for DeepSeek-R1
        self.use_ai = True  # Flag to enable/disable AI generation (can be toggled for debugging)

    async def generate_text(
        self,
        context: str,
        query: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using AWS Lambda + Bedrock based on context and query.
        
        Uses DeepSeek-R1 as primary model with Amazon Nova Micro as fallback.
        If both AI models fail, uses rule-based fallback.

        Args:
            context: Background information and data for the LLM
            query: The specific question or task for the LLM
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature (0-1, higher = more creative)

        Returns:
            Generated text string

        Raises:
            Exception: If generation fails
        """
        # Check if AI generation is enabled
        if not self.use_ai:
            logger.info("AI generation disabled, using fallback")
            return self._generate_rule_based_fallback(context, query)
        
        # Try primary model (DeepSeek-R1)
        result = await self._try_generate_with_model(
            context, query, self.primary_model, max_tokens, temperature
        )
        if result:
            return result
        
        # Try fallback model (Amazon Nova Micro)
        logger.warning(f"{self.primary_model} failed, trying {self.fallback_model}")
        result = await self._try_generate_with_model(
            context, query, self.fallback_model, max_tokens, temperature, timeout=10.0
        )
        if result:
            return result
        
        # Both AI models failed, use rule-based fallback
        logger.error("All AI models failed, using rule-based fallback")
        return self._generate_rule_based_fallback(context, query)
    
    async def generate_text_with_model_info(
        self,
        context: str,
        query: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> tuple[str, str]:
        """
        Generate text and return both the text and the model used.
        
        Returns:
            Tuple of (generated_text, model_name)
        """
        # Check if AI generation is enabled
        if not self.use_ai:
            logger.info("AI generation disabled, using fallback")
            return self._generate_rule_based_fallback(context, query), "Rule-based"
        
        # Try primary model (DeepSeek-R1)
        result = await self._try_generate_with_model(
            context, query, self.primary_model, max_tokens, temperature
        )
        if result:
            return result, self.primary_model
        
        # Try fallback model (Amazon Nova Micro)
        logger.warning(f"{self.primary_model} failed, trying {self.fallback_model}")
        result = await self._try_generate_with_model(
            context, query, self.fallback_model, max_tokens, temperature, timeout=10.0
        )
        if result:
            return result, self.fallback_model
        
        # Both AI models failed, use rule-based fallback
        logger.error("All AI models failed, using rule-based fallback")
        return self._generate_rule_based_fallback(context, query), "Rule-based"

    async def _try_generate_with_model(
        self,
        context: str,
        query: str,
        model: str,
        max_tokens: int,
        temperature: float,
        timeout: float | None = None,
    ) -> str | None:
        """
        Try to generate text with a specific model.
        
        Returns:
            Generated text if successful, None if failed
        """
        # Use provided timeout or default
        request_timeout = timeout if timeout is not None else self.timeout
        
        try:
            # Build the full prompt
            prompt = self._build_prompt(context, query)

            logger.info(f"Text generation request using {model}: {query[:100]}...")

            # Call AWS Lambda endpoint with timeout
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.post(
                    self.lambda_url,
                    json={
                        "prompt": prompt,
                        "model": model,
                        "temperature": temperature,
                        "maxTokens": max_tokens,
                    },
                )
                
                # Log response for debugging
                if response.status_code != 200:
                    logger.error(f"Lambda returned status {response.status_code} for {model}: {response.text}")
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                # Extract reply from Lambda response
                generated_text = data.get("reply", "")
                
                if not generated_text:
                    logger.warning(f"Empty response from {model}")
                    return None
                
                logger.info(f"Successfully generated text with {model}: {generated_text[:100]}...")
                return generated_text

        except httpx.TimeoutException:
            logger.warning(f"{model} request timed out after {request_timeout}s")
            return None

        except httpx.HTTPError as e:
            logger.warning(f"HTTP error with {model}: {e}")
            return None
            
        except Exception as e:
            logger.warning(f"Error with {model}: {e}")
            return None

    def _build_prompt(self, context: str, query: str) -> str:
        """Build the full prompt for the LLM."""
        return f"""You are an expert League of Legends analyst providing personalized player insights.

Context:
{context}

Task:
{query}

Requirements:
- Keep response under 2 sentences
- Be specific and actionable
- Use League of Legends terminology
- Focus on player improvement

Provide your insight:"""

    def _generate_rule_based_fallback(self, context: str, query: str) -> str:
        """Generate rule-based fallback text when all AI models are unavailable."""
        logger.info("Using rule-based fallback text generation")
        
        # Extract score from context if available
        score = 50  # default
        if "Score: " in context:
            try:
                score_str = context.split("Score: ")[1].split("/")[0]
                score = int(score_str)
            except:
                pass
        
        # Generate insight based on query type and score
        if "playstyle label" in query.lower():
            return "Adaptive Strategist"
        elif "one-liner" in query.lower():
            return "Balanced playstyle with consistent performance"
        elif "insight" in query.lower() or "Generate" in query:
            # Score-based insights
            if score >= 80:
                return "Exceptional performance in this area. Maintain consistency while exploring advanced tactics."
            elif score >= 65:
                return "Strong fundamentals with room to refine edge cases and high-pressure situations."
            elif score >= 50:
                return "Solid baseline established. Focus on consistency and decision-making under pressure."
            else:
                return "Key growth opportunity. Review patterns and practice fundamentals in this area."
        elif "highlight" in query.lower():
            return "Consistent performance across game phases"
        else:
            return "Analysis complete."

    async def generate_batch(
        self, requests: list[dict[str, str]], **kwargs
    ) -> list[str]:
        """
        Generate multiple texts in batch.

        Args:
            requests: List of dicts with 'context' and 'query' keys
            **kwargs: Additional generation parameters

        Returns:
            List of generated text strings
        """
        results = []
        for req in requests:
            text = await self.generate_text(
                context=req.get("context", ""),
                query=req.get("query", ""),
                **kwargs,
            )
            results.append(text)
        return results


# Singleton instance
text_generation_service = TextGenerationService()
