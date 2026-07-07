# ============================================================
# MODULE 3 — BEHAVIOUR ENGINE
# Detects investing behavioral patterns from trades.
# Updates BehaviourProfile counts.
# Returns BehaviourContext for Prompt Builder.
# ============================================================

from django.utils import timezone
from datetime import timedelta
from accounts.models import BehaviourProfile
from portfolio.models import Order, Holding
from market.mentor.constants import (
    BEHAVIOUR_PANIC_SELL,
    BEHAVIOUR_FOMO_BUY,
    BEHAVIOUR_OVERTRADE,
    BEHAVIOUR_HOLD_LOSER,
    BEHAVIOUR_SELL_WINNER_EARLY,
    BEHAVIOUR_POOR_DIVERSIFICATION,
    BEHAVIOUR_LOGICAL_EXIT,
    BEHAVIOUR_DISCIPLINED_HOLD,
    FOMO_THRESHOLD_PCT,
    PANIC_SELL_HOURS,
    OVERTRADING_DAILY,
    CONCENTRATION_THRESHOLD,
)


class BehaviourContext:
    """
    Output of the Behaviour Engine.
    Passed to Prompt Builder.
    """
    def __init__(self):
        self.detected_pattern = None
        self.pattern_explanation = None
        self.dominant_weakness = None
        self.dominant_weakness_count = 0
        self.is_repeated_mistake = False
        self.coaching_priority = False
        self.behaviour_history = {}

    def to_dict(self):
        return {
            'detected_pattern': self.detected_pattern,
            'pattern_explanation': self.pattern_explanation,
            'dominant_weakness': self.dominant_weakness,
            'dominant_weakness_count': self.dominant_weakness_count,
            'is_repeated_mistake': self.is_repeated_mistake,
            'coaching_priority': self.coaching_priority,
        }


