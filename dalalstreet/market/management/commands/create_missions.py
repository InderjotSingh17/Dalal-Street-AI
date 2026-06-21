from django.core.management.base import BaseCommand
from portfolio.models import Mission

MISSIONS = [
    {
        'name': 'First Steps',
        'description': 'Make your very first trade on Dalal Street AI',
        'xp_reward': 50,
        'mission_type': 'ONETIME',
        'mission_key': 'first_trade',
    },
    {
        'name': 'Daily Trader',
        'description': 'Make at least one trade today',
        'xp_reward': 15,
        'mission_type': 'DAILY',
        'mission_key': 'daily_trade',
    },
    {
        'name': 'Explorer',
        'description': 'View 5 different stock pages today',
        'xp_reward': 10,
        'mission_type': 'DAILY',
        'mission_key': 'daily_explore',
    },
    {
        'name': 'Diversifier',
        'description': 'Own stocks in 3 or more different sectors',
        'xp_reward': 25,
        'mission_type': 'ONETIME',
        'mission_key': 'diversify',
    },
    {
        'name': 'Watchlist Builder',
        'description': 'Add 5 stocks to your watchlist',
        'xp_reward': 10,
        'mission_type': 'ONETIME',
        'mission_key': 'watchlist_5',
    },
    {
        'name': 'Portfolio Builder',
        'description': 'Have more than ₹1,00,000 invested at once',
        'xp_reward': 20,
        'mission_type': 'ONETIME',
        'mission_key': 'invest_1lakh',
    },
    {
        'name': 'Big Buyer',
        'description': 'Buy 10 or more shares in a single trade',
        'xp_reward': 15,
        'mission_type': 'DAILY',
        'mission_key': 'big_buy',
    },
    {
        'name': 'Profit Maker',
        'description': 'Have a positive P&L on any holding',
        'xp_reward': 25,
        'mission_type': 'ONETIME',
        'mission_key': 'profit',
    },
    {
        'name': 'Consistent Investor',
        'description': 'Log in on 5 different days',
        'xp_reward': 30,
        'mission_type': 'ONETIME',
        'mission_key': 'login_5days',
    },
]

class Command(BaseCommand):
    help = 'Create all missions'

    def handle(self, *args, **kwargs):
        for m in MISSIONS:
            mission, created = Mission.objects.get_or_create(
                mission_key=m['mission_key'],
                defaults=m
            )
            if created:
                self.stdout.write(f"✓ Created: {mission.name}")
            else:
                self.stdout.write(f"→ Already exists: {mission.name}")
        self.stdout.write('Done!')