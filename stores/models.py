from django.db import models
# from django.contrib.auth.models import User
from django.conf import settings

class Store(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.FloatField(blank=True, null=True)  # Changed to FloatField
    longitude = models.FloatField(blank=True, null=True)  # Changed to FloatField
    contact_number = models.CharField(max_length=20)  # Increased length
    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'manager'},
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.store.name}"


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.item.name} x {self.quantity} in {self.cart}"

    @property
    def subtotal(self):
        return self.item.price * self.quantity