class BehaviourEngine:

    def __init__(self, user):
        self.user = user
        self.profile = BehaviourProfile.get_or_create_for_user(user)

    # ----------------------------------------------------------
    # BUY EVENT ANALYSIS
    # ----------------------------------------------------------
    def analyze_buy(self, stock, quantity, total_cost):
        """
        Analyze a buy trade for behavioral patterns.
        Returns BehaviourContext.
        """
        context = BehaviourContext()
        context.behaviour_history = self._get_behaviour_history()
        context.dominant_weakness = self.profile.get_dominant_weakness()

        # Detect FOMO
        if self._is_fomo_buy(stock):
            context.detected_pattern = BEHAVIOUR_FOMO_BUY
            context.pattern_explanation = (
                f"You bought {stock.symbol} when it was up "
                f"{stock.change_percent}% today. Buying after a large "
                f"single-day gain is a classic FOMO pattern — the smart "
                f"money often bought earlier. Always check fundamentals "
                f"before chasing a running stock."
            )
            self.profile.fomo_buy_count += 1

        # Detect overtrading
        if self._is_overtrading():
            context.detected_pattern = BEHAVIOUR_OVERTRADE
            context.pattern_explanation = (
                "You have made many trades today. Overtrading increases "
                "transaction costs and is often driven by emotion rather "
                "than research. Quality over quantity — a few well-researched "
                "trades beat many impulsive ones."
            )
            self.profile.overtrading_count += 1

        # Check if this is a repeated mistake
        if context.detected_pattern:
            count = self._get_pattern_count(context.detected_pattern)
            if count >= 2:
                context.is_repeated_mistake = True
                context.coaching_priority = True

        context.dominant_weakness = self.profile.get_dominant_weakness()
        context.dominant_weakness_count = self._get_dominant_count()
        self.profile.last_analysis_date = timezone.now().date()
        self.profile.dominant_weakness = context.dominant_weakness or ''
        self.profile.save()

        return context

    # ----------------------------------------------------------
    # SELL EVENT ANALYSIS
    # ----------------------------------------------------------
    def analyze_sell(self, stock, quantity, sell_price, avg_buy_price):
        """
        Analyze a sell trade for behavioral patterns.
        Returns BehaviourContext.
        """
        context = BehaviourContext()
        context.behaviour_history = self._get_behaviour_history()

        sell_price = float(sell_price)
        avg_buy_price = float(avg_buy_price)
        pnl_pct = ((sell_price - avg_buy_price) / avg_buy_price) * 100 if avg_buy_price else 0

        # Detect panic selling
        if self._is_panic_sell(stock, sell_price, avg_buy_price):
            context.detected_pattern = BEHAVIOUR_PANIC_SELL
            context.pattern_explanation = (
                f"You sold {stock.symbol} at a loss of "
                f"{abs(pnl_pct):.1f}% within a short time of buying. "
                f"This is panic selling — exiting because of fear rather "
                f"than a change in fundamentals. Ask yourself: has the "
                f"business changed, or just the price?"
            )
            self.profile.panic_sell_count += 1

        # Detect selling winner too early
        elif self._is_selling_winner_early(pnl_pct, stock):
            context.detected_pattern = BEHAVIOUR_SELL_WINNER_EARLY
            context.pattern_explanation = (
                f"You sold {stock.symbol} at only +{pnl_pct:.1f}% gain "
                f"while the stock still shows strong fundamentals. "
                f"Selling winners too early is a common mistake — it limits "
                f"your upside while letting losers run. Let quality stocks "
                f"compound over time."
            )
            self.profile.sell_winner_early_count += 1

        # Logical exit — reward good behaviour
        elif pnl_pct > 10:
            context.detected_pattern = BEHAVIOUR_LOGICAL_EXIT
            context.pattern_explanation = (
                f"You booked a solid +{pnl_pct:.1f}% gain on {stock.symbol}. "
                f"Well-timed exits based on targets rather than emotion "
                f"are a sign of disciplined investing."
            )
            self.profile.disciplined_hold_count += 1

        # Check if repeated mistake
        if context.detected_pattern and context.detected_pattern not in [
            BEHAVIOUR_LOGICAL_EXIT, BEHAVIOUR_DISCIPLINED_HOLD
        ]:
            count = self._get_pattern_count(context.detected_pattern)
            if count >= 2:
                context.is_repeated_mistake = True
                context.coaching_priority = True

        context.dominant_weakness = self.profile.get_dominant_weakness()
        context.dominant_weakness_count = self._get_dominant_count()
        self.profile.last_analysis_date = timezone.now().date()
        self.profile.dominant_weakness = context.dominant_weakness or ''
        self.profile.save()

        return context

    # ----------------------------------------------------------
    # PORTFOLIO ANALYSIS
    # ----------------------------------------------------------
    def analyze_portfolio(self):
        """
        Analyze overall portfolio for behavioral patterns.
        Returns BehaviourContext.
        """
        context = BehaviourContext()
        context.behaviour_history = self._get_behaviour_history()
        context.dominant_weakness = self.profile.get_dominant_weakness()
        context.dominant_weakness_count = self._get_dominant_count()

        # Check for poor diversification
        holdings = Holding.objects.filter(
            user=self.user
        ).select_related('stock')

        if holdings.count() > 0:
            total_invested = sum(
                float(h.avg_buy_price) * h.quantity for h in holdings
            )
            if total_invested > 0:
                for h in holdings:
                    invested = float(h.avg_buy_price) * h.quantity
                    pct = (invested / total_invested) * 100
                    if pct > CONCENTRATION_THRESHOLD:
                        context.detected_pattern = BEHAVIOUR_POOR_DIVERSIFICATION
                        context.pattern_explanation = (
                            f"{h.stock.symbol} makes up {pct:.0f}% of your "
                            f"portfolio — above the safe threshold of "
                            f"{CONCENTRATION_THRESHOLD}%. This concentration "
                            f"risk means one bad quarter could significantly "
                            f"hurt your total portfolio."
                        )
                        self.profile.poor_diversification_count += 1
                        self.profile.save()
                        break

        # Check dominant weakness — if repeated 3+ times, flag for coaching
        if context.dominant_weakness_count >= 3:
            context.coaching_priority = True
            context.is_repeated_mistake = True

        return context

    # ----------------------------------------------------------
    # DETECTION HELPERS
    # ----------------------------------------------------------
    def _is_fomo_buy(self, stock):
        """Stock up more than threshold % today = possible FOMO."""
        if stock.change_percent is None:
            return False
        return float(stock.change_percent) >= FOMO_THRESHOLD_PCT

    def _is_panic_sell(self, stock, sell_price, avg_buy_price):
        """Sold at a loss within PANIC_SELL_HOURS of buying."""
        if sell_price >= avg_buy_price:
            return False  # Not a loss — not panic selling

        cutoff = timezone.now() - timedelta(hours=PANIC_SELL_HOURS)
        recent_buy = Order.objects.filter(
            user=self.user,
            stock=stock,
            order_type='BUY',
            timestamp__gte=cutoff,
        ).exists()

        return recent_buy

    def _is_selling_winner_early(self, pnl_pct, stock):
        """
        Selling at small profit while stock still has strong fundamentals.
        Threshold: profit between 1% and 8% with good ROE.
        """
        if pnl_pct <= 1:
            return False
        if pnl_pct >= 15:
            return False  # 15%+ is a solid gain, not early

        # Only flag if stock fundamentals are still strong
        if stock.roe and float(stock.roe) > 15:
            return True
        if stock.pe_ratio and float(stock.pe_ratio) < 25:
            return True

        return False

    def _is_overtrading(self):
        """More than OVERTRADING_DAILY trades today."""
        today = timezone.now().date()
        today_trades = Order.objects.filter(
            user=self.user,
            timestamp__date=today,
        ).count()
        return today_trades >= OVERTRADING_DAILY

    # ----------------------------------------------------------
    # HISTORY & COUNTS
    # ----------------------------------------------------------
    def _get_behaviour_history(self):
        """Returns a summary of all behavioral counts."""
        return {
            'panic_sell_count': self.profile.panic_sell_count,
            'fomo_buy_count': self.profile.fomo_buy_count,
            'overtrading_count': self.profile.overtrading_count,
            'hold_loser_count': self.profile.hold_loser_count,
            'sell_winner_early_count': self.profile.sell_winner_early_count,
            'poor_diversification_count': self.profile.poor_diversification_count,
            'disciplined_hold_count': self.profile.disciplined_hold_count,
        }

    def _get_pattern_count(self, pattern):
        """Returns how many times a pattern has been detected."""
        mapping = {
            BEHAVIOUR_PANIC_SELL: self.profile.panic_sell_count,
            BEHAVIOUR_FOMO_BUY: self.profile.fomo_buy_count,
            BEHAVIOUR_OVERTRADE: self.profile.overtrading_count,
            BEHAVIOUR_HOLD_LOSER: self.profile.hold_loser_count,
            BEHAVIOUR_SELL_WINNER_EARLY: self.profile.sell_winner_early_count,
            BEHAVIOUR_POOR_DIVERSIFICATION: self.profile.poor_diversification_count,
        }
        return mapping.get(pattern, 0)

    def _get_dominant_count(self):
        """Returns the count of the dominant weakness."""
        weakness = self.profile.get_dominant_weakness()
        if not weakness:
            return 0
        return self._get_pattern_count(weakness)

    def get_coaching_summary(self):
        """
        Returns a summary for the Prompt Builder.
        Tells the LLM about the user's behavioral history.
        """
        history = self._get_behaviour_history()
        dominant = self.profile.get_dominant_weakness()
        dominant_count = self._get_dominant_count()

        if not any(history.values()):
            return {
                'summary': 'No behavioral patterns detected yet. This investor is new.',
                'dominant_weakness': None,
                'coaching_needed': False,
                'history': history,
            }

        coaching_needed = dominant_count >= 2

        summary_parts = []
        if history['panic_sell_count'] > 0:
            summary_parts.append(f"Panic sold {history['panic_sell_count']} time(s)")
        if history['fomo_buy_count'] > 0:
            summary_parts.append(f"FOMO bought {history['fomo_buy_count']} time(s)")
        if history['overtrading_count'] > 0:
            summary_parts.append(f"Overtraded {history['overtrading_count']} time(s)")
        if history['sell_winner_early_count'] > 0:
            summary_parts.append(f"Sold winners early {history['sell_winner_early_count']} time(s)")
        if history['disciplined_hold_count'] > 0:
            summary_parts.append(f"Made {history['disciplined_hold_count']} disciplined exit(s)")

        return {
            'summary': '. '.join(summary_parts) if summary_parts else 'No significant patterns yet.',
            'dominant_weakness': dominant,
            'dominant_weakness_count': dominant_count,
            'coaching_needed': coaching_needed,
            'history': history,
        }