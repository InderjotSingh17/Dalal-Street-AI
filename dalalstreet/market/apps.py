from django.apps import AppConfig
import sys

class MarketConfig(AppConfig):
    name = 'market'

    def ready(self):
        pass
        #if 'runserver' in sys.argv:
        #    from market import scheduler
        #    scheduler.start()