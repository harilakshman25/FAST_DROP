from django.contrib import admin
from .models import Store, Item


class ItemInline(admin.TabularInline):
    model = Item
    extra = 1  # Allows adding multiple items at once


class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'manager')
    search_fields = ('name', 'manager__username')
    list_filter = ('manager',)
    inlines = [ItemInline]  # Allows adding items directly in Store admin


class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'price', 'stock', 'created_at')
    list_filter = ('store',)
    search_fields = ('name', 'store__name')


admin.site.register(Store, StoreAdmin)
admin.site.register(Item, ItemAdmin)
