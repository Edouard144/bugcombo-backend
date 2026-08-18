from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Item, UserInventory, UserEquip

User = get_user_model()

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'item_type', 'rarity', 'price', 'icon', 'is_active', 'created_at']

class UserInventorySerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)

    class Meta:
        model = UserInventory
        fields = ['id', 'item', 'purchased_at', 'is_equipped']

class UserEquipSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)

    class Meta:
        model = UserEquip
        fields = ['id', 'item_type', 'item', 'equipped_at']
