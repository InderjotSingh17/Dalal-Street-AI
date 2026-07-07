# ============================================================
# DALAL STREET AI — MENTOR CONSTANTS
# Single source of truth for all mentor configuration
# ============================================================

# ------------------------------------------------------------
# KNOWLEDGE LEVELS
# ------------------------------------------------------------
KNOWLEDGE_BEGINNER = 'beginner'
KNOWLEDGE_INTERMEDIATE = 'intermediate'
KNOWLEDGE_ADVANCED = 'advanced'

KNOWLEDGE_LEVELS = [
    KNOWLEDGE_BEGINNER,
    KNOWLEDGE_INTERMEDIATE,
    KNOWLEDGE_ADVANCED,
]

# Level up after this many lessons
LESSONS_TO_INTERMEDIATE = 10
LESSONS_TO_ADVANCED = 25

# ------------------------------------------------------------
# EVENT TYPES
# ------------------------------------------------------------
EVENT_BUY = 'buy'
EVENT_SELL = 'sell'
EVENT_PORTFOLIO_VIEW = 'portfolio_view'
EVENT_DAILY_REPORT = 'daily_report'
EVENT_WEEKLY_REVIEW = 'weekly_review'

# ------------------------------------------------------------
# ANALYSIS PILLARS
# ------------------------------------------------------------
PILLAR_FUNDAMENTAL = 'fundamental'
PILLAR_VALUATION = 'valuation'
PILLAR_ENTRY = 'entry'
PILLAR_EXIT = 'exit'
PILLAR_PORTFOLIO = 'portfolio'
PILLAR_BEHAVIOURAL = 'behavioural'
PILLAR_EDUCATIONAL = 'educational'
PILLAR_RISK = 'risk'
PILLAR_SECTOR = 'sector'
PILLAR_PERFORMANCE = 'performance'

# Pillar selection map per event + knowledge level
PILLAR_MAP = {
    EVENT_BUY: {
        KNOWLEDGE_BEGINNER: [
            PILLAR_FUNDAMENTAL,
            PILLAR_VALUATION,
            PILLAR_PORTFOLIO,
            PILLAR_EDUCATIONAL,
        ],
        KNOWLEDGE_INTERMEDIATE: [
            PILLAR_FUNDAMENTAL,
            PILLAR_VALUATION,
            PILLAR_ENTRY,
            PILLAR_RISK,
            PILLAR_PORTFOLIO,
            PILLAR_EDUCATIONAL,
        ],
        KNOWLEDGE_ADVANCED: [
            PILLAR_FUNDAMENTAL,
            PILLAR_VALUATION,
            PILLAR_ENTRY,
            PILLAR_RISK,
            PILLAR_SECTOR,
            PILLAR_PORTFOLIO,
            PILLAR_EDUCATIONAL,
        ],
    },
    EVENT_SELL: {
        KNOWLEDGE_BEGINNER: [
            PILLAR_EXIT,
            PILLAR_BEHAVIOURAL,
            PILLAR_PORTFOLIO,
            PILLAR_EDUCATIONAL,
        ],
        KNOWLEDGE_INTERMEDIATE: [
            PILLAR_EXIT,
            PILLAR_BEHAVIOURAL,
            PILLAR_PERFORMANCE,
            PILLAR_PORTFOLIO,
            PILLAR_EDUCATIONAL,
        ],
        KNOWLEDGE_ADVANCED: [
            PILLAR_EXIT,
            PILLAR_BEHAVIOURAL,
            PILLAR_PERFORMANCE,
            PILLAR_RISK,
            PILLAR_PORTFOLIO,
            PILLAR_EDUCATIONAL,
        ],
    },
    EVENT_PORTFOLIO_VIEW: {
        KNOWLEDGE_BEGINNER: [
            PILLAR_PORTFOLIO,
            PILLAR_BEHAVIOURAL,
            PILLAR_EDUCATIONAL,
        ],
        KNOWLEDGE_INTERMEDIATE: [
            PILLAR_PORTFOLIO,
            PILLAR_BEHAVIOURAL,
            PILLAR_RISK,
            PILLAR_SECTOR,
            PILLAR_EDUCATIONAL,
        ],
        KNOWLEDGE_ADVANCED: [
            PILLAR_PORTFOLIO,
            PILLAR_BEHAVIOURAL,
            PILLAR_RISK,
            PILLAR_SECTOR,
            PILLAR_PERFORMANCE,
            PILLAR_EDUCATIONAL,
        ],
    },
}

