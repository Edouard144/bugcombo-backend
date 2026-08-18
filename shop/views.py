from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Item, UserInventory, UserEquip
from .serializers import ItemSerializer, UserInventorySerializer, UserEquipSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class ItemListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Shop'],
        summary='List shop items',
        description='Get all available shop items.',
        parameters=[
            OpenApiParameter(name='item_type', description='Filter by item type', required=False, type=str, enum=['avatar', 'title', 'badge', 'theme', 'emote', 'banner']),
            OpenApiParameter(name='rarity', description='Filter by rarity', required=False, type=str, enum=['common', 'rare', 'epic', 'legendary']),
        ],
        responses={200: OpenApiResponse(response=ItemSerializer(many=True))}
    )
    def get(self, request):
        items = Item.objects.filter(is_active=True)
        item_type = request.query_params.get('item_type')
        rarity = request.query_params.get('rarity')
        if item_type:
            items = items.filter(item_type=item_type)
        if rarity:
            items = items.filter(rarity=rarity)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)

class PurchaseItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Shop'],
        summary='Purchase item',
        description='Purchase an item from the shop.',
        parameters=[
            OpenApiParameter(name='item_id', description='Item ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            201: OpenApiResponse(response=UserInventorySerializer, description='Item purchased'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Already owned or insufficient funds'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Item not found'),
        }
    )
    def post(self, request, item_id):
        item = get_object_or_404(Item, id=item_id, is_active=True)
        
        existing = UserInventory.objects.filter(user=request.user, item=item).first()
        if existing:
            return Response({'error': 'Already owned'}, status=status.HTTP_400_BAD_REQUEST)
        
        # For now, we'll allow purchase without currency check
        # In production, you'd check user's coins/currency
        inventory = UserInventory.objects.create(user=request.user, item=item)
        serializer = UserInventorySerializer(inventory)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class InventoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Shop'],
        summary='My inventory',
        description='Get all items owned by the authenticated user.',
        responses={200: OpenApiResponse(response=UserInventorySerializer(many=True))}
    )
    def get(self, request):
        inventory = UserInventory.objects.filter(user=request.user).select_related('item')
        serializer = UserInventorySerializer(inventory, many=True)
        return Response(serializer.data)

class EquipItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Shop'],
        summary='Equip item',
        description='Equip an item from inventory. Only one item per type can be equipped.',
        parameters=[
            OpenApiParameter(name='item_id', description='Item ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=UserEquipSerializer, description='Item equipped'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Not owned or invalid type'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Item not found'),
        }
    )
    def post(self, request, item_id):
        item = get_object_or_404(Item, id=item_id, is_active=True)
        
        inventory = UserInventory.objects.filter(user=request.user, item=item).first()
        if not inventory:
            return Response({'error': 'Item not owned'}, status=status.HTTP_400_BAD_REQUEST)
        
        UserEquip.objects.filter(user=request.user, item_type=item.item_type).delete()
        
        equip, _ = UserEquip.objects.get_or_create(
            user=request.user,
            item_type=item.item_type,
            defaults={'item': item}
        )
        
        serializer = UserEquipSerializer(equip)
        return Response(serializer.data)

class UnequipItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Shop'],
        summary='Unequip item',
        description='Unequip an item by type.',
        parameters=[
            OpenApiParameter(name='item_type', description='Item type', required=True, type=str, location=OpenApiParameter.PATH, enum=['avatar', 'title', 'badge', 'theme', 'emote', 'banner'])
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Item unequipped'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='No item equipped of this type'),
        }
    )
    def post(self, request, item_type):
        try:
            equip = UserEquip.objects.get(user=request.user, item_type=item_type)
            equip.delete()
            return Response({'ok': True})
        except UserEquip.DoesNotExist:
            return Response({'error': 'No item equipped of this type'}, status=status.HTTP_404_NOT_FOUND)

class EquippedItemsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Shop'],
        summary='Equipped items',
        description='Get all equipped items for the authenticated user.',
        responses={200: OpenApiResponse(response=UserEquipSerializer(many=True))}
    )
    def get(self, request):
        equipped = UserEquip.objects.filter(user=request.user).select_related('item')
        serializer = UserEquipSerializer(equipped, many=True)
        return Response(serializer.data)
