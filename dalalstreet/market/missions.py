from django.utils import timezone
from portfolio.models import Mission, UserMission, Holding, Watchlist, Order

def complete_mission(user, profile, mission_key):
    try:
        mission = Mission.objects.get(mission_key=mission_key)
    except Mission.DoesNotExist:
        return False

    today = timezone.now().date()

    if mission.mission_type == 'DAILY':
        already_done = UserMission.objects.filter(
            user=user,
            mission=mission,
            completed=True,
            completed_date=today
        ).exists()
    else:
        already_done = UserMission.objects.filter(
            user=user,
            mission=mission,
            completed=True
        ).exists()

    if already_done:
        return False

    UserMission.objects.update_or_create(
        user=user,
        mission=mission,
        defaults={'completed': True, 'completed_date': today}
    )
    profile.add_xp(mission.xp_reward)
    return True

def check_missions_on_trade(user, profile, quantity):
    completed = []

    # First trade
    total_orders = Order.objects.filter(user=user).count()
    if total_orders == 1:
        if complete_mission(user, profile, 'first_trade'):
            completed.append('First Steps')

    # Daily trade
    if complete_mission(user, profile, 'daily_trade'):
        completed.append('Daily Trader')

    # Big buy
    if quantity >= 10:
        if complete_mission(user, profile, 'big_buy'):
            completed.append('Big Buyer')

    # Portfolio builder
    total_invested = sum(
        float(h.avg_buy_price) * h.quantity
        for h in Holding.objects.filter(user=user)
    )
    if total_invested >= 100000:
        if complete_mission(user, profile, 'invest_1lakh'):
            completed.append('Portfolio Builder')

    # Diversifier
    sectors = Holding.objects.filter(
        user=user
    ).exclude(
        stock__sector=''
    ).values_list('stock__sector', flat=True).distinct()
    if sectors.count() >= 3:
        if complete_mission(user, profile, 'diversify'):
            completed.append('Diversifier')

    # Profit maker
    for holding in Holding.objects.filter(user=user).select_related('stock'):
        pnl = (float(holding.stock.current_price) - float(holding.avg_buy_price)) * holding.quantity
        if pnl > 0:
            if complete_mission(user, profile, 'profit'):
                completed.append('Profit Maker')
            break

    return completed

def check_missions_on_watchlist(user, profile):
    completed = []
    count = Watchlist.objects.filter(user=user).count()
    if count >= 5:
        if complete_mission(user, profile, 'watchlist_5'):
            completed.append('Watchlist Builder')
    return completed

def check_missions_on_login(user, profile):
    completed = []
    login_days = Order.objects.filter(
        user=user
    ).dates('timestamp', 'day').count()
    if login_days >= 5:
        if complete_mission(user, profile, 'login_5days'):
            completed.append('Consistent Investor')
    return completed