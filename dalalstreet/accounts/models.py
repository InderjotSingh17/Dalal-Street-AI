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

class LearningProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_profile')
    knowledge_level = models.CharField(max_length=20, default='beginner')
    concepts_taught = models.JSONField(default=list)
    concepts_mastered = models.JSONField(default=list)
    current_topic = models.CharField(max_length=50, blank=True, default='')
    next_topic = models.CharField(max_length=50, blank=True, default='')
    total_lessons_received = models.IntegerField(default=0)
    last_lesson_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.knowledge_level}"

    @classmethod
    def get_or_create_for_user(cls, user):
        profile, created = cls.objects.get_or_create(user=user)
        return profile


class BehaviourProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='behaviour_profile')
    panic_sell_count = models.IntegerField(default=0)
    fomo_buy_count = models.IntegerField(default=0)
    overtrading_count = models.IntegerField(default=0)
    hold_loser_count = models.IntegerField(default=0)
    sell_winner_early_count = models.IntegerField(default=0)
    poor_diversification_count = models.IntegerField(default=0)
    disciplined_hold_count = models.IntegerField(default=0)
    dominant_weakness = models.CharField(max_length=50, blank=True, default='')
    last_analysis_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} — behaviour profile"

    @classmethod
    def get_or_create_for_user(cls, user):
        profile, created = cls.objects.get_or_create(user=user)
        return profile

    def get_dominant_weakness(self):
        counts = {
            'panic_selling': self.panic_sell_count,
            'fomo_buying': self.fomo_buy_count,
            'overtrading': self.overtrading_count,
            'holding_losers': self.hold_loser_count,
            'selling_winners_early': self.sell_winner_early_count,
        }
        if not any(counts.values()):
            return None
        return max(counts, key=counts.get)


class MentorCardCache(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20)
    stock_symbol = models.CharField(max_length=20, blank=True, default='')
    card_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.event_type} — {self.created_at}"

    @classmethod
    def invalidate_for_user(cls, user):
        cls.objects.filter(user=user, is_valid=True).update(is_valid=False)