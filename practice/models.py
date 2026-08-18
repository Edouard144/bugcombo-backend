from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class PracticeRoom(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_rooms')
    language = models.CharField(max_length=50, default='python')
    difficulty = models.CharField(max_length=20, default='easy')
    buggy_code = models.TextField()
    duration = models.IntegerField(default=180)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    score = models.FloatField(null=True, blank=True)
    correctness = models.FloatField(null=True, blank=True)
    cleanliness = models.FloatField(null=True, blank=True)
    efficiency = models.FloatField(null=True, blank=True)
    security = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Practice {self.id} - {self.user.username}"

class PracticeSubmission(models.Model):
    room = models.ForeignKey(PracticeRoom, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_submissions')
    code = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    correctness = models.FloatField(null=True, blank=True)
    cleanliness = models.FloatField(null=True, blank=True)
    efficiency = models.FloatField(null=True, blank=True)
    security = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Practice submission {self.id} - {self.user.username}"
