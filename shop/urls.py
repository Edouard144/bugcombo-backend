from django.urls import path
from .views import ItemListView, PurchaseItemView, InventoryView, EquipItemView, UnequipItemView, EquippedItemsView

urlpatterns = [
    path('items/', ItemListView.as_view(), name='item_list'),
    path('items/<int:item_id>/purchase/', PurchaseItemView.as_view(), name='purchase_item'),
    path('inventory/', InventoryView.as_view(), name='inventory'),
    path('equip/<int:item_id>/', EquipItemView.as_view(), name='equip_item'),
    path('unequip/<str:item_type>/', UnequipItemView.as_view(), name='unequip_item'),
    path('equipped/', EquippedItemsView.as_view(), name='equipped_items'),
]
