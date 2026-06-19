import csv
import os
import yfinance as yf
from django.core.management.base import BaseCommand
from market.models import Stock

class Command(BaseCommand):
    help = 'Fetch live stock prices and fundamentals for Nifty 500 from NSE via yfinance'

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
                fast = ticker.fast_info
                info = ticker.info  # slower, has fundamentals

                price = fast.last_price
                prev_close = fast.previous_close
                change_pct = ((price - prev_close) / prev_close) * 100

                Stock.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': name,
                        'current_price': round(price, 2),
                        'previous_close': round(prev_close, 2),
                        'change_percent': round(change_pct, 2),
                        'open_price': round(info.get('open', 0) or 0, 2),
                        'day_high': round(info.get('dayHigh', 0) or 0, 2),
                        'day_low': round(info.get('dayLow', 0) or 0, 2),
                        'week52_high': round(info.get('fiftyTwoWeekHigh', 0) or 0, 2),
                        'week52_low': round(info.get('fiftyTwoWeekLow', 0) or 0, 2),
                        'market_cap': info.get('marketCap', 0) or 0,
                        'pe_ratio': round(info.get('trailingPE', 0) or 0, 2) if info.get('trailingPE') else None,
                        'eps': round(info.get('trailingEps', 0) or 0, 2) if info.get('trailingEps') else None,
                        'pb_ratio': round(info.get('priceToBook', 0) or 0, 2) if info.get('priceToBook') else None,
                        'dividend_yield': round((info.get('dividendYield', 0) or 0) * 100, 2) if info.get('dividendYield') else None,
                        'book_value': round(info.get('bookValue', 0) or 0, 2) if info.get('bookValue') else None,
                        'roe': round((info.get('returnOnEquity', 0) or 0) * 100, 2) if info.get('returnOnEquity') else None,
                        'debt_to_equity': round(info.get('debtToEquity', 0) or 0, 2) if info.get('debtToEquity') else None,
                        'volume': info.get('volume', 0) or 0,
                        'sector': info.get('sector', '') or '',
                    }
                )
                self.stdout.write(f"✓ {symbol}: ₹{price:.2f} ({change_pct:+.2f}%)")
                success += 1
            except Exception as e:
                self.stdout.write(f"✗ {symbol}: {e}")
                failed += 1

        self.stdout.write(f'\nDone! {success} fetched, {failed} failed.')