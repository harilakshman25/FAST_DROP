from django.core.management.base import BaseCommand
from orders.models import Order, OrderItem, OrderBatch
from stores.models import CartItem

class Command(BaseCommand):
    help = 'Clears all orders and related data from the database'

    def handle(self, *args, **kwargs):
        try:
            # Clear cart items first
            cart_items_count = CartItem.objects.all().count()
            CartItem.objects.all().delete()
            
            # Clear order items
            order_items_count = OrderItem.objects.all().count()
            OrderItem.objects.all().delete()
            
            # Clear order batches
            batch_count = OrderBatch.objects.all().count()
            OrderBatch.objects.all().delete()
            
            # Clear orders
            orders_count = Order.objects.all().count()
            Order.objects.all().delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleared:\n'
                    f'- {cart_items_count} cart items\n'
                    f'- {order_items_count} order items\n'
                    f'- {batch_count} order batches\n'
                    f'- {orders_count} orders'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing orders: {str(e)}')
            ) 