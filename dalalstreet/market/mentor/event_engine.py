# ============================================================
# MODULE 4 — EVENT ENGINE
# Single entry point for all mentor events.
# Gathers raw data and returns structured EventContext.
# No analysis happens here — only data collection.
# ============================================================

from portfolio.models import Holding, Order
from accounts.models import UserProfile
from market.mentor.constants import (
    EVENT_BUY,
    EVENT_SELL,
    EVENT_PORTFOLIO_VIEW,
    KNOWLEDGE_BEGINNER,
)


class EventContext:
    """
    Structured data object passed to all downstream modules.
    Contains everything needed for analysis — no module
    should query the database independently after this.
    """

    def __init__(self):
        # Event metadata
        self.event_type = None
        self.timestamp = None

        # User context
        self.user = None
        self.username = None
        self.balance = 0
        self.knowledge_level = KNOWLEDGE_BEGINNER
        self.total_trades_ever = 0
        self.is_first_trade = False

        # Stock context (for buy/sell events)
        self.stock = None
        self.stock_symbol = None
        self.stock_name = None
        self.stock_sector = None
        self.current_price = 0
        self.change_percent_today = 0
        self.pe_ratio = None
        self.eps = None
        self.roe = None
        self.pb_ratio = None
        self.debt_to_equity = None
        self.market_cap = 0
        self.week52_high = 0
        self.week52_low = 0
        self.dividend_yield = None
        self.day_high = 0
        self.day_low = 0
        self.volume = 0

        # Trade context (for buy/sell events)
        self.quantity = 0
        self.trade_price = 0
        self.total_trade_value = 0
        self.avg_buy_price = 0      # for sell events
        self.pnl = 0                # for sell events
        self.pnl_pct = 0            # for sell events

        # Portfolio context
        self.total_invested = 0
        self.total_current_value = 0
        self.total_pnl = 0
        self.num_holdings = 0
        self.holdings_data = []     # list of dicts
        self.sector_allocation = {} # sector -> % dict
        self.cash_pct = 0           # % of total in cash
        self.invested_pct = 0       # % of total invested

        # Market cap category
        self.market_cap_category = 'Unknown'

    def to_summary(self):
        """
        Returns a human-readable summary string for the Prompt Builder.
        """
        lines = []

        if self.event_type == EVENT_BUY:
            lines.append(f"EVENT: User bought {self.quantity} shares of {self.stock_symbol} at ₹{self.trade_price:.2f} (total ₹{self.total_trade_value:.0f})")
            lines.append(f"Is first trade ever: {self.is_first_trade}")

        elif self.event_type == EVENT_SELL:
            direction = 'PROFIT' if self.pnl >= 0 else 'LOSS'
            lines.append(f"EVENT: User sold {self.quantity} shares of {self.stock_symbol} at ₹{self.trade_price:.2f}")
            lines.append(f"Avg buy price: ₹{self.avg_buy_price:.2f} | P&L: ₹{self.pnl:.0f} ({self.pnl_pct:+.1f}%) — {direction}")

        elif self.event_type == EVENT_PORTFOLIO_VIEW:
            lines.append("EVENT: User opened portfolio page")

        if self.stock:
            lines.append(f"\nSTOCK: {self.stock_symbol} — {self.stock_name}")
            lines.append(f"Sector: {self.stock_sector or 'Unknown'} | Market Cap Category: {self.market_cap_category}")
            lines.append(f"Price: ₹{self.current_price} | Today: {self.change_percent_today:+.2f}%")
            lines.append(f"52W Range: ₹{self.week52_low} — ₹{self.week52_high}")
            lines.append(f"P/E: {self.pe_ratio or 'N/A'} | EPS: {self.eps or 'N/A'} | ROE: {self.roe or 'N/A'}%")
            lines.append(f"P/B: {self.pb_ratio or 'N/A'} | D/E: {self.debt_to_equity or 'N/A'} | Div Yield: {self.dividend_yield or 'N/A'}%")

        lines.append(f"\nPORTFOLIO:")
        lines.append(f"Cash: ₹{self.balance:,.0f} ({self.cash_pct:.1f}%) | Invested: ₹{self.total_invested:,.0f} ({self.invested_pct:.1f}%)")
        lines.append(f"Current value: ₹{self.total_current_value:,.0f} | Total P&L: ₹{self.total_pnl:,.0f}")
        lines.append(f"Holdings: {self.num_holdings} stocks")

        if self.holdings_data:
            lines.append("\nHOLDINGS:")
            for h in self.holdings_data:
                lines.append(
                    f"  {h['symbol']}: {h['quantity']} shares | "
                    f"Avg ₹{h['avg_buy_price']:.0f} | "
                    f"Current ₹{h['current_price']:.0f} | "
                    f"P&L ₹{h['pnl']:.0f} ({h['pnl_pct']:+.1f}%) | "
                    f"Sector: {h['sector']}"
                )

        if self.sector_allocation:
            lines.append("\nSECTOR ALLOCATION:")
            for sector, pct in self.sector_allocation.items():
                lines.append(f"  {sector}: {pct:.1f}%")

        return '\n'.join(lines)


