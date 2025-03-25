from django.contrib import admin

from apps.sales.models import Product, ProductBatch, Order, OrderItem

admin.site.register(Product)
admin.site.register(ProductBatch)
admin.site.register(Order)
admin.site.register(OrderItem)