from django.db import models
from django.conf import settings
import uuid

class DuelRoom(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('judging', 'Judging'),
        ('finished', 'Finished'),
    ]

    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=8, unique=True, db_index=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_duels')
    opponent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='joined_duels')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting', db_index=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    buggy_code = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['opponent', 'status']),
        ]

    def __str__(self):
        return f"Duel {self.code} ({self.status})"


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(DuelRoom, on_delete=models.CASCADE, related_name='submissions')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    correctness = models.FloatField(null=True, blank=True)
    cleanliness = models.FloatField(null=True, blank=True)
    efficiency = models.FloatField(null=True, blank=True)
    security = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    is_winner = models.BooleanField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['room', 'player']),
            models.Index(fields=['player', 'submitted_at']),
        ]

    def __str__(self):
        return f"Submission by {self.player} in {self.room.code}"