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
            prompt = PromptBuilder(event_ctx, learning_ctx, behaviour_ctx).build()
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
            prompt = PromptBuilder(event_ctx, learning_ctx, behaviour_ctx).build()
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
            prompt = PromptBuilder(event_ctx, learning_ctx, behaviour_ctx).build()
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