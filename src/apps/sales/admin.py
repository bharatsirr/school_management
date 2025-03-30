from django.contrib import admin

from apps.sales.models import Product, ProductBatch, OrderItem

admin.site.register(Product)
admin.site.register(ProductBatch)
admin.site.register(OrderItem)