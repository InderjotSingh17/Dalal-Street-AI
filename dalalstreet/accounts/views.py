from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import UserProfile

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid username or password'})
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST.get('email', '')
        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/register.html', {'error': 'Username already taken'})
        user = User.objects.create_user(username=username, password=password, email=email)
        UserProfile.objects.create(user=user, balance=1000000)
        login(request, user)
        return redirect('dashboard')
    return render(request, 'accounts/register.html')

def logout_view(request):
    logout(request)
    return redirect('landing')
