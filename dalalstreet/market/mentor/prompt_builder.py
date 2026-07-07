# ============================================================
# MODULE 5 — PROMPT BUILDER
# Assembles focused prompts from all context objects.
# Selects only relevant pillars per event + knowledge level.
# Keeps prompts concise and structured.
# ============================================================

from market.mentor.constants import (
    EVENT_BUY,
    EVENT_SELL,
    EVENT_PORTFOLIO_VIEW,
    PILLAR_MAP,
    PILLAR_FUNDAMENTAL,
    PILLAR_VALUATION,
    PILLAR_ENTRY,
    PILLAR_EXIT,
    PILLAR_PORTFOLIO,
    PILLAR_BEHAVIOURAL,
    PILLAR_EDUCATIONAL,
    PILLAR_RISK,
    PILLAR_SECTOR,
    PILLAR_PERFORMANCE,
    KNOWLEDGE_BEGINNER,
    BUY_CARD_SCHEMA,
    SELL_CARD_SCHEMA,
    PORTFOLIO_CARD_SCHEMA,
)


class PromptBuilder:

    def __init__(self, event_context, learning_context, behaviour_context):
        self.event = event_context
        self.learning = learning_context
        self.behaviour = behaviour_context

    def build(self):
        """
        Main entry point.
        Returns the final prompt string for the LLM.
        """
        if self.event.event_type == EVENT_BUY:
            return self._build_buy_prompt()
        elif self.event.event_type == EVENT_SELL:
            return self._build_sell_prompt()
        elif self.event.event_type == EVENT_PORTFOLIO_VIEW:
            return self._build_portfolio_prompt()
        else:
            raise ValueError(f"Unknown event type: {self.event.event_type}")

    # ----------------------------------------------------------
    # BUY PROMPT
    # ----------------------------------------------------------
    def _build_buy_prompt(self):
        pillars = PILLAR_MAP[EVENT_BUY].get(
            self.event.knowledge_level,
            PILLAR_MAP[EVENT_BUY][KNOWLEDGE_BEGINNER]
        )

        sections = []

        sections.append(self._system_instruction())
        sections.append(self._user_profile_section())
        sections.append(self._trade_section_buy())

        if PILLAR_FUNDAMENTAL in pillars:
            sections.append(self._fundamental_section())

        if PILLAR_VALUATION in pillars:
            sections.append(self._valuation_section())

        if PILLAR_ENTRY in pillars:
            sections.append(self._entry_section())

        if PILLAR_RISK in pillars:
            sections.append(self._risk_section())

        if PILLAR_SECTOR in pillars:
            sections.append(self._sector_section())

        if PILLAR_PORTFOLIO in pillars:
            sections.append(self._portfolio_section())

        if PILLAR_BEHAVIOURAL in pillars:
            sections.append(self._behaviour_section())

        sections.append(self._learning_section())
        sections.append(self._buy_output_instruction())

        return '\n\n'.join(filter(None, sections))

    # ----------------------------------------------------------
    # SELL PROMPT
    # ----------------------------------------------------------
    def _build_sell_prompt(self):
        pillars = PILLAR_MAP[EVENT_SELL].get(
            self.event.knowledge_level,
            PILLAR_MAP[EVENT_SELL][KNOWLEDGE_BEGINNER]
        )

        sections = []

        sections.append(self._system_instruction())
        sections.append(self._user_profile_section())
        sections.append(self._trade_section_sell())

        if PILLAR_EXIT in pillars:
            sections.append(self._exit_section())

        if PILLAR_FUNDAMENTAL in pillars:
            sections.append(self._fundamental_section())

        if PILLAR_BEHAVIOURAL in pillars:
            sections.append(self._behaviour_section())

        if PILLAR_PERFORMANCE in pillars:
            sections.append(self._performance_section())

        if PILLAR_PORTFOLIO in pillars:
            sections.append(self._portfolio_section())

        sections.append(self._learning_section())
        sections.append(self._sell_output_instruction())

        return '\n\n'.join(filter(None, sections))

    # ----------------------------------------------------------
    # PORTFOLIO PROMPT
    # ----------------------------------------------------------
    def _build_portfolio_prompt(self):
        pillars = PILLAR_MAP[EVENT_PORTFOLIO_VIEW].get(
            self.event.knowledge_level,
            PILLAR_MAP[EVENT_PORTFOLIO_VIEW][KNOWLEDGE_BEGINNER]
        )

        sections = []

        sections.append(self._system_instruction())
        sections.append(self._user_profile_section())
        sections.append(self._portfolio_section())

        if PILLAR_RISK in pillars:
            sections.append(self._risk_section())

        if PILLAR_SECTOR in pillars:
            sections.append(self._sector_section())

        if PILLAR_BEHAVIOURAL in pillars:
            sections.append(self._behaviour_section())

        if PILLAR_PERFORMANCE in pillars:
            sections.append(self._performance_section())

        sections.append(self._learning_section())
        sections.append(self._portfolio_output_instruction())

        return '\n\n'.join(filter(None, sections))

    # ----------------------------------------------------------
    # SECTIONS
    # ----------------------------------------------------------
    def _system_instruction(self):
        return """ROLE: You are an experienced Indian stock market mentor and investing coach.
You are NOT a chatbot. You do NOT wait for questions.
You automatically analyze every trade the user makes and provide educational coaching.

CORE RULES:
- NEVER predict stock prices
- NEVER guarantee profits or returns
- NEVER say "Buy this" or "Sell this"
- ALWAYS explain WHY, not just WHAT
- ALWAYS teach — every response must improve the user's investing knowledge
- Use Indian context (NSE, Nifty, ₹, Indian companies as examples)
- Be encouraging but honest
- Be concise — no essays, only mentor cards"""

    def _user_profile_section(self):
        level = self.event.knowledge_level
        lessons = self.learning.concepts_taught_count

        level_desc = {
            'beginner': 'Complete beginner. Use very simple language. Explain every term.',
            'intermediate': 'Has basic knowledge. Can handle moderate complexity.',
            'advanced': 'Experienced. Use professional terminology.',
        }.get(level, 'Beginner')

        return f"""USER PROFILE:
Username: {self.event.username}
Knowledge Level: {level.upper()} — {level_desc}
Lessons received so far: {lessons}
{self.learning.to_dict().get('already_knows', '')}"""

    def _trade_section_buy(self):
        e = self.event
        first_trade_note = "\nNOTE: This is the user's FIRST EVER trade. Be extra encouraging." if e.is_first_trade else ""

        return f"""BUY TRADE:
Stock: {e.stock_symbol} — {e.stock_name}
Quantity: {e.quantity} shares
Price: ₹{e.trade_price:.2f}
Total invested: ₹{e.total_trade_value:.0f}
Today's change: {e.change_percent_today:+.2f}%
Market Cap Category: {e.market_cap_category}
Sector: {e.stock_sector}{first_trade_note}"""

    def _trade_section_sell(self):
        e = self.event
        outcome = 'PROFIT' if e.pnl >= 0 else 'LOSS'

        return f"""SELL TRADE:
Stock: {e.stock_symbol} — {e.stock_name}
Quantity: {e.quantity} shares sold
Sell price: ₹{e.trade_price:.2f}
Avg buy price: ₹{e.avg_buy_price:.2f}
P&L: ₹{e.pnl:.0f} ({e.pnl_pct:+.1f}%) — {outcome}
Today's change: {e.change_percent_today:+.2f}%"""

    def _fundamental_section(self):
        e = self.event
        if not e.stock:
            return None

        lines = ["FUNDAMENTALS (use only available data):"]
        if e.pe_ratio:
            lines.append(f"P/E Ratio: {e.pe_ratio:.1f}")
        if e.eps:
            lines.append(f"EPS: ₹{e.eps:.2f}")
        if e.roe:
            lines.append(f"ROE: {e.roe:.1f}%")
        if e.pb_ratio:
            lines.append(f"P/B Ratio: {e.pb_ratio:.2f}")
        if e.debt_to_equity:
            lines.append(f"Debt/Equity: {e.debt_to_equity:.2f}")
        if e.dividend_yield:
            lines.append(f"Dividend Yield: {e.dividend_yield:.2f}%")
        if e.market_cap:
            lines.append(f"Market Cap: ₹{e.market_cap/10000000:.0f} Cr ({e.market_cap_category})")

        if len(lines) == 1:
            return None
        return '\n'.join(lines)

    def _valuation_section(self):
        e = self.event
        if not e.stock or not e.pe_ratio:
            return None

        pe = e.pe_ratio
        if pe > 50:
            valuation_note = "EXPENSIVE — P/E above 50 implies very high growth expectations. High risk if growth disappoints."
        elif pe > 30:
            valuation_note = "MODERATELY EXPENSIVE — P/E above 30. Priced for good growth."
        elif pe > 15:
            valuation_note = "FAIR VALUE — P/E in reasonable range for most Indian companies."
        elif pe > 0:
            valuation_note = "POTENTIALLY CHEAP — Low P/E. Research why before assuming undervalued."
        else:
            valuation_note = "P/E not meaningful — check if company is profitable."

        week_range_note = ""
        if e.week52_high and e.week52_low and e.week52_high > e.week52_low:
            position = ((e.current_price - e.week52_low) / (e.week52_high - e.week52_low)) * 100
            week_range_note = f"\n52W Position: {position:.0f}% of 52-week range (Low ₹{e.week52_low} — High ₹{e.week52_high})"

        return f"""VALUATION:
P/E Assessment: {valuation_note}{week_range_note}"""

    def _entry_section(self):
        e = self.event
        if not e.stock:
            return None

        lines = ["ENTRY ANALYSIS:"]

        if e.change_percent_today > 5:
            lines.append(f"⚠️ Stock up {e.change_percent_today:.1f}% today — buying on a strong up day. Higher entry risk.")
        elif e.change_percent_today < -3:
            lines.append(f"Stock down {abs(e.change_percent_today):.1f}% today — buying on a dip. Could be opportunity or falling knife.")
        else:
            lines.append(f"Stock change today: {e.change_percent_today:+.1f}% — relatively neutral entry day.")

        if e.week52_high and e.week52_low and e.week52_high > e.week52_low:
            position = ((e.current_price - e.week52_low) / (e.week52_high - e.week52_low)) * 100
            if position > 85:
                lines.append(f"Price near 52-week HIGH ({position:.0f}% of range) — buying near top of range.")
            elif position < 20:
                lines.append(f"Price near 52-week LOW ({position:.0f}% of range) — buying near bottom of range.")
            else:
                lines.append(f"Price at {position:.0f}% of 52-week range — mid-range entry.")

        return '\n'.join(lines)

    def _exit_section(self):
        e = self.event
        lines = ["EXIT ANALYSIS:"]

        if e.pnl_pct < -10:
            lines.append(f"Significant loss of {e.pnl_pct:.1f}%. Analyze if fundamentals changed or this is temporary volatility.")
        elif e.pnl_pct < 0:
            lines.append(f"Small loss of {e.pnl_pct:.1f}%. Was there a fundamental reason to exit, or was this emotional?")
        elif e.pnl_pct < 5:
            lines.append(f"Very small profit of {e.pnl_pct:.1f}%. Consider if this exit was premature.")
        elif e.pnl_pct < 20:
            lines.append(f"Reasonable profit of {e.pnl_pct:.1f}%. Analyze if the original investment thesis played out.")
        else:
            lines.append(f"Strong profit of {e.pnl_pct:.1f}%. Well done for holding through to meaningful gains.")

        if e.stock and e.stock.pe_ratio:
            lines.append(f"Stock still trades at P/E {e.stock.pe_ratio} — consider if fundamentals still support higher price.")

        return '\n'.join(lines)

    def _portfolio_section(self):
        e = self.event
        lines = [
            "PORTFOLIO CONTEXT:",
            f"Cash: ₹{e.balance:,.0f} ({e.cash_pct:.1f}%) | Invested: ₹{e.total_invested:,.0f} ({e.invested_pct:.1f}%)",
            f"Total P&L: ₹{e.total_pnl:,.0f}",
            f"Number of holdings: {e.num_holdings}",
        ]

        if e.holdings_data:
            lines.append("Holdings:")
            for h in e.holdings_data[:8]:
                lines.append(
                    f"  {h['symbol']} ({h['sector']}): {h['quantity']}x | "
                    f"P&L {h['pnl_pct']:+.1f}%"
                )

        if e.sector_allocation:
            lines.append("Sector allocation:")
            for sector, pct in e.sector_allocation.items():
                lines.append(f"  {sector}: {pct:.1f}%")

        return '\n'.join(lines)

    def _risk_section(self):
        e = self.event
        lines = ["RISK FACTORS:"]

        if e.debt_to_equity and e.debt_to_equity > 1.5:
            lines.append(f"⚠️ High D/E ratio of {e.debt_to_equity:.1f} — significant debt burden.")

        if e.invested_pct > 80:
            lines.append(f"⚠️ Portfolio {e.invested_pct:.0f}% invested — very little cash reserve.")

        if e.num_holdings <= 2:
            lines.append("⚠️ Very few holdings — high concentration risk.")

        if e.sector_allocation:
            max_sector = max(e.sector_allocation, key=e.sector_allocation.get)
            max_pct = e.sector_allocation[max_sector]
            if max_pct > 60:
                lines.append(f"⚠️ {max_sector} sector = {max_pct:.0f}% of portfolio — sector concentration risk.")

        if len(lines) == 1:
            lines.append("No major risk flags detected based on available data.")

        return '\n'.join(lines)

    def _sector_section(self):
        e = self.event
        if not e.stock_sector:
            return None

        return f"""SECTOR CONTEXT:
Stock sector: {e.stock_sector}
Portfolio exposure to this sector before trade: {e.sector_allocation.get(e.stock_sector, 0):.1f}%
Total sectors in portfolio: {len(e.sector_allocation)}"""

    def _behaviour_section(self):
        b = self.behaviour
        coaching = {
            'summary': b.pattern_explanation or 'No behavioral patterns detected yet.',
            'dominant_weakness': b.dominant_weakness,
            'coaching_needed': b.coaching_priority,
            'dominant_weakness_count': b.dominant_weakness_count,
        }

        lines = [f"BEHAVIOURAL HISTORY: {coaching['summary']}"]

        if b.detected_pattern:
            lines.append(f"DETECTED THIS TRADE: {b.detected_pattern}")
            lines.append(f"Explanation: {b.pattern_explanation}")

        if coaching.get('coaching_needed'):
            lines.append(
                f"⚠️ COACHING PRIORITY: User's dominant weakness is "
                f"'{coaching['dominant_weakness']}' — detected "
                f"{coaching.get('dominant_weakness_count', 0)} times. "
                f"Address this specifically in your response."
            )

        return '\n'.join(lines)

    def _performance_section(self):
        e = self.event
        orders = []
        try:
            from portfolio.models import Order
            recent = Order.objects.filter(
                user=e.user
            ).order_by('-timestamp')[:20]

            wins = sum(1 for o in recent if o.order_type == 'SELL')
            lines = [
                f"PERFORMANCE CONTEXT:",
                f"Total trades: {e.total_trades_ever}",
            ]
            return '\n'.join(lines)
        except Exception:
            return None

    def _learning_section(self):
        l = self.learning

        lines = [
            f"LEARNING INSTRUCTION:",
            f"User knowledge level: {l.knowledge_level}",
            f"Lessons received so far: {l.concepts_taught_count}",
            f"Concept to teach this trade: {l.concept_name or 'Choose the most relevant'}",
        ]

        if l.concept_explanation:
            lines.append(f"Use this explanation (adapt to level): {l.concept_explanation}")

        lines.append(
            "Include this concept in your educational_insight field. "
            "Explain it simply. Relate it to this specific trade."
        )

        return '\n'.join(lines)

    def _buy_output_instruction(self):
        import json
        schema_str = json.dumps(BUY_CARD_SCHEMA, indent=2)

        return f"""OUTPUT INSTRUCTION:
Respond with ONLY valid JSON. No markdown. No explanation outside JSON.
Use this exact schema:
{schema_str}

Rules for your response:
- trade_quality_score: 1-10 integer based on fundamentals, entry timing, portfolio impact
- strengths: 2-3 specific points using actual data from above
- weaknesses: 1-2 honest concerns — never say "none" if risks exist
- educational_insight: 2-3 sentences teaching the concept above, related to THIS specific trade
- concept_key: must exactly match one of the concept keys provided
- behavioural_observation: null if no pattern, otherwise describe what you detected
- improvement_suggestion: null if trade was good, otherwise one specific actionable tip"""

    def _sell_output_instruction(self):
        import json
        schema_str = json.dumps(SELL_CARD_SCHEMA, indent=2)

        return f"""OUTPUT INSTRUCTION:
Respond with ONLY valid JSON. No markdown. No explanation outside JSON.
Use this exact schema:
{schema_str}

Rules:
- exit_quality: honest assessment — do not soften if it was panic selling
- behavioural_pattern: must be one of the allowed values or null
- lesson: the single most important thing this trade teaches
- next_steps: one specific actionable suggestion"""

    def _portfolio_output_instruction(self):
        import json
        schema_str = json.dumps(PORTFOLIO_CARD_SCHEMA, indent=2)

        return f"""OUTPUT INSTRUCTION:
Respond with ONLY valid JSON. No markdown. No explanation outside JSON.
Use this exact schema:
{schema_str}

Rules:
- health_score: 1-100 based on diversification, risk, cash allocation
- three_action_items: specific, actionable, based on actual portfolio data above
- concept_explanation: explain in simple language relevant to their current portfolio"""
