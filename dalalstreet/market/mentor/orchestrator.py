# -*- coding: utf-8 -*-
# ============================================================
# MODULE 8 - ORCHESTRATOR
# Single entry point for all mentor functionality.
# Wires all 7 modules together.
# Views call ONLY this - nothing else.
# ============================================================

import logging
from market.mentor.event_engine import EventEngine
from market.mentor.learning_engine import LearningEngine
from market.mentor.behaviour_engine import BehaviourEngine
from market.mentor.prompt_builder import PromptBuilder
from market.mentor.llm_service import LLMService
from market.mentor.card_generator import CardGenerator
from market.mentor.constants import EVENT_BUY, EVENT_SELL, EVENT_PORTFOLIO_VIEW
from market.mentor.analysis_engine import build_signals
from market.mentor.prioritizer import prioritize

logger = logging.getLogger(__name__)


class MentorOrchestrator:

    def __init__(self, user):
        self.user = user
        self.event_engine = EventEngine(user)
        self.learning_engine = LearningEngine(user)
        self.behaviour_engine = BehaviourEngine(user)
        self.llm_service = LLMService(user)
        self.card_generator = CardGenerator()

    def on_buy(self, stock, quantity, total_cost):
        try:
            event_ctx = self.event_engine.build_buy_context(stock, quantity, total_cost)
            learning_ctx = self.learning_engine.get_learning_context(
                event_type=EVENT_BUY, stock=stock
            )
            behaviour_ctx = self.behaviour_engine.analyze_buy(stock, quantity, total_cost)

            signals = build_signals(event_ctx, behaviour_ctx)
            chosen_signal = prioritize(signals, self.learning_engine.profile, self.behaviour_engine.profile)

            prompt = PromptBuilder(event_ctx, learning_ctx, behaviour_ctx, chosen_signal).build()
            raw = self.llm_service.get_mentor_card(prompt, EVENT_BUY, stock.symbol)
            card = self.card_generator.generate(raw, EVENT_BUY)
            self.learning_engine.mark_concept_taught(card.get('concept_key'))
            self.llm_service.invalidate_cache()
            return card
        except Exception as e:
            logger.error(f"Mentor on_buy error: {e}")
            return self.card_generator.generate(
                self.llm_service._get_fallback(EVENT_BUY), EVENT_BUY
            )

    def on_sell(self, stock, quantity, sell_price, avg_buy_price):
        try:
            event_ctx = self.event_engine.build_sell_context(
                stock, quantity, sell_price, avg_buy_price
            )
            learning_ctx = self.learning_engine.get_learning_context(
                event_type=EVENT_SELL, stock=stock
            )
            behaviour_ctx = self.behaviour_engine.analyze_sell(
                stock, quantity, sell_price, avg_buy_price
            )

            signals = build_signals(event_ctx, behaviour_ctx)
            chosen_signal = prioritize(signals, self.learning_engine.profile, self.behaviour_engine.profile)

            prompt = PromptBuilder(event_ctx, learning_ctx, behaviour_ctx, chosen_signal).build()
            raw = self.llm_service.get_mentor_card(prompt, EVENT_SELL, stock.symbol)
            card = self.card_generator.generate(raw, EVENT_SELL)
            self.learning_engine.mark_concept_taught(card.get('concept_key'))
            self.llm_service.invalidate_cache()
            return card
        except Exception as e:
            logger.error(f"Mentor on_sell error: {e}")
            return self.card_generator.generate(
                self.llm_service._get_fallback(EVENT_SELL), EVENT_SELL
            )

    def on_portfolio_view(self):
        try:
            event_ctx = self.event_engine.build_portfolio_context()
            learning_ctx = self.learning_engine.get_learning_context(
                event_type=EVENT_PORTFOLIO_VIEW
            )
            behaviour_ctx = self.behaviour_engine.analyze_portfolio()

            signals = build_signals(event_ctx, behaviour_ctx)
            chosen_signal = prioritize(signals, self.learning_engine.profile, self.behaviour_engine.profile)

            prompt = PromptBuilder(event_ctx, learning_ctx, behaviour_ctx, chosen_signal).build()
            raw = self.llm_service.get_mentor_card(prompt, EVENT_PORTFOLIO_VIEW)
            card = self.card_generator.generate(raw, EVENT_PORTFOLIO_VIEW)
            self.learning_engine.mark_concept_taught(card.get('concept_key'))
            return card
        except Exception as e:
            logger.error(f"Mentor on_portfolio_view error: {e}")
            return self.card_generator.generate(
                self.llm_service._get_fallback(EVENT_PORTFOLIO_VIEW),
                EVENT_PORTFOLIO_VIEW
            )

    def on_daily_report(self):
        try:
            from market.mentor.constants import EVENT_DAILY_REPORT, DAILY_REPORT_SCHEMA
            from django.utils import timezone
            import json

            event_ctx = self.event_engine.build_daily_report_context()

            if not event_ctx.todays_trades:
                return None  # nothing to report today

            today_str = timezone.now().date().isoformat()
            cached = self.llm_service._get_cached(EVENT_DAILY_REPORT, today_str)
            if cached:
                return cached

            trades_summary = "\n".join(
                f"{t['order_type']} {t['quantity']}x {t['symbol']} @ ₹{t['price']:.2f} at {t['timestamp'].strftime('%H:%M')}"
                for t in event_ctx.todays_trades
            )

            prompt = f"""You are an experienced Indian stock market mentor writing an end-of-day summary.

TODAY'S TRADES:
{trades_summary}

PORTFOLIO STATE:
Cash: ₹{event_ctx.balance:,.0f} | Invested: ₹{event_ctx.total_invested:,.0f} | Total P&L: ₹{event_ctx.total_pnl:,.0f}

Write a short, honest daily report. Judge decisions by reasoning, not just outcome.

Respond with ONLY valid JSON, no markdown:
{json.dumps(DAILY_REPORT_SCHEMA, indent=2)}"""

            raw = self.llm_service._call_gemini_with_retry(prompt)
            if raw is None:
                return None
            parsed = self.llm_service._parse_json(raw)
            if parsed:
                self.llm_service._save_to_cache(EVENT_DAILY_REPORT, today_str, parsed)
            return parsed
        except Exception as e:
            logger.error(f"Mentor on_daily_report error: {e}")
            return None

    def on_weekly_review(self):
        try:
            from market.mentor.constants import EVENT_WEEKLY_REVIEW, WEEKLY_REVIEW_SCHEMA
            from django.utils import timezone
            import json

            event_ctx = self.event_engine.build_weekly_review_context()

            if not event_ctx.weeks_trades:
                return None  # nothing to review this week

            week_key = timezone.now().strftime('%Y-W%U')  # e.g. 2026-W35
            cached = self.llm_service._get_cached(EVENT_WEEKLY_REVIEW, week_key)
            if cached:
                return cached

            trades_summary = "\n".join(
                f"{t['order_type']} {t['quantity']}x {t['symbol']} @ ₹{t['price']:.2f} on {t['timestamp'].strftime('%d %b %H:%M')}"
                for t in event_ctx.weeks_trades
            )

            behaviour_summary = self.behaviour_engine.get_coaching_summary()

            prompt = f"""You are an experienced Indian stock market mentor writing a weekly behavioural review.

THIS WEEK'S TRADES ({len(event_ctx.weeks_trades)} total):
{trades_summary}

BEHAVIOURAL HISTORY (all-time counts): {behaviour_summary['summary']}
Dominant weakness: {behaviour_summary.get('dominant_weakness') or 'None yet'}

Judge decisions by reasoning, not just outcome. Focus on PATTERNS across the week, not individual trades.

Respond with ONLY valid JSON, no markdown:
{json.dumps(WEEKLY_REVIEW_SCHEMA, indent=2)}"""

            raw = self.llm_service._call_gemini_with_retry(prompt)
            if raw is None:
                return None
            parsed = self.llm_service._parse_json(raw)
            if parsed:
                self.llm_service._save_to_cache(EVENT_WEEKLY_REVIEW, week_key, parsed)
            return parsed
        except Exception as e:
            logger.error(f"Mentor on_weekly_review error: {e}")
            return None