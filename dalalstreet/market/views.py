from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Stock
from accounts.models import UserProfile

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
    }
    return render(request, 'market/dashboard.html', context)

@login_required(login_url='/login/')
def stock_detail(request, symbol):
    stock = get_object_or_404(Stock, symbol=symbol)
    profile = UserProfile.objects.get(user=request.user)
    holding = None
    try:
        from portfolio.models import Holding
        holding = Holding.objects.get(user=request.user, stock=stock)
    except:
        pass
    return render(request, 'market/stock_detail.html', {
        'stock': stock,
        'balance': profile.balance,
        'holding': holding,
    })