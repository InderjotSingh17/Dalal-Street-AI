from portfolio.models import Holding, Order
from django.utils import timezone
from datetime import timedelta


def get_diversification_score(user):
    holdings = Holding.objects.filter(user=user).select_related('stock')
    if not holdings:
        return {
            'score': 0,
            'label': 'No holdings',
            'color': 'grey',
            'message': 'You have no stocks yet. Start investing to build a diversified portfolio.',
            'tips': ['Buy stocks from at least 3 different sectors to reduce risk.']
        }

    total_invested = sum(float(h.avg_buy_price) * h.quantity for h in holdings)
    if total_invested == 0:
        return {'score': 0, 'label': 'No data', 'color': 'grey', 'message': '', 'tips': []}

    # Check concentration in single stock
    max_concentration = 0
    most_concentrated = None
    for h in holdings:
        invested = float(h.avg_buy_price) * h.quantity
        pct = (invested / total_invested) * 100
        if pct > max_concentration:
            max_concentration = pct
            most_concentrated = h.stock.symbol

    # Check sector diversity
    sectors = set()
    for h in holdings:
        if h.stock.sector:
            sectors.add(h.stock.sector)

    num_stocks = holdings.count()
    num_sectors = len(sectors)

    # Score calculation
    score = 100
    tips = []

    if max_concentration > 70:
        score -= 40
        tips.append(f'{most_concentrated} makes up {max_concentration:.0f}% of your portfolio. Consider spreading across more stocks.')
    elif max_concentration > 50:
        score -= 20
        tips.append(f'{most_concentrated} makes up {max_concentration:.0f}% of your portfolio. A bit concentrated — consider diversifying.')

    if num_stocks < 3:
        score -= 20
        tips.append('You own fewer than 3 stocks. A healthy portfolio typically has 5-10 stocks.')
    elif num_stocks < 5:
        score -= 10
        tips.append('Consider adding more stocks to spread your risk further.')

    if num_sectors < 2:
        score -= 20
        tips.append('All your stocks are in the same sector. Invest across different sectors like IT, Banking, Pharma.')
    elif num_sectors < 3:
        score -= 10
        tips.append(f'You are in {num_sectors} sectors. Try to cover at least 3-4 different sectors.')

    score = max(0, min(100, score))

    if score >= 75:
        label, color = 'Well diversified', 'green'
    elif score >= 50:
        label, color = 'Moderately diversified', 'yellow'
    elif score >= 25:
        label, color = 'Poorly diversified', 'orange'
    else:
        label, color = 'Very concentrated', 'red'

    if not tips:
        tips.append('Great job! Your portfolio is well diversified across stocks and sectors.')

    return {
        'score': score,
        'label': label,
        'color': color,
        'message': f'You own {num_stocks} stocks across {num_sectors} sectors.',
        'tips': tips,
        'max_concentration': round(max_concentration, 1),
        'most_concentrated': most_concentrated,
        'num_stocks': num_stocks,
        'num_sectors': num_sectors,
    }


def get_risk_level(user):
    holdings = Holding.objects.filter(user=user).select_related('stock')
    from accounts.models import UserProfile
    profile = UserProfile.objects.get(user=user)

    if not holdings:
        return {'level': 'Low', 'color': 'green', 'message': 'No holdings. Your cash is safe but not growing.'}

    total_value = float(profile.balance) + sum(
        float(h.stock.current_price) * h.quantity for h in holdings
    )
    invested = sum(float(h.avg_buy_price) * h.quantity for h in holdings)
    invested_pct = (invested / total_value * 100) if total_value > 0 else 0

    if invested_pct > 80:
        return {
            'level': 'High',
            'color': 'red',
            'message': f'You have invested {invested_pct:.0f}% of your total portfolio. Keep some cash for opportunities.',
            'invested_pct': round(invested_pct, 1)
        }
    elif invested_pct > 50:
        return {
            'level': 'Medium',
            'color': 'yellow',
            'message': f'You have invested {invested_pct:.0f}% of your portfolio. Balanced approach.',
            'invested_pct': round(invested_pct, 1)
        }
    else:
        return {
            'level': 'Low',
            'color': 'green',
            'message': f'You have invested {invested_pct:.0f}% of your portfolio. Lots of cash available.',
            'invested_pct': round(invested_pct, 1)
        }


def get_behavioral_insights(user):
    insights = []
    now = timezone.now()
    recent_orders = Order.objects.filter(
        user=user,
        timestamp__gte=now - timedelta(days=7)
    ).select_related('stock').order_by('-timestamp')

    # Detect panic selling — sold within 24h of buying at a loss
    buy_times = {}
    for order in recent_orders:
        if order.order_type == 'BUY':
            buy_times[order.stock.symbol] = order

    for order in recent_orders:
        if order.order_type == 'SELL' and order.stock.symbol in buy_times:
            buy_order = buy_times[order.stock.symbol]
            time_diff = buy_order.timestamp - order.timestamp
            if abs(time_diff.total_seconds()) < 86400:
                if float(order.price) < float(buy_order.price):
                    insights.append({
                        'type': 'warning',
                        'icon': '😰',
                        'title': 'Panic selling detected',
                        'message': f'You bought {order.stock.symbol} at ₹{buy_order.price} and sold at ₹{order.price} within 24 hours. Panic selling locks in losses — great investors hold through short-term volatility.',
                    })

    # Detect FOMO — bought after large single day gain
    for order in recent_orders:
        if order.order_type == 'BUY':
            if float(order.stock.change_percent) > 5:
                insights.append({
                    'type': 'warning',
                    'icon': '🚨',
                    'title': 'Possible FOMO buy',
                    'message': f'You bought {order.stock.symbol} when it was up {order.stock.change_percent}% in a single day. Buying after a big run-up can mean you are buying at the top. Always check fundamentals before buying.',
                })

    # Positive — held through volatility
    holdings = Holding.objects.filter(user=user).select_related('stock')
    profitable = [h for h in holdings if float(h.stock.current_price) > float(h.avg_buy_price)]
    if len(profitable) > 0:
        insights.append({
            'type': 'success',
            'icon': '💪',
            'title': 'Staying disciplined',
            'message': f'You are holding {len(profitable)} profitable position{"s" if len(profitable) > 1 else ""}. Staying patient with winners is the mark of a disciplined investor.',
        })

    # No trading activity
    if not recent_orders:
        insights.append({
            'type': 'info',
            'icon': '📊',
            'title': 'No recent activity',
            'message': 'You have not traded in the last 7 days. Review the market and look for opportunities.',
        })

    return insights