# ------------------------------------------------------------
# BEHAVIOURAL PATTERNS
# ------------------------------------------------------------
BEHAVIOUR_PANIC_SELL = 'panic_selling'
BEHAVIOUR_FOMO_BUY = 'fomo_buying'
BEHAVIOUR_OVERTRADE = 'overtrading'
BEHAVIOUR_HOLD_LOSER = 'holding_losers'
BEHAVIOUR_SELL_WINNER_EARLY = 'selling_winners_early'
BEHAVIOUR_POOR_DIVERSIFICATION = 'poor_diversification'
BEHAVIOUR_LOGICAL_EXIT = 'logical_exit'
BEHAVIOUR_DISCIPLINED_HOLD = 'disciplined_hold'

# Thresholds for pattern detection
FOMO_THRESHOLD_PCT = 5.0       # stock up >5% same day = possible FOMO
PANIC_SELL_HOURS = 24          # sold within 24h of buying at a loss
OVERTRADING_DAILY = 5          # more than 5 trades in one day
CONCENTRATION_THRESHOLD = 50   # >50% in one stock = concentration risk

# ------------------------------------------------------------
# CONCEPT LIBRARY
# Every concept the mentor can teach
# key: unique identifier
# name: display name
# pillar: which pillar it belongs to
# levels: which knowledge levels it is appropriate for
# ------------------------------------------------------------
CONCEPT_LIBRARY = {
    # FUNDAMENTAL CONCEPTS
    'pe_ratio': {
        'name': 'P/E Ratio',
        'pillar': PILLAR_FUNDAMENTAL,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE, KNOWLEDGE_ADVANCED],
        'beginner': "P/E Ratio (Price to Earnings) tells you how much investors are paying for every ₹1 of profit a company makes. If TCS has a P/E of 30, investors pay ₹30 for every ₹1 TCS earns. Higher P/E usually means higher growth expectations.",
        'intermediate': "P/E Ratio should always be compared against industry peers and historical averages. A high P/E can be justified by strong earnings growth — this is where PEG ratio becomes useful.",
        'advanced': "Forward P/E uses estimated future earnings instead of trailing earnings. A stock with high trailing P/E but low forward P/E may be about to report strong results.",
    },
    'eps': {
        'name': 'EPS — Earnings Per Share',
        'pillar': PILLAR_FUNDAMENTAL,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE],
        'beginner': "EPS (Earnings Per Share) is the profit a company made divided by total shares. If Infosys earned ₹24,000 Cr and has 400 Cr shares, EPS = ₹60. Rising EPS over multiple quarters means the company is growing profitably.",
        'intermediate': "Consistent EPS growth above 15% annually is a strong signal of business quality. Watch for EPS dilution when companies issue new shares — it reduces value per existing shareholder.",
    },
    'roe': {
        'name': 'ROE — Return on Equity',
        'pillar': PILLAR_FUNDAMENTAL,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE, KNOWLEDGE_ADVANCED],
        'beginner': "ROE measures how efficiently a company uses your money to generate profit. ROE of 20% means for every ₹100 invested by shareholders, the company earns ₹20 profit. Above 15% is generally considered strong in India.",
        'intermediate': "ROE above 20% sustained over 5+ years is a hallmark of excellent businesses like HDFC Bank and Asian Paints. However, high ROE driven by excessive debt is misleading — always check D/E alongside ROE.",
        'advanced': "DuPont analysis breaks ROE into Net Margin × Asset Turnover × Leverage. This reveals whether ROE is driven by profitability, efficiency or debt — each has very different investment implications.",
    },
    'market_cap': {
        'name': 'Market Capitalisation',
        'pillar': PILLAR_FUNDAMENTAL,
        'levels': [KNOWLEDGE_BEGINNER],
        'beginner': "Market Cap = Stock Price × Total Shares. It tells you the total value of a company. Large cap (above ₹20,000 Cr) companies like RELIANCE are stable. Small cap (below ₹5,000 Cr) companies carry higher risk but higher growth potential.",
    },
    'pb_ratio': {
        'name': 'P/B Ratio',
        'pillar': PILLAR_VALUATION,
        'levels': [KNOWLEDGE_INTERMEDIATE, KNOWLEDGE_ADVANCED],
        'intermediate': "P/B (Price to Book) compares market price to the company's net assets. P/B below 1 means you are buying assets cheaper than their book value — potentially undervalued. Very high P/B means the market values intangibles like brand and IP heavily.",
        'advanced': "For asset-heavy industries like banking, P/B is the primary valuation metric. For asset-light businesses like IT services, P/B is less meaningful since their value lies in human capital and IP.",
    },
    'debt_to_equity': {
        'name': 'Debt to Equity Ratio',
        'pillar': PILLAR_RISK,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE],
        'beginner': "Debt to Equity shows how much debt a company has vs shareholder money. D/E of 0.5 means for every ₹1 of equity, the company has ₹0.50 debt. Low D/E companies like TCS and Infosys have almost zero debt — very safe.",
        'intermediate': "D/E must be interpreted by industry. Banks naturally have high D/E because they borrow to lend. For manufacturing companies, D/E above 1.5 starts becoming a concern during economic slowdowns.",
    },
    'dividend_yield': {
        'name': 'Dividend Yield',
        'pillar': PILLAR_FUNDAMENTAL,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE],
        'beginner': "Dividend Yield tells you what % of the stock price the company pays back to shareholders annually as cash dividends. A 3% yield on a ₹1,000 stock means ₹30 per share per year — paid without selling any shares.",
        'intermediate': "High dividend yield alone is not enough — check if the company has consistently maintained or grown dividends over 5+ years. A suddenly high yield can mean the stock price fell, not that dividends grew.",
    },

    # VALUATION CONCEPTS
    'margin_of_safety': {
        'name': 'Margin of Safety',
        'pillar': PILLAR_VALUATION,
        'levels': [KNOWLEDGE_INTERMEDIATE, KNOWLEDGE_ADVANCED],
        'intermediate': "Margin of Safety means buying a stock only when it trades significantly below your estimate of its intrinsic value. Benjamin Graham popularized this — if you think a stock is worth ₹100, only buy at ₹70 or below. The gap protects you from being wrong.",
        'advanced': "Intrinsic value estimation requires DCF (Discounted Cash Flow) analysis. For Indian investors, a simpler approach is comparing current P/E to historical average P/E and industry P/E to estimate if a margin of safety exists.",
    },

    # PORTFOLIO CONCEPTS
    'diversification': {
        'name': 'Diversification',
        'pillar': PILLAR_PORTFOLIO,
        'levels': [KNOWLEDGE_BEGINNER],
        'beginner': "Diversification means spreading investments across different stocks and sectors so one bad investment cannot destroy your portfolio. Own stocks from Banking, IT, Pharma, Energy — if one sector falls, others may hold. Never put all eggs in one basket.",
    },
    'position_sizing': {
        'name': 'Position Sizing',
        'pillar': PILLAR_PORTFOLIO,
        'levels': [KNOWLEDGE_INTERMEDIATE, KNOWLEDGE_ADVANCED],
        'intermediate': "Position sizing decides how much to invest in each stock. A common rule for beginners — no single stock should exceed 15-20% of total portfolio. This limits damage if one investment goes wrong.",
        'advanced': "Kelly Criterion is a mathematical formula for optimal position sizing based on win rate and risk-reward ratio. Most professional investors use a fractional Kelly (25-50%) to reduce volatility.",
    },
    'concentration_risk': {
        'name': 'Concentration Risk',
        'pillar': PILLAR_RISK,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE],
        'beginner': "Concentration risk means too much of your portfolio is in one stock or sector. If 60% of your portfolio is in RELIANCE and it falls 20%, your total portfolio falls 12%. Spread across stocks to reduce this risk.",
        'intermediate': "Sector concentration is equally dangerous. If 70% of your portfolio is in IT stocks and the IT sector faces headwinds, your entire portfolio suffers simultaneously.",
    },

    # BEHAVIOURAL CONCEPTS
    'fomo': {
        'name': 'FOMO — Fear Of Missing Out',
        'pillar': PILLAR_BEHAVIOURAL,
        'levels': [KNOWLEDGE_BEGINNER],
        'beginner': "FOMO makes you buy a stock after it has already risen sharply because you fear missing further gains. This is dangerous — you are buying after smart money already bought. By the time you hear about a big mover, you are often too late.",
    },
    'panic_selling': {
        'name': 'Panic Selling',
        'pillar': PILLAR_BEHAVIOURAL,
        'levels': [KNOWLEDGE_BEGINNER],
        'beginner': "Panic selling means selling in fear when prices fall — usually at exactly the wrong time. Markets always recover from temporary drops. Investors who sold during the COVID crash of March 2020 missed a 100% recovery within a year.",
    },
    'loss_aversion': {
        'name': 'Loss Aversion',
        'pillar': PILLAR_BEHAVIOURAL,
        'levels': [KNOWLEDGE_INTERMEDIATE],
        'intermediate': "Loss aversion means the pain of losing ₹10,000 feels twice as strong as the joy of gaining ₹10,000. This causes investors to hold losing stocks too long (hoping to break even) and sell winners too early. Recognize this bias in yourself.",
    },
    'rupee_cost_averaging': {
        'name': 'Rupee Cost Averaging',
        'pillar': PILLAR_PORTFOLIO,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE],
        'beginner': "Rupee Cost Averaging means investing a fixed amount regularly regardless of market conditions. When prices are low you buy more shares, when high you buy fewer. Over time your average cost is lower than if you tried to time the market.",
        'intermediate': "RCA removes emotional decision-making from investing. The biggest risk is stopping during market crashes — that is exactly when you should continue since you are buying quality stocks cheaply.",
    },

    # EXIT CONCEPTS
    'exit_strategy': {
        'name': 'Exit Strategy',
        'pillar': PILLAR_EXIT,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE],
        'beginner': "An exit strategy is a pre-planned decision about when you will sell. Good reasons to sell: fundamentals changed, stock became highly overvalued, better opportunity elsewhere. Bad reasons: price dropped temporarily, someone told you to sell.",
        'intermediate': "Systematic exits — selling a portion at pre-defined price targets — reduce emotional decision making. Selling 25% at +20%, another 25% at +40% locks in gains while keeping exposure to further upside.",
    },
    'stop_loss': {
        'name': 'Stop Loss',
        'pillar': PILLAR_RISK,
        'levels': [KNOWLEDGE_BEGINNER, KNOWLEDGE_INTERMEDIATE],
        'beginner': "A stop loss is a pre-set maximum loss you are willing to accept on a trade before exiting. Example: buy at ₹100, set stop loss at ₹90 — you exit if price falls to ₹90, limiting loss to 10%. This prevents small losses becoming catastrophic.",
        'intermediate': "Trailing stop loss moves up as the price rises, protecting profits. If you bought at ₹100 and price rose to ₹150, a 10% trailing stop exits at ₹135 — protecting ₹35 of profit even if price falls.",
    },
}

