from django.db import models
from django.conf import settings

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    condition_type = models.CharField(max_length=50)
    condition_value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['condition_value']

    def __str__(self):
        return self.name