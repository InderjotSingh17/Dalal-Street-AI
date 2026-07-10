from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Stock
from accounts.models import UserProfile
from decimal import Decimal
from django.contrib import messages
from market.missions import check_missions_on_trade
from market.missions import check_missions_on_watchlist
from django.http import JsonResponse

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    stocks = Stock.objects.all().order_by('symbol')
    return render(request, 'market/landing.html', {'stocks': stocks})

@login_required(login_url='/login/')
def dashboard(request):
    search = request.GET.get('q', '')
    sector = request.GET.get('sector', '')
    sort = request.GET.get('sort', 'symbol')

    stocks = Stock.objects.all()

    if search:
        stocks = stocks.filter(
            Q(symbol__icontains=search) | Q(company_name__icontains=search)
        )
    if sector:
        stocks = stocks.filter(sector=sector)

    sort_map = {
        'symbol': 'symbol',
        'price': '-current_price',
        'change': '-change_percent',
        'market_cap': '-market_cap',
    }
    stocks = stocks.order_by(sort_map.get(sort, 'symbol'))

    gainers = Stock.objects.order_by('-change_percent')[:5]
    losers = Stock.objects.order_by('change_percent')[:5]
    sectors = Stock.objects.exclude(sector='').values_list('sector', flat=True).distinct().order_by('sector')
    profile = UserProfile.objects.get(user=request.user)
    from portfolio.models import Holding
    holdings = Holding.objects.filter(user=request.user).select_related('stock')
    total_invested = sum(h.invested_value for h in holdings)
    total_current = sum(h.current_value for h in holdings)
    total_pnl = total_current - total_invested
    context = {
        'stocks': stocks,
        'gainers': gainers,
        'losers': losers,
        'sectors': sectors,
        'balance': profile.balance,
        'search': search,
        'selected_sector': sector,
        'sort': sort,
        'total_stocks': stocks.count(),
        'xp': profile.xp,
        'level': profile.level,
        'level_name': profile.level_name,
        'next_level_xp': profile.next_level_xp,
        'xp_progress': profile.xp_progress_percent,
        'total_invested': round(total_invested, 2),
        'total_current': round(total_current, 2),       
        'total_pnl': round(total_pnl, 2)
    }
    return render(request, 'market/dashboard.html', context)

@login_required(login_url='/login/')
def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, symbol=symbol)
    profile = UserProfile.objects.get(user=request.user)
    holding = None
    in_watchlist = False
    try:
        from portfolio.models import Holding, Watchlist
        holding = Holding.objects.get(user=request.user, stock=stock)
    except:
        pass
    try:
        from portfolio.models import Watchlist
        Watchlist.objects.get(user=request.user, stock=stock)
        in_watchlist = True
    except:
        pass
    coaching_tip = request.session.pop('coaching_tip', None)
    mentor_card = request.session.pop('mentor_card', None)
    mentor_event = request.session.pop('mentor_event', None)
    return render(request, 'market/stock_detail.html', {
        'stock': stock,
        'balance': profile.balance,
        'holding': holding,
        'in_watchlist': in_watchlist,
        'coaching_tip': coaching_tip,
        'mentor_card': mentor_card,
        'mentor_event': mentor_event,
    })