# Order in which concepts should be taught to beginners
CONCEPT_TEACHING_ORDER = [
    'market_cap',
    'pe_ratio',
    'eps',
    'diversification',
    'fomo',
    'panic_selling',
    'roe',
    'debt_to_equity',
    'dividend_yield',
    'concentration_risk',
    'exit_strategy',
    'stop_loss',
    'rupee_cost_averaging',
    'pb_ratio',
    'loss_aversion',
    'margin_of_safety',
    'position_sizing',
]

# ------------------------------------------------------------
# MENTOR CARD SCHEMA
# The exact JSON structure LLM must return for buy events
# ------------------------------------------------------------
BUY_CARD_SCHEMA = {
    "trade_quality_score": "integer 1-10",
    "verdict": "Excellent | Good | Acceptable | Questionable | Risky",
    "strengths": ["list of strings"],
    "weaknesses": ["list of strings"],
    "risk_level": "Low | Medium | High | Very High",
    "portfolio_impact": "string",
    "educational_insight": "string",
    "concept_key": "string — must be a key from CONCEPT_LIBRARY",
    "concept_name": "string",
    "concept_explanation": "string — beginner friendly",
    "behavioural_observation": "null or string",
    "improvement_suggestion": "null or string",
}

SELL_CARD_SCHEMA = {
    "exit_quality": "Excellent | Good | Acceptable | Questionable | Premature | Panic",
    "verdict": "string",
    "was_logical": "boolean",
    "analysis": "string",
    "behavioural_pattern": "null | panic_selling | fomo_buying | logical_exit | booking_profit_early | stop_loss | overdue_exit",
    "behavioural_explanation": "null or string",
    "lesson": "string",
    "concept_key": "string",
    "concept_name": "string",
    "concept_explanation": "string",
    "next_steps": "string",
}

PORTFOLIO_CARD_SCHEMA = {
    "health_score": "integer 1-100",
    "health_label": "Excellent | Good | Fair | Poor | Critical",
    "top_strength": "string",
    "top_concern": "string",
    "diversification_feedback": "string",
    "concentration_warning": "null or string",
    "cash_feedback": "string",
    "behavioural_patterns": ["list of detected pattern strings"],
    "three_action_items": ["string", "string", "string"],
    "concept_key": "string",
    "concept_name": "string",
    "concept_explanation": "string",
}

# ------------------------------------------------------------
# CACHE DURATIONS (in minutes)
# ------------------------------------------------------------
CACHE_PORTFOLIO_MINUTES = 30
CACHE_DAILY_REPORT_MINUTES = 1440  # 24 hours

# ------------------------------------------------------------
# LLM SETTINGS
# ------------------------------------------------------------
LLM_MODEL = 'gemini-2.5-flash'
LLM_MAX_RETRIES = 2
LLM_TEMPERATURE = 0.3  # Lower = more consistent, less creative