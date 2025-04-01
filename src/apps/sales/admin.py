from django.contrib import admin

from apps.sales.models import Product, ProductBatch, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'selling_price', 'unit_rate')
    search_fields = ('name',)
    list_filter = ('category',)

@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch_number', 'quantity')
    search_fields = ('product__name', 'batch_number')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'amount', 'is_paid')
    search_fields = ('order__id', 'product__name')
    list_filter = ('is_paid',)