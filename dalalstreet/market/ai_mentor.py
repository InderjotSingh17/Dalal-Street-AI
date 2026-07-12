import google.generativeai as genai
from django.conf import settings
from portfolio.models import Holding, Order
from accounts.models import UserProfile


def configure_gemini():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(model_name='gemini-3.5-flash')


def get_stock_context(stock):
    return f"""
Stock: {stock.symbol} — {stock.company_name}
Sector: {stock.sector or 'Unknown'}
Current Price: ₹{stock.current_price}
Previous Close: ₹{stock.previous_close}
Change Today: {stock.change_percent}%
Day High: ₹{stock.day_high}
Day Low: ₹{stock.day_low}
52W High: ₹{stock.week52_high}
52W Low: ₹{stock.week52_low}
Market Cap: ₹{stock.market_cap} ({('Large Cap' if stock.market_cap > 200000000000 else 'Mid Cap' if stock.market_cap > 50000000000 else 'Small Cap') if stock.market_cap else 'Unknown'})
P/E Ratio: {stock.pe_ratio or 'N/A'}
EPS: ₹{stock.eps or 'N/A'}
P/B Ratio: {stock.pb_ratio or 'N/A'}
ROE: {stock.roe or 'N/A'}%
Debt to Equity: {stock.debt_to_equity or 'N/A'}
Dividend Yield: {stock.dividend_yield or 'N/A'}%
Book Value: ₹{stock.book_value or 'N/A'}
Volume: {stock.volume or 'N/A'}
"""


def get_portfolio_context(user):
    profile = UserProfile.objects.get(user=user)
    holdings = Holding.objects.filter(user=user).select_related('stock')
    orders = Order.objects.filter(user=user).order_by('-timestamp')[:20]

    total_invested = sum(float(h.avg_buy_price) * h.quantity for h in holdings)
    total_current = sum(float(h.stock.current_price) * h.quantity for h in holdings)
    total_pnl = total_current - total_invested

    holdings_text = ""
    for h in holdings:
        pnl = (float(h.stock.current_price) - float(h.avg_buy_price)) * h.quantity
        pnl_pct = ((float(h.stock.current_price) - float(h.avg_buy_price)) / float(h.avg_buy_price)) * 100 if h.avg_buy_price else 0
        holdings_text += f"- {h.stock.symbol}: {h.quantity} shares, avg buy ₹{h.avg_buy_price}, current ₹{h.stock.current_price}, P&L ₹{pnl:.0f} ({pnl_pct:+.1f}%), sector: {h.stock.sector or 'Unknown'}\n"

    sectors = {}
    for h in holdings:
        sector = h.stock.sector or 'Unknown'
        invested = float(h.avg_buy_price) * h.quantity
        sectors[sector] = sectors.get(sector, 0) + invested

    sector_text = ""
    for sector, amount in sectors.items():
        pct = (amount / total_invested * 100) if total_invested > 0 else 0
        sector_text += f"- {sector}: {pct:.1f}%\n"

    recent_trades = ""
    for o in orders[:10]:
        recent_trades += f"- {o.order_type} {o.quantity}x {o.stock.symbol} @ ₹{o.price} on {o.timestamp.strftime('%d %b')}\n"

    return f"""
Cash Balance: ₹{profile.balance:,.0f}
Total Invested: ₹{total_invested:,.0f}
Current Value: ₹{total_current:,.0f}
Total P&L: ₹{total_pnl:,.0f}
Number of stocks: {holdings.count()}

Holdings:
{holdings_text or 'None'}

Sector Allocation:
{sector_text or 'None'}

Recent Trades:
{recent_trades or 'None'}
"""


def analyze_buy(user, stock, quantity, total_cost):
    """Called automatically when user buys a stock"""
    model = configure_gemini()
    portfolio = get_portfolio_context(user)
    stock_info = get_stock_context(stock)

    prompt = f"""You are an experienced Indian stock market mentor. A beginner investor just bought {quantity} shares of {stock.symbol} at ₹{stock.current_price} (total ₹{total_cost:.0f}).

STOCK DATA:
{stock_info}

PORTFOLIO AFTER THIS TRADE:
{portfolio}

Analyze this trade and generate a Mentor Card in this EXACT JSON format (respond with ONLY valid JSON, no markdown):
{{
  "trade_quality_score": <number 1-10>,
  "verdict": "<one of: Excellent, Good, Acceptable, Questionable, Risky>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "risk_level": "<Low, Medium, High, Very High>",
  "educational_insight": "<2-3 sentences teaching something important about this trade in beginner-friendly language>",
  "concept_learned": "<name of one investing concept this trade teaches>",
  "concept_explanation": "<explain this concept in 2 sentences, use Indian examples>",
  "behavioral_warning": "<null or a warning if the user might be FOMO buying, panic buying etc>",
  "portfolio_impact": "<one sentence on how this changes the portfolio composition>"
}}

Rules:
- NEVER say the stock will go up or down
- NEVER guarantee profits
- Focus on EDUCATION and REASONING
- Be specific — use actual numbers from the data
- Be encouraging but honest
- Write for a complete beginner"""

    try:
        response = model.generate_content(prompt)
        import json
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {
            "trade_quality_score": 5,
            "verdict": "Acceptable",
            "strengths": [f"You invested in {stock.symbol}, a well-known NSE stock"],
            "weaknesses": ["Analysis unavailable — check your internet connection"],
            "risk_level": "Medium",
            "educational_insight": f"You bought {stock.symbol} at ₹{stock.current_price}. Always research a stock's P/E ratio, sector, and market cap before buying.",
            "concept_learned": "Fundamental Analysis",
            "concept_explanation": "Fundamental analysis means evaluating a company's financial health — profits, debt, and growth — to decide if its stock is worth buying.",
            "behavioral_warning": None,
            "portfolio_impact": "This trade has been added to your portfolio."
        }