class EventEngine:

    def __init__(self, user):
        self.user = user

    def build_buy_context(self, stock, quantity, total_cost):
        """Called from buy_stock view after a successful purchase."""
        context = EventContext()
        context.event_type = EVENT_BUY
        context.user = self.user

        self._fill_user_context(context)
        self._fill_stock_context(context, stock)
        self._fill_portfolio_context(context)

        context.quantity = quantity
        context.trade_price = float(stock.current_price)
        context.total_trade_value = float(total_cost)

        # Check if first trade
        total_orders = Order.objects.filter(user=self.user).count()
        context.total_trades_ever = total_orders
        context.is_first_trade = (total_orders == 1)

        return context

    def build_sell_context(self, stock, quantity, sell_price, avg_buy_price):
        """Called from sell_stock view after a successful sale."""
        context = EventContext()
        context.event_type = EVENT_SELL
        context.user = self.user

        self._fill_user_context(context)
        self._fill_stock_context(context, stock)
        self._fill_portfolio_context(context)

        context.quantity = quantity
        context.trade_price = float(sell_price)
        context.total_trade_value = float(sell_price) * quantity
        context.avg_buy_price = float(avg_buy_price)

        # Calculate P&L
        context.pnl = (float(sell_price) - float(avg_buy_price)) * quantity
        context.pnl_pct = (
            (float(sell_price) - float(avg_buy_price)) / float(avg_buy_price) * 100
            if avg_buy_price else 0
        )

        total_orders = Order.objects.filter(user=self.user).count()
        context.total_trades_ever = total_orders

        return context

    def build_portfolio_context(self):
        """Called from portfolio view."""
        context = EventContext()
        context.event_type = EVENT_PORTFOLIO_VIEW
        context.user = self.user

        self._fill_user_context(context)
        self._fill_portfolio_context(context)

        total_orders = Order.objects.filter(user=self.user).count()
        context.total_trades_ever = total_orders

        return context

    # ----------------------------------------------------------
    # PRIVATE HELPERS
    # ----------------------------------------------------------
    def _fill_user_context(self, context):
        profile = UserProfile.objects.get(user=self.user)
        context.username = self.user.username
        context.balance = float(profile.balance)

        try:
            from accounts.models import LearningProfile
            lp = LearningProfile.get_or_create_for_user(self.user)
            context.knowledge_level = lp.knowledge_level
        except Exception:
            context.knowledge_level = 'beginner'

    def _fill_stock_context(self, context, stock):
        context.stock = stock
        context.stock_symbol = stock.symbol
        context.stock_name = stock.company_name
        context.stock_sector = stock.sector or 'Unknown'
        context.current_price = float(stock.current_price)
        context.change_percent_today = float(stock.change_percent) if stock.change_percent else 0
        context.pe_ratio = float(stock.pe_ratio) if stock.pe_ratio else None
        context.eps = float(stock.eps) if stock.eps else None
        context.roe = float(stock.roe) if stock.roe else None
        context.pb_ratio = float(stock.pb_ratio) if stock.pb_ratio else None
        context.debt_to_equity = float(stock.debt_to_equity) if stock.debt_to_equity else None
        context.market_cap = stock.market_cap or 0
        context.week52_high = float(stock.week52_high) if stock.week52_high else 0
        context.week52_low = float(stock.week52_low) if stock.week52_low else 0
        context.dividend_yield = float(stock.dividend_yield) if stock.dividend_yield else None
        context.day_high = float(stock.day_high) if stock.day_high else 0
        context.day_low = float(stock.day_low) if stock.day_low else 0
        context.volume = stock.volume or 0

        # Market cap category
        if context.market_cap > 200000000000:
            context.market_cap_category = 'Large Cap'
        elif context.market_cap > 50000000000:
            context.market_cap_category = 'Mid Cap'
        elif context.market_cap > 0:
            context.market_cap_category = 'Small Cap'
        else:
            context.market_cap_category = 'Unknown'

    def _fill_portfolio_context(self, context):
        holdings = Holding.objects.filter(
            user=self.user
        ).select_related('stock')

        total_invested = 0
        total_current = 0
        holdings_data = []
        sector_totals = {}

        for h in holdings:
            invested = float(h.avg_buy_price) * h.quantity
            current = float(h.stock.current_price) * h.quantity
            pnl = current - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0

            total_invested += invested
            total_current += current

            sector = h.stock.sector or 'Unknown'
            sector_totals[sector] = sector_totals.get(sector, 0) + invested

            holdings_data.append({
                'symbol': h.stock.symbol,
                'company': h.stock.company_name,
                'sector': sector,
                'quantity': h.quantity,
                'avg_buy_price': float(h.avg_buy_price),
                'current_price': float(h.stock.current_price),
                'invested': invested,
                'current_value': current,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
            })

        context.total_invested = total_invested
        context.total_current_value = total_current
        context.total_pnl = total_current - total_invested
        context.num_holdings = len(holdings_data)
        context.holdings_data = holdings_data

        # Sector allocation as percentages
        if total_invested > 0:
            context.sector_allocation = {
                sector: (amount / total_invested * 100)
                for sector, amount in sector_totals.items()
            }

        # Cash vs invested ratio
        total_portfolio = context.balance + total_current
        if total_portfolio > 0:
            context.cash_pct = (context.balance / total_portfolio) * 100
            context.invested_pct = (total_current / total_portfolio) * 100