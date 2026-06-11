from django.db import models
from django.contrib.auth.models import User
from market.models import Stock
class Holding(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE
    )

    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}"
# Create your models here.
