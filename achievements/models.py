from django.db import models


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=100)

    def __str__(self):
        return self.name