@login_required(login_url='/login/')
def buy_stock(request, symbol):
    if request.method != 'POST':
        return redirect('stock_detail', symbol=symbol)

    stock = get_object_or_404(Stock, symbol=symbol)
    profile = UserProfile.objects.get(user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        return redirect('stock_detail', symbol=symbol)

    total_cost = Decimal(str(stock.current_price)) * quantity

    if profile.balance < total_cost:
        return redirect('stock_detail', symbol=symbol)

    profile.balance -= total_cost
    profile.save()

    from portfolio.models import Holding, Order
    holding, created = Holding.objects.get_or_create(
        user=request.user,
        stock=stock,
        defaults={'quantity': 0, 'avg_buy_price': 0}
    )

    total_qty = holding.quantity + quantity
    total_invested = (Decimal(str(holding.avg_buy_price)) * holding.quantity) + total_cost
    holding.avg_buy_price = total_invested / total_qty
    holding.quantity = total_qty
    holding.save()

    xp_to_add = 10
    if not Order.objects.filter(user=request.user).exists():
        xp_to_add += 50
    profile.add_xp(xp_to_add)
    check_missions_on_trade(request.user, profile, quantity)
    # AI Mentor analysis — runs automatically
    # AI Mentor analysis — runs automatically
    from market.mentor.orchestrator import MentorOrchestrator
    mentor = MentorOrchestrator(request.user)
    mentor_card = mentor.on_buy(stock, quantity, float(total_cost))
    request.session['mentor_card'] = mentor_card
    request.session['mentor_event'] = 'buy'
    return redirect('stock_detail', symbol=symbol)


@login_required(login_url='/login/')
def sell_stock(request, symbol):
    if request.method != 'POST':
        return redirect('stock_detail', symbol=symbol)

    stock = get_object_or_404(Stock, symbol=symbol)
    profile = UserProfile.objects.get(user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    from portfolio.models import Holding, Order
    try:
        holding = Holding.objects.get(user=request.user, stock=stock)
    except Holding.DoesNotExist:
        return redirect('stock_detail', symbol=symbol)

    if quantity <= 0 or quantity > holding.quantity:
        return redirect('stock_detail', symbol=symbol)

    total_value = Decimal(str(stock.current_price)) * quantity

    profile.balance += total_value
    profile.save()

    avg_price = float(holding.avg_buy_price)  # capture BEFORE mutating/deleting the holding
    holding.quantity -= quantity
    if holding.quantity == 0:
        holding.delete()
    else:
        holding.save()

    profile.add_xp(10)
    check_missions_on_trade(request.user, profile, quantity)
    # AI Mentor analysis — runs automatically
    from market.mentor.orchestrator import MentorOrchestrator
    mentor = MentorOrchestrator(request.user)
    mentor_card = mentor.on_sell(stock, quantity, float(stock.current_price), avg_price)
    request.session['mentor_card'] = mentor_card
    request.session['mentor_event'] = 'sell'
    return redirect('stock_detail', symbol=symbol)

@login_required(login_url='/login/')
def portfolio(request):
    from portfolio.models import Holding
    from market.mentor.orchestrator import MentorOrchestrator
    profile = UserProfile.objects.get(user=request.user)
    holdings = Holding.objects.filter(user=request.user).select_related('stock')

    total_invested = sum(h.invested_value for h in holdings)
    total_current = sum(h.current_value for h in holdings)
    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    ai_report = None
    if holdings.exists():
        mentor = MentorOrchestrator(request.user)
        ai_report = mentor.on_portfolio_view()

    return render(request, 'market/portfolio.html', {
        'holdings': holdings,
        'balance': profile.balance,
        'total_invested': round(total_invested, 2),
        'total_current': round(total_current, 2),
        'total_pnl': round(total_pnl, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'ai_report': ai_report,
    })

@login_required(login_url='/login/')
def orders(request):
    from portfolio.models import Order
    profile = UserProfile.objects.get(user=request.user)
    order_list = Order.objects.filter(user=request.user).select_related('stock').order_by('-timestamp')
    return render(request, 'market/orders.html', {
        'orders': order_list,
        'balance': profile.balance,
    })

@login_required(login_url='/login/')
def watchlist(request):
    from portfolio.models import Watchlist
    profile = UserProfile.objects.get(user=request.user)
    items = Watchlist.objects.filter(user=request.user).select_related('stock')
    return render(request, 'market/watchlist.html', {
        'items': items,
        'balance': profile.balance,
    })

@login_required(login_url='/login/')
def toggle_watchlist(request, symbol):
    from portfolio.models import Watchlist
    stock = get_object_or_404(Stock, symbol=symbol)
    item, created = Watchlist.objects.get_or_create(user=request.user, stock=stock)
    if created:
        profile = UserProfile.objects.get(user=request.user)
        check_missions_on_watchlist(request.user, profile)
    else:
        item.delete()
    return redirect('stock_detail', symbol=symbol)

@login_required(login_url='/login/')
def missions(request):
    from portfolio.models import Mission, UserMission
    from django.utils import timezone
    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()
    all_missions = Mission.objects.all()

    mission_data = []
    for m in all_missions:
        if m.mission_type == 'DAILY':
            user_mission = UserMission.objects.filter(
                user=request.user, mission=m,
                completed=True, completed_date=today
            ).first()
        else:
            user_mission = UserMission.objects.filter(
                user=request.user, mission=m, completed=True
            ).first()

        mission_data.append({
            'mission': m,
            'completed': user_mission is not None,
        })

    daily = [m for m in mission_data if m['mission'].mission_type == 'DAILY']
    onetime = [m for m in mission_data if m['mission'].mission_type == 'ONETIME']
    completed_count = sum(1 for m in mission_data if m['completed'])

    return render(request, 'market/missions.html', {
        'daily': daily,
        'onetime': onetime,
        'balance': profile.balance,
        'xp': profile.xp,
        'level': profile.level,
        'level_name': profile.level_name,
        'completed_count': completed_count,
        'total_count': len(mission_data),
    })

@login_required(login_url='/login/')
def leaderboard(request):
    from portfolio.models import Holding, Order
    from django.contrib.auth.models import User

    profiles = UserProfile.objects.all().select_related('user')
    leaderboard_data = []

    for profile in profiles:
        holdings = Holding.objects.filter(user=profile.user).select_related('stock')
        total_invested = sum(h.invested_value for h in holdings)
        total_current = sum(h.current_value for h in holdings)
        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        total_portfolio = float(profile.balance) + total_current

        leaderboard_data.append({
            'user': profile.user,
            'profile': profile,
            'total_portfolio': round(total_portfolio, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl_pct, 2),
            'xp': profile.xp,
            'level_name': profile.level_name,
            'level': profile.level,
            'total_trades': Order.objects.filter(user=profile.user).count(),
        })

    leaderboard_data.sort(key=lambda x: x['total_portfolio'], reverse=True)

    user_rank = None
    for i, entry in enumerate(leaderboard_data):
        if entry['user'] == request.user:
            user_rank = i + 1
            break

    my_profile = UserProfile.objects.get(user=request.user)

    return render(request, 'market/leaderboard.html', {
        'leaderboard': leaderboard_data,
        'user_rank': user_rank,
        'balance': my_profile.balance,
        'my_profile': my_profile,
    })

@login_required(login_url='/login/')
def mentor(request):
    from market.mentor_rules import get_diversification_score, get_risk_level, get_behavioral_insights, get_portfolio_tips, get_sector_allocation
    profile = UserProfile.objects.get(user=request.user)

    diversification = get_diversification_score(request.user)
    risk = get_risk_level(request.user)
    behavioral = get_behavioral_insights(request.user)
    tips = get_portfolio_tips(request.user)
    sector_allocation = get_sector_allocation(request.user)

    return render(request, 'market/mentor.html', {
        'balance': profile.balance,
        'diversification': diversification,
        'risk': risk,
        'behavioral': behavioral,
        'tips': tips,
        'sector_allocation': sector_allocation,
        'xp': profile.xp,
        'level_name': profile.level_name,
    })

@login_required(login_url='/login/')
def learn(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'market/learn.html', {
        'balance': profile.balance,
    })

@login_required(login_url='/login/')
def ai_mentor(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'market/ai_mentor.html', {
        'balance': profile.balance,
    })

@login_required(login_url='/login/')
def ai_mentor_chat(request):
    import json
    from market.ai_mentor import ask_ai_mentor

    if request.method != 'POST':
        return redirect('ai_mentor')

    data = json.loads(request.body)
    user_message = data.get('message', '')
    chat_history = data.get('history', [])

    if not user_message.strip():
        from django.http import JsonResponse
        return JsonResponse({'error': 'Empty message'}, status=400)

    try:
        response = ask_ai_mentor(request.user, user_message, chat_history)
        from django.http import JsonResponse
        return JsonResponse({'response': response})
    except Exception as e:
        from django.http import JsonResponse
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='/login/')
def stock_price_api(request, symbol):
    stock = get_object_or_404(Stock, symbol=symbol)

    return JsonResponse({
        "symbol": stock.symbol,
        "current_price": float(stock.current_price),
        "change_percent": float(stock.change_percent),
        "previous_close": float(stock.previous_close),
        "day_high": float(stock.day_high),
        "day_low": float(stock.day_low),
    })