# ============================================================
# MODULE — PRIORITIZER
# Takes the signal list from analysis_engine + the user's
# learning/behaviour history, picks ONE thing to teach.
# Deterministic. No LLM call.
# ============================================================

SEVERITY_WEIGHT = {'high': 3, 'medium': 2, 'low': 1}


def prioritize(signals, learning_profile, behaviour_profile):
    """
    Returns a single chosen Signal (or None if no signals).
    Priority order:
    1. Behaviour signal marked as repeated mistake -> always wins
    2. Signal tied to a concept never taught before
    3. Highest severity signal remaining
    """
    if not signals:
        return None

    taught = set(getattr(learning_profile, 'concepts_taught', []) or [])

    # 1. Repeated behavioural mistake always wins
    for s in signals:
        if s.factor == 'behaviour' and s.severity == 'high':
            return s

    # 2. Never-taught concept beats everything else
    never_taught = [s for s in signals if s.concept_key and s.concept_key not in taught]
    if never_taught:
        never_taught.sort(key=lambda s: SEVERITY_WEIGHT.get(s.severity, 0), reverse=True)
        return never_taught[0]

    # 3. Otherwise, highest severity overall
    signals_sorted = sorted(signals, key=lambda s: SEVERITY_WEIGHT.get(s.severity, 0), reverse=True)
    return signals_sorted[0]