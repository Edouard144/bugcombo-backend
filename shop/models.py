from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Item(models.Model):
    TYPE_CHOICES = [
        ('avatar', 'Avatar'),
        ('title', 'Title'),
        ('badge', 'Badge'),
        ('theme', 'Theme'),
        ('emote', 'Emote'),
        ('banner', 'Banner'),
    ]

    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    price = models.IntegerField(default=0)
    icon = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['item_type', 'price']

    def __str__(self):
        return self.name

class UserInventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='inventory_entries')
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_equipped = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'item']
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.username} - {self.item.name}"

class UserEquip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equipped_items')
    item_type = models.CharField(max_length=20, choices=Item.TYPE_CHOICES)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='equipped_entries')
    equipped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'item_type']
        ordering = ['item_type']

    def __str__(self):
        return f"{self.user.username} - {self.item_type}: {self.item.name}"
