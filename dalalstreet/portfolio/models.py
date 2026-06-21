from django.db import models
from django.contrib.auth.models import User
from market.models import Stock

class Holding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    avg_buy_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ('user', 'stock')

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}"

    @property
    def current_value(self):
        return float(self.stock.current_price) * self.quantity

    @property
    def invested_value(self):
        return float(self.avg_buy_price) * self.quantity

    @property
    def pnl(self):
        return self.current_value - self.invested_value

    @property
    def pnl_percent(self):
        if self.invested_value == 0:
            return 0
        return (self.pnl / self.invested_value) * 100

class Order(models.Model):
    BUY = 'BUY'
    SELL = 'SELL'
    ORDER_TYPES = [(BUY, 'Buy'), (SELL, 'Sell')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_type} {self.quantity} {self.stock.symbol} @ ₹{self.price}"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stock')

    def __str__(self):
        return f"{self.user.username} watching {self.stock.symbol}"

class Mission(models.Model):
    DAILY = 'DAILY'
    ONETIME = 'ONETIME'
    MISSION_TYPES = [(DAILY, 'Daily'), (ONETIME, 'One-time')]

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    xp_reward = models.IntegerField(default=10)
    mission_type = models.CharField(max_length=10, choices=MISSION_TYPES, default=DAILY)
    mission_key = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class UserMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'mission')

    def __str__(self):
        return f"{self.user.username} - {self.mission.name}"