from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True)
    condition_type = models.CharField(max_length=50)
    condition_value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"

class DailyReward(models.Model):
    day = models.IntegerField(unique=True)
    xp = models.IntegerField(default=0)
    coins = models.IntegerField(default=0)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['day']

    def __str__(self):
        return f"Day {self.day} reward"

class UserDailyReward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_rewards')
    day = models.IntegerField()
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'day']
        ordering = ['-day']

    def __str__(self):
        return f"{self.user.username} - Day {self.day}"

class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_reward_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.current_streak} day streak"
