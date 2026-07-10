from django.contrib import admin
from django.urls import path
from market import views
from accounts import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('buy/<str:symbol>/', views.buy_stock, name='buy_stock'),
    path('sell/<str:symbol>/', views.sell_stock, name='sell_stock'),
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('orders/', views.orders, name='orders'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/toggle/<str:symbol>/', views.toggle_watchlist, name='toggle_watchlist'),
    path('missions/', views.missions, name='missions'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('mentor/', views.mentor, name='mentor'),
    path('learn/', views.learn, name='learn'),
    path('ai-mentor/', views.ai_mentor, name='ai_mentor'),
    path('ai-mentor/chat/', views.ai_mentor_chat, name='ai_mentor_chat'),
    path('api/stock/<str:symbol>/', views.stock_price_api, name='stock_price_api'),
]