import json
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import MentorCardCache
from market.mentor.constants import (
    LLM_MODEL, LLM_MAX_RETRIES, EVENT_BUY, EVENT_SELL,
    EVENT_PORTFOLIO_VIEW, CACHE_PORTFOLIO_MINUTES,
)

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, user):
        self.user = user

    def get_mentor_card(self, prompt, event_type, stock_symbol='', force_refresh=False):
        if event_type == EVENT_PORTFOLIO_VIEW and not force_refresh:
            cached = self._get_cached(event_type, stock_symbol)
            if cached:
                return cached
        raw_response = self._call_gemini_with_retry(prompt)
        if raw_response is None:
            return self._get_fallback(event_type)
        parsed = self._parse_json(raw_response)
        if parsed is None:
            return self._get_fallback(event_type)
        if event_type == EVENT_PORTFOLIO_VIEW:
            self._save_to_cache(event_type, stock_symbol, parsed)
        return parsed

    def _call_gemini_with_retry(self, prompt):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=LLM_MODEL,
                generation_config={'temperature': 0.3, 'max_output_tokens': 4000}  # bumped from 2000
            )
        except Exception as e:
            logger.error(f"Gemini config error: {e}")
            return None
        for attempt in range(LLM_MAX_RETRIES):
            try:
                response = model.generate_content(prompt)
                # Check finish_reason BEFORE trusting response.text
                if response and response.candidates:
                    finish_reason = response.candidates[0].finish_reason
                    if finish_reason == 2:  # MAX_TOKENS
                        logger.warning(f"Gemini truncated output (MAX_TOKENS) on attempt {attempt + 1}")
                        if attempt == LLM_MAX_RETRIES - 1:
                            return None
                        continue  # retry rather than return half-truncated text
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                if attempt == LLM_MAX_RETRIES - 1:
                    return None
        return None

    def _parse_json(self, raw_text):
        if not raw_text:
            return None
        text = raw_text.strip()
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        if 'json' in text and '```' in text:
            try:
                start = text.index('```json') + 7
                end = text.index('```', start)
                return json.loads(text[start:end].strip())
            except Exception:
                pass
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        logger.error(f"Failed to parse JSON: {text[:200]}")
        return None

    def _get_cached(self, event_type, stock_symbol):
        cutoff = timezone.now() - timedelta(minutes=CACHE_PORTFOLIO_MINUTES)
        cached = MentorCardCache.objects.filter(
            user=self.user, event_type=event_type,
            stock_symbol=stock_symbol, is_valid=True,
            created_at__gte=cutoff,
        ).first()
        return cached.card_data if cached else None

    def _save_to_cache(self, event_type, stock_symbol, card_data):
        try:
            MentorCardCache.objects.create(
                user=self.user, event_type=event_type,
                stock_symbol=stock_symbol, card_data=card_data,
            )
        except Exception as e:
            logger.error(f"Cache save error: {e}")

    def invalidate_cache(self):
        MentorCardCache.objects.filter(
            user=self.user, is_valid=True
        ).update(is_valid=False)

    def _get_fallback(self, event_type):
        if event_type == EVENT_BUY:
            return {
                "trade_quality_score": 5, "verdict": "Acceptable",
                "strengths": ["You are actively learning by trading in the simulator"],
                "weaknesses": ["Always research fundamentals before buying"],
                "risk_level": "Medium",
                "portfolio_impact": "Trade added to portfolio.",
                "educational_insight": "Check P/E ratio, sector strength, and portfolio fit before buying.",
                "concept_key": "pe_ratio", "concept_name": "P/E Ratio",
                "concept_explanation": "P/E compares price to earnings. High P/E means high growth expectations.",
                "behavioural_observation": None,
                "improvement_suggestion": "Research last 4 quarterly results before next trade.",
            }
        elif event_type == EVENT_SELL:
            return {
                "exit_quality": "Acceptable",
                "verdict": "Trade completed. Review your reasoning.",
                "was_logical": True,
                "analysis": "Did the fundamental reason you bought this stock change?",
                "behavioural_pattern": None, "behavioural_explanation": None,
                "lesson": "Always have a pre-planned exit strategy.",
                "concept_key": "exit_strategy", "concept_name": "Exit Strategy",
                "concept_explanation": "Good exits are based on fundamentals or pre-set targets, not fear.",
                "next_steps": "Write down your target price before your next trade.",
            }
        else:
            return {
                "health_score": 50, "health_label": "Fair",
                "top_strength": "You are actively investing and building experience.",
                "top_concern": "Diversify across at least 3-4 different sectors.",
                "diversification_feedback": "Own stocks from Banking, IT, Pharma and Energy.",
                "concentration_warning": None,
                "cash_feedback": "Keep 20-30% in cash for market dip opportunities.",
                "behavioural_patterns": [],
                "three_action_items": [
                    "Review sector allocation of your holdings",
                    "Ensure no single stock exceeds 25% of portfolio",
                    "Research P/E ratio of each stock you own"
                ],
                "concept_key": "diversification", "concept_name": "Diversification",
                "concept_explanation": "Spread investments across stocks and sectors so one bad investment cannot destroy your portfolio.",
            }