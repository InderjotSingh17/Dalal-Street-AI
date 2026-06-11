import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

def fetch_stock_prices():
    from django.core.management import call_command
    call_command('fetch_stocks')

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        fetch_stock_prices,
        trigger='interval',
        minutes=15,
        id='fetch_stocks',
        replace_existing=True,
    )
    logger.info("Scheduler started — fetching stocks every 15 minutes")
    scheduler.start()