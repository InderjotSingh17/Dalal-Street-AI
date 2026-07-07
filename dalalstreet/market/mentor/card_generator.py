# -*- coding: utf-8 -*-
# ============================================================
# MODULE 7 - CARD GENERATOR
# Validates and cleans LLM output.
# Guarantees all required fields exist before template renders.
# ============================================================

from market.mentor.constants import (
    EVENT_BUY, EVENT_SELL, EVENT_PORTFOLIO_VIEW,
)


class CardGenerator:

    def generate(self, raw_card, event_type):
        if event_type == EVENT_BUY:
            return self._generate_buy_card(raw_card)
        elif event_type == EVENT_SELL:
            return self._generate_sell_card(raw_card)
        elif event_type == EVENT_PORTFOLIO_VIEW:
            return self._generate_portfolio_card(raw_card)
        return {}

    def _generate_buy_card(self, raw):
        return {
            'event_type': EVENT_BUY,
            'trade_quality_score': self._int(raw.get('trade_quality_score'), 5, 1, 10),
            'verdict': self._str(raw.get('verdict'), 'Acceptable'),
            'strengths': self._list(raw.get('strengths'), ['Trade recorded.']),
            'weaknesses': self._list(raw.get('weaknesses'), ['Always research before buying.']),
            'risk_level': self._str(raw.get('risk_level'), 'Medium'),
            'portfolio_impact': self._str(raw.get('portfolio_impact'), 'Trade added to portfolio.'),
            'educational_insight': self._str(raw.get('educational_insight'), ''),
            'concept_key': self._str(raw.get('concept_key'), ''),
            'concept_name': self._str(raw.get('concept_name'), ''),
            'concept_explanation': self._str(raw.get('concept_explanation'), ''),
            'behavioural_observation': raw.get('behavioural_observation'),
            'improvement_suggestion': raw.get('improvement_suggestion'),
            'score_color': self._score_color(raw.get('trade_quality_score', 5)),
            'verdict_color': self._verdict_color(raw.get('verdict', 'Acceptable')),
        }

    def _generate_sell_card(self, raw):
        return {
            'event_type': EVENT_SELL,
            'exit_quality': self._str(raw.get('exit_quality'), 'Acceptable'),
            'verdict': self._str(raw.get('verdict'), 'Trade completed.'),
            'was_logical': bool(raw.get('was_logical', True)),
            'analysis': self._str(raw.get('analysis'), ''),
            'behavioural_pattern': raw.get('behavioural_pattern'),
            'behavioural_explanation': raw.get('behavioural_explanation'),
            'lesson': self._str(raw.get('lesson'), ''),
            'concept_key': self._str(raw.get('concept_key'), ''),
            'concept_name': self._str(raw.get('concept_name'), ''),
            'concept_explanation': self._str(raw.get('concept_explanation'), ''),
            'next_steps': self._str(raw.get('next_steps'), ''),
            'exit_color': self._exit_color(raw.get('exit_quality', 'Acceptable')),
            'is_positive_exit': raw.get('exit_quality') in ['Excellent', 'Good'],
        }

    def _generate_portfolio_card(self, raw):
        return {
            'event_type': EVENT_PORTFOLIO_VIEW,
            'health_score': self._int(raw.get('health_score'), 50, 1, 100),
            'health_label': self._str(raw.get('health_label'), 'Fair'),
            'top_strength': self._str(raw.get('top_strength'), ''),
            'top_concern': self._str(raw.get('top_concern'), ''),
            'diversification_feedback': self._str(raw.get('diversification_feedback'), ''),
            'concentration_warning': raw.get('concentration_warning'),
            'cash_feedback': self._str(raw.get('cash_feedback'), ''),
            'behavioural_patterns': self._list(raw.get('behavioural_patterns'), []),
            'three_action_items': self._list(raw.get('three_action_items'), []),
            'concept_key': self._str(raw.get('concept_key'), ''),
            'concept_name': self._str(raw.get('concept_name'), ''),
            'concept_explanation': self._str(raw.get('concept_explanation'), ''),
            'health_color': self._health_color(raw.get('health_score', 50)),
        }

    # ----------------------------------------------------------
    # COLOR HELPERS - used by templates
    # ----------------------------------------------------------
    def _score_color(self, score):
        try:
            score = int(score)
        except (TypeError, ValueError):
            return '#ffc107'
        if score >= 8:
            return '#00d68f'
        elif score >= 6:
            return '#ffc107'
        return '#ff6b6b'

    def _verdict_color(self, verdict):
        colors = {
            'Excellent': '#00d68f',
            'Good': '#00d68f',
            'Acceptable': '#ffc107',
            'Questionable': '#ff9800',
            'Risky': '#ff6b6b',
        }
        return colors.get(verdict, '#ffc107')

    def _exit_color(self, quality):
        colors = {
            'Excellent': '#00d68f',
            'Good': '#00d68f',
            'Acceptable': '#ffc107',
            'Questionable': '#ff9800',
            'Premature': '#ff9800',
            'Panic': '#ff6b6b',
        }
        return colors.get(quality, '#ffc107')

    def _health_color(self, score):
        try:
            score = int(score)
        except (TypeError, ValueError):
            return '#ffc107'
        if score >= 75:
            return '#00d68f'
        elif score >= 50:
            return '#ffc107'
        return '#ff6b6b'

    # ----------------------------------------------------------
    # TYPE SAFETY HELPERS
    # ----------------------------------------------------------
    def _str(self, value, default=''):
        if value is None:
            return default
        return str(value).strip() or default

    def _int(self, value, default=5, min_val=1, max_val=10):
        try:
            result = int(value)
            return max(min_val, min(max_val, result))
        except (TypeError, ValueError):
            return default

    def _list(self, value, default=None):
        if default is None:
            default = []
        if isinstance(value, list):
            return value
        return default