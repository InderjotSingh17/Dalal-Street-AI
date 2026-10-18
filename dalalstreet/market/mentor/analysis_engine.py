# ============================================================
# MODULE — ANALYSIS ENGINE
# Converts EventContext + BehaviourContext into one flat list
# of structured signals. This is what Phase 7 will prioritize.
# ============================================================

class Signal:
    def __init__(self, factor, severity, detail, concept_key=None):
        self.factor = factor          # e.g. 'valuation', 'behaviour', 'concentration'
        self.severity = severity      # 'high' | 'medium' | 'low'
        self.detail = detail          # human-readable string
        self.concept_key = concept_key  # links to CONCEPT_LIBRARY, if applicable

    def __repr__(self):
        return f"<Signal {self.factor}/{self.severity}: {self.detail}>"


def build_signals(event_ctx, behaviour_ctx):
    """
    Takes EventContext + BehaviourContext, returns a flat list of Signal objects.
    No LLM involved — pure Python, fully testable.
    """
    signals = []

    # --- Valuation ---
    if event_ctx.pe_ratio:
        if event_ctx.pe_ratio > 50:
            signals.append(Signal('valuation', 'high', f"P/E of {event_ctx.pe_ratio:.1f} is very expensive", 'pe_ratio'))
        elif event_ctx.pe_ratio > 30:
            signals.append(Signal('valuation', 'medium', f"P/E of {event_ctx.pe_ratio:.1f} is moderately expensive", 'pe_ratio'))

    # --- Risk: debt ---
    if event_ctx.debt_to_equity and event_ctx.debt_to_equity > 1.5:
        signals.append(Signal('risk', 'high', f"D/E of {event_ctx.debt_to_equity:.1f} is high", 'debt_to_equity'))

    # --- Risk: concentration (portfolio-level) ---
    if event_ctx.sector_allocation:
        max_sector = max(event_ctx.sector_allocation, key=event_ctx.sector_allocation.get)
        max_pct = event_ctx.sector_allocation[max_sector]
        if max_pct > 60:
            signals.append(Signal('concentration', 'high', f"{max_sector} sector = {max_pct:.0f}% of portfolio", 'concentration_risk'))

    # --- Portfolio: low cash ---
    if event_ctx.invested_pct > 80:
        signals.append(Signal('portfolio', 'medium', f"Only {event_ctx.cash_pct:.0f}% cash remaining", 'diversification'))

    # --- Portfolio: too few holdings ---
    if event_ctx.num_holdings <= 2 and event_ctx.num_holdings > 0:
        signals.append(Signal('concentration', 'medium', "Very few holdings — high concentration risk", 'diversification'))

    # --- Entry timing ---
    if event_ctx.change_percent_today and event_ctx.change_percent_today > 5:
        signals.append(Signal('entry', 'medium', f"Bought after a {event_ctx.change_percent_today:.1f}% single-day gain", 'fomo'))

    # --- Behavioural (from BehaviourEngine, already prioritized to one pattern) ---
    if behaviour_ctx and behaviour_ctx.detected_pattern:
        severity = 'high' if behaviour_ctx.is_repeated_mistake else 'medium'
        signals.append(Signal('behaviour', severity, behaviour_ctx.pattern_explanation, behaviour_ctx.detected_pattern))

    return signals