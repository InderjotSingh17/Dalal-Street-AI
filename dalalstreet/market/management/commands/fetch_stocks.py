import csv
import os
import yfinance as yf
from django.core.management.base import BaseCommand
from market.models import Stock

class Command(BaseCommand):
    help = 'Fetch live stock prices for Nifty 500 from NSE via yfinance'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'nifty500.csv')
        csv_path = os.path.abspath(csv_path)

        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            stocks = [(row['symbol'], row['company_name']) for row in reader]

        self.stdout.write(f'Fetching {len(stocks)} stocks...')
        success, failed = 0, 0

        for symbol, name in stocks:
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                info = ticker.fast_info
                price = info.last_price
                prev_close = info.previous_close
                change_pct = ((price - prev_close) / prev_close) * 100

                Stock.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': name,
                        'current_price': round(price, 2),
                        'previous_close': round(prev_close, 2),
                        'change_percent': round(change_pct, 2),
                    }
                )
                self.stdout.write(f"✓ {symbol}: ₹{price:.2f} ({change_pct:+.2f}%)")
                success += 1
            except Exception as e:
                self.stdout.write(f"✗ {symbol}: {e}")
                failed += 1

        self.stdout.write(f'\nDone! {success} fetched, {failed} failed.')