def get_portfolio_tips(user):
    tips = []
    holdings = Holding.objects.filter(user=user).select_related('stock')

    if not holdings:
        tips.append({
            'icon': '🚀',
            'tip': 'Start by buying 2-3 large-cap stocks like RELIANCE, TCS or HDFCBANK to build a solid foundation.'
        })
        return tips

    # Check for high PE stocks
    high_pe = [h for h in holdings if h.stock.pe_ratio and float(h.stock.pe_ratio) > 50]
    if high_pe:
        symbols = ', '.join(h.stock.symbol for h in high_pe[:3])
        tips.append({
            'icon': '⚠️',
            'tip': f'{symbols} have a P/E ratio above 50. High P/E stocks carry more risk — make sure you understand why the market values them so highly.'
        })

    # Check for stocks with no sector data
    no_sector = [h for h in holdings if not h.stock.sector]
    if len(no_sector) > 2:
        tips.append({
            'icon': '📋',
            'tip': 'Research the sectors of your holdings so you can better understand your portfolio composition.'
        })

    # General tip based on number of holdings
    if holdings.count() == 1:
        tips.append({
            'icon': '🎯',
            'tip': 'You only own one stock. Diversify by adding stocks from different sectors to reduce concentration risk.'
        })

    tips.append({
        'icon': '📚',
        'tip': 'Review the P/E ratio and EPS of each stock you own. Understanding fundamentals helps you make better buy/sell decisions.'
    })

    return tips

def get_trade_coaching_tip(user, stock, order_type, quantity):
    tips = []

    if order_type == 'BUY':
        # P/E based tip
        if stock.pe_ratio:
            pe = float(stock.pe_ratio)
            if pe > 50:
                tips.append(f"{stock.symbol} has a high P/E of {pe:.0f}. This means the market expects strong future growth. High P/E stocks carry more risk if growth disappoints.")
            elif pe < 15:
                tips.append(f"{stock.symbol} has a low P/E of {pe:.0f}. This could mean it is undervalued — or the market expects slower growth. Always check the reason.")
            else:
                tips.append(f"{stock.symbol} has a P/E of {pe:.0f}, which is moderate. P/E compares price to earnings — lower generally means cheaper relative to profits.")

        # FOMO warning
        if stock.change_percent and float(stock.change_percent) > 5:
            tips.append(f"{stock.symbol} is up {stock.change_percent}% today. Be careful of buying after a big run-up — prices often correct after large single-day gains.")

        # First buy tip
        total_orders = Order.objects.filter(user=user).count()
        if total_orders <= 1:
            tips.append("Great first trade! Remember — investing is a long-term game. Don't panic if prices drop short-term.")

        # Quantity tip
        if quantity >= 10:
            tips.append(f"You bought {quantity} shares. Buying in larger quantities concentrates your risk in one stock. Make sure you are confident in this position.")

    elif order_type == 'SELL':
        # Check if selling at loss
        try:
            holding = Holding.objects.get(user=user, stock=stock)
            if float(stock.current_price) < float(holding.avg_buy_price):
                loss_pct = ((float(holding.avg_buy_price) - float(stock.current_price)) / float(holding.avg_buy_price)) * 100
                tips.append(f"You are selling {stock.symbol} at a {loss_pct:.1f}% loss. Selling at a loss locks it in permanently. Ask yourself — has the fundamental reason you bought changed?")
        except:
            pass

        tips.append("After selling, review why you bought this stock and whether your thesis played out. This reflection makes you a better investor.")

    return tips[0] if tips else "Every trade is a learning opportunity. Review the fundamentals of each stock you buy or sell."

def get_sector_allocation(user):
    holdings = Holding.objects.filter(user=user).select_related('stock')
    if not holdings:
        return []

    sector_data = {}
    total_invested = 0

    for h in holdings:
        invested = float(h.avg_buy_price) * h.quantity
        total_invested += invested
        sector = h.stock.sector or 'Unknown'
        sector_data[sector] = sector_data.get(sector, 0) + invested

    if total_invested == 0:
        return []

    result = []
    colors = ['#00d68f','#7c3aed','#f59e0b','#3b82f6','#ef4444','#10b981','#f97316','#8b5cf6','#06b6d4','#84cc16']
    for i, (sector, amount) in enumerate(sorted(sector_data.items(), key=lambda x: x[1], reverse=True)):
        result.append({
            'sector': sector,
            'amount': round(amount, 0),
            'percent': round((amount / total_invested) * 100, 1),
            'color': colors[i % len(colors)],
        })

    return result