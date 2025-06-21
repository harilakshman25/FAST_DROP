from django.db import models
from django.conf import settings
from stores.models import Item, Store
from django.utils.timezone import now, timedelta
import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PICKED', 'Picked'),  # New status for picked orders
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('UPI', 'UPI'),
        ('CARD', 'Card Payment'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,  # Make it nullable initially
        blank=True  # Allow blank values in forms
    )
    delivery_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries',
        limit_choices_to={'role': 'delivery_agent'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.BooleanField(default=False)
    
    # Delivery Address Fields
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Grouping Orders for Optimization
    group_id = models.UUIDField(default=uuid.uuid4, editable=False)
    delivery_agent_location = models.CharField(max_length=255, blank=True, null=True)  # Starting location for agent
    batch = models.ForeignKey('OrderBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Group orders placed within 4 minutes for the same store into the same group
        if not self.group_id and self.store:
            recent_order = Order.objects.filter(
                store=self.store,
                created_at__gte=now() - timedelta(minutes=4),
                status__in=['PENDING', 'CONFIRMED']
            ).order_by('-created_at').first()
            if recent_order:
                self.group_id = recent_order.group_id

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order #{self.id} - {self.user.username}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f'{self.item.name} x {self.quantity}'

class OrderBatch(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    delivery_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order_batches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date = models.DateField()  # The date this batch is for
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ['delivery_agent', 'date']

    def __str__(self):
        return f"Batch for {self.delivery_agent.get_full_name()} on {self.date}"

    @property
    def total_orders(self):
        return self.orders.count()

    @property
    def completed_orders(self):
        return self.orders.filter(status='DELIVERED').count()

    @property
    def progress_percentage(self):
        if self.total_orders == 0:
            return 0
        return (self.completed_orders / self.total_orders) * 100
