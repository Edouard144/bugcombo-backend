from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=100)

    users = models.ManyToManyField(User, related_name='achievements', blank=True)

    def __str__(self):
        return self.name
