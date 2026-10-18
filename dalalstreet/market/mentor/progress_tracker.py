# ============================================================
# MODULE — PROGRESS TRACKER
# Measures whether decision quality (trade_quality_score) is
# improving over time, using past mentor cards already saved.
# Pure Python — no LLM call.
# ============================================================

from accounts.models import MentorCardCache


def get_decision_quality_trend(user):
    """
    Returns trend info based on trade_quality_score across past buy cards.
    """
    cards = MentorCardCache.objects.filter(
        user=user, event_type='buy'
    ).order_by('created_at')

    scores = []
    for c in cards:
        score = c.card_data.get('trade_quality_score')
        if isinstance(score, (int, float)):
            scores.append(score)

    if len(scores) < 4:
        return {
            'trend': 'not_enough_data',
            'scores': scores,
            'average': round(sum(scores) / len(scores), 1) if scores else None,
        }

    mid = len(scores) // 2
    first_half_avg = sum(scores[:mid]) / mid
    second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

    diff = second_half_avg - first_half_avg
    if diff > 0.5:
        trend = 'improving'
    elif diff < -0.5:
        trend = 'declining'
    else:
        trend = 'stable'

    return {
        'trend': trend,
        'scores': scores,
        'average': round(sum(scores) / len(scores), 1),
        'first_half_avg': round(first_half_avg, 1),
        'second_half_avg': round(second_half_avg, 1),
    }