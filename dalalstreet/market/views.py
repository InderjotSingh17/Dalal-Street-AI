from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile
from .models import Stock

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    stocks = Stock.objects.all().order_by('symbol')
    return render(request, 'market/landing.html',{'stocks': stocks})

@login_required(login_url='/login/')
def dashboard(request):
    stocks = Stock.objects.all()
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'market/dashboard.html', {
        'stocks': stocks,
        'balance': profile.balance,
    })