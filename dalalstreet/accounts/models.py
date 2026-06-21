from django.db import models
from django.contrib.auth.models import User

LEVELS = [
    (0,    1, 'Beginner'),
    (100,  2, 'Learner'),
    (300,  3, 'Analyst'),
    (600,  4, 'Trader'),
    (1000, 5, 'Pro Trader'),
    (1500, 6, 'Expert'),
    (2500, 7, 'Legend'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=1000000)
    xp = models.IntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def level(self):
        current = 1
        for xp_req, lvl, name in LEVELS:
            if self.xp >= xp_req:
                current = lvl
        return current

    @property
    def level_name(self):
        current = 'Beginner'
        for xp_req, lvl, name in LEVELS:
            if self.xp >= xp_req:
                current = name
        return current

    @property
    def next_level_xp(self):
        for xp_req, lvl, name in LEVELS:
            if self.xp < xp_req:
                return xp_req
        return LEVELS[-1][0]

    @property
    def xp_progress_percent(self):
        current_level_xp = 0
        next_level_xp = LEVELS[-1][0]
        for i, (xp_req, lvl, name) in enumerate(LEVELS):
            if self.xp >= xp_req:
                current_level_xp = xp_req
                if i + 1 < len(LEVELS):
                    next_level_xp = LEVELS[i + 1][0]
                else:
                    return 100
        if next_level_xp == current_level_xp:
            return 100
        return int(((self.xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100)

    def add_xp(self, amount):
        self.xp += amount
        self.save()