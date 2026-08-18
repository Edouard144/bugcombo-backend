from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Guild(models.Model):
    name = models.CharField(max_length=100, unique=True)
    tag = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    banner = models.CharField(max_length=100, blank=True)
    level = models.IntegerField(default=1)
    xp = models.IntegerField(default=0)
    coins = models.IntegerField(default=0)
    max_members = models.IntegerField(default=50)
    is_public = models.BooleanField(default=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_guilds')
    officers = models.ManyToManyField(User, related_name='officer_guilds', blank=True)
    members = models.ManyToManyField(User, through='GuildMember', related_name='guilds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class GuildMember(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('officer', 'Officer'),
        ('leader', 'Leader'),
    ]

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    xp = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['guild', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.guild.name} ({self.role})"

class GuildEvent(models.Model):
    EVENT_TYPES = [
        ('raid', 'Raid'),
        ('war', 'Guild War'),
        ('tournament', 'Tournament'),
        ('practice', 'Practice Session'),
        ('social', 'Social Event'),
    ]

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    max_participants = models.IntegerField(default=0)
    participants = models.ManyToManyField(User, through='GuildEventParticipant', related_name='guild_events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_guild_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name} - {self.guild.name}"

class GuildEventParticipant(models.Model):
    event = models.ForeignKey(GuildEvent, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"

class GuildWar(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    guild1 = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='wars_as_guild1')
    guild2 = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='wars_as_guild2')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    guild1_score = models.IntegerField(default=0)
    guild2_score = models.IntegerField(default=0)
    winner = models.ForeignKey(Guild, on_delete=models.CASCADE, null=True, blank=True, related_name='war_wins')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.guild1.name} vs {self.guild2.name}"
