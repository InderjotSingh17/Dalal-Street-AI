from django.db import models

class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=150)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    previous_close = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    open_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    day_high = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    day_low = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    week52_high = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    week52_low = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    market_cap = models.BigIntegerField(default=0)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    eps = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pb_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    book_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    roe = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    debt_to_equity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    volume = models.BigIntegerField(default=0)
    sector = models.CharField(max_length=100, blank=True, default='')

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.symbol