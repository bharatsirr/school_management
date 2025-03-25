from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="e.g., T-shirt, Pant")
    description = models.TextField(help_text="Product specifications (e.g., size 23, 26)")
    unit_rate = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cost per unit (e.g., 100)")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Selling price (e.g., 150)")
    category = models.CharField(max_length=100, help_text="e.g., Dress, Transport")

    def __str__(self):
        return f"{self.name} - {self.category}"

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def profit_margin(self):
        """Returns the profit margin for the product."""
        return self.selling_price - self.unit_rate
    



class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total order amount")
    is_paid = models.BooleanField(default=False, help_text="Payment status")
    payment = models.ForeignKey('finance.PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - User: {self.user.username}"

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def mark_as_paid(self, payment_transaction=None):
        """Mark the order as paid."""
        self.is_paid = True
        if payment_transaction:
            self.payment = payment_transaction
        self.save()



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Item amount in order")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="order_items")
    is_paid = models.BooleanField(default=False, help_text="Payment status for this item")
    batch = models.ForeignKey('ProductBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")

    def __str__(self):
        return f"{self.product.name} - {self.amount}"

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def mark_as_paid(self):
        """Mark this item as paid."""
        self.is_paid = True
        self.save()



import uuid

class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    batch_number = models.CharField(max_length=50, unique=True, editable=False, help_text="Auto-generated batch ID")
    purchase_date = models.DateField(help_text="Batch purchase date")
    quantity = models.PositiveIntegerField(help_text="Total quantity purchased")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cost per unit")
    remaining_quantity = models.PositiveIntegerField(help_text="Quantity available in stock")

    def save(self, *args, **kwargs):
        """Auto-generate unique batch number if not set."""
        if not self.batch_number:
            self.batch_number = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"

    class Meta:
        verbose_name = "Product Batch"
        verbose_name_plural = "Product Batches"

    def consume_stock(self, quantity):
        """Reduces available stock."""
        if quantity > self.remaining_quantity:
            raise ValueError("Not enough stock available.")
        self.remaining_quantity -= quantity
        self.save()