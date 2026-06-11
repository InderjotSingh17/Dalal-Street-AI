from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=1000000
    )

    def __str__(self):
        return self.user.username