def analyze_sell(user, stock, quantity, sell_price, avg_buy_price):
    """Called automatically when user sells a stock"""
    model = configure_gemini()
    portfolio = get_portfolio_context(user)
    stock_info = get_stock_context(stock)

    pnl = (float(sell_price) - float(avg_buy_price)) * quantity
    pnl_pct = ((float(sell_price) - float(avg_buy_price)) / float(avg_buy_price)) * 100

    prompt = f"""You are an experienced Indian stock market mentor. A beginner investor just sold {quantity} shares of {stock.symbol}.

TRADE DETAILS:
- Sold at: ₹{sell_price}
- Average buy price: ₹{avg_buy_price}
- P&L: ₹{pnl:.0f} ({pnl_pct:+.1f}%)
- Outcome: {'PROFIT' if pnl > 0 else 'LOSS'}

STOCK DATA:
{stock_info}

PORTFOLIO AFTER THIS TRADE:
{portfolio}

Analyze this exit and generate a Mentor Card in this EXACT JSON format (respond with ONLY valid JSON, no markdown):
{{
  "exit_quality": "<Excellent, Good, Acceptable, Questionable, Premature, Panic>",
  "verdict": "<one sentence verdict on this exit decision>",
  "was_logical": <true or false>,
  "analysis": "<2-3 sentences analyzing whether this was a good exit — consider the stock fundamentals, P&L, and timing>",
  "behavioral_pattern": "<null or detected pattern: panic_selling, booking_profit_early, logical_exit, stop_loss, overdue_exit>",
  "behavioral_explanation": "<if behavioral pattern detected, explain what it means and how to improve>",
  "lesson": "<the most important lesson from this trade>",
  "concept_learned": "<investing concept this teaches>",
  "concept_explanation": "<explain in 2 sentences with Indian example>",
  "next_steps": "<one actionable suggestion for the investor>"
}}

Rules:
- NEVER say the stock will go up or down
- Be honest — if it was panic selling, say so kindly
- Always explain WHY, not just WHAT
- Use actual numbers in your analysis
- Be encouraging even when pointing out mistakes"""

    try:
        response = model.generate_content(prompt)
        import json
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {
            "exit_quality": "Acceptable",
            "verdict": f"You exited {stock.symbol} with a {'profit' if pnl > 0 else 'loss'} of ₹{abs(pnl):.0f}.",
            "was_logical": True,
            "analysis": f"You sold {stock.symbol} at ₹{sell_price} vs your buy price of ₹{avg_buy_price}. Every trade is a learning opportunity.",
            "behavioral_pattern": None,
            "behavioral_explanation": None,
            "lesson": "Always have a clear reason for selling — either the fundamentals changed or you reached your target.",
            "concept_learned": "Exit Strategy",
            "concept_explanation": "An exit strategy is a pre-planned set of conditions under which you will sell a stock. Having one prevents emotional decisions.",
            "next_steps": "Review why you bought this stock and whether your original thesis played out."
        }


def analyze_portfolio(user):
    """Called when user views portfolio page"""
    model = configure_gemini()
    portfolio = get_portfolio_context(user)

    prompt = f"""You are an experienced Indian stock market mentor reviewing a beginner's portfolio.

PORTFOLIO DATA:
{portfolio}

Generate a Portfolio Health Report in this EXACT JSON format (respond with ONLY valid JSON, no markdown):
{{
  "health_score": <number 1-100>,
  "health_label": "<Excellent, Good, Fair, Poor, Critical>",
  "top_strength": "<the best thing about this portfolio>",
  "top_concern": "<the biggest risk or weakness>",
  "diversification_feedback": "<specific feedback on sector and stock diversification>",
  "concentration_risk": "<null or which stock/sector is dangerously concentrated>",
  "cash_feedback": "<feedback on cash vs invested ratio>",
  "behavioral_patterns": ["<pattern 1 if detected>"],
  "three_action_items": ["<action 1>", "<action 2>", "<action 3>"],
  "learning_tip": "<one investing concept the user should learn based on their portfolio>"
}}

Be specific — use actual stock names, percentages and amounts from the data above."""

    try:
        response = model.generate_content(prompt)
        import json
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return None

def ask_ai_mentor(user, user_message, chat_history=None):
    """Conversational chat — used by the AI Chat page"""
    model = configure_gemini()
    portfolio = get_portfolio_context(user)

    history_text = ""
    if chat_history:
        for msg in chat_history[-10:]:
            role = "User" if msg.get('role') == 'user' else "Mentor"
            history_text += f"{role}: {msg.get('content', '')}\n"

    prompt = f"""You are an experienced, friendly Indian stock market mentor chatting with a beginner investor on Dalal Street AI.

USER'S PORTFOLIO:
{portfolio}

RECENT CONVERSATION:
{history_text or 'This is the start of the conversation.'}

USER'S NEW MESSAGE:
{user_message}

Respond conversationally and helpfully, using the user's actual portfolio data where relevant.

Rules:
- NEVER say a stock will go up or down
- NEVER guarantee profits or give direct buy/sell orders — teach reasoning instead
- Reference actual numbers from their portfolio when relevant
- Keep the tone warm and encouraging, like a patient mentor
- Keep responses concise — 3-5 sentences unless the question needs more detail
- Use Indian market context and examples where helpful"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI MENTOR CHAT ERROR: {e}")
        return "Sorry, I'm having trouble connecting right now. Please try again in a moment."