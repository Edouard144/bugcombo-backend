from django.db import models
from django.conf import settings

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    condition_type = models.CharField(max_length=50, default='wins')
    condition_value = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['condition_value']

    def __str__(self):
        return self.name