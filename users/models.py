from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    country = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    total_duels = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    last_win_at = models.DateTimeField(null=True, blank=True)
    achievements = models.ManyToManyField('achievements.Achievement', blank=True, related_name='users')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Gamification
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    elo = models.IntegerField(default=1000)
    games_played = models.IntegerField(default=0)

    # Social
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    from_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('duel_played', 'Duel Played'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('level_up', 'Level Up'),
        ('friend_added', 'Friend Added'),
        ('tournament_joined', 'Tournament Joined'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"