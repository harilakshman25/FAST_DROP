from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Store, Item, Cart, CartItem

User = get_user_model()

class StoreAppTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='manager', password='password123', role='manager')
        self.customer = User.objects.create_user(username='customer', password='password123', role='customer')
        self.store = Store.objects.create(name='Test Store', manager=self.manager)
        self.item = Item.objects.create(name='Test Item', price=10.00, store=self.store, stock=10)

    def test_items_list_view(self):
        response = self.client.get(reverse('stores:items_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item.name)

    def test_manager_can_add_item(self):
        self.client.login(username='manager', password='password123')
        response = self.client.post(reverse('stores:add_item'), {
            'name': 'New Item',
            'price': 15.00,
            'stock': 5
        })
        self.assertEqual(Item.objects.count(), 2)
        self.assertRedirects(response, reverse('stores:items_list'))

    def test_customer_cannot_add_item(self):
        self.client.login(username='customer', password='password123')
        response = self.client.post(reverse('stores:add_item'), {
            'name': 'Illegal Item',
            'price': 20.00,
            'stock': 3
        })
        self.assertEqual(Item.objects.count(), 1)  # Item should not be added
        self.assertRedirects(response, reverse('stores:items_list'))

    def test_add_to_cart(self):
        self.client.login(username='customer', password='password123')
        response = self.client.post(reverse('stores:add_to_cart', args=[self.item.id]), {'quantity': 2})
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertRedirects(response, reverse('stores:items_list'))

    def test_remove_from_cart(self):
        self.client.login(username='customer', password='password123')
        cart = Cart.objects.create(user=self.customer)
        cart_item = CartItem.objects.create(cart=cart, item=self.item, quantity=2)
        response = self.client.post(reverse('stores:remove_from_cart', args=[cart_item.id]))
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertRedirects(response, reverse('stores:cart'))

    def test_cart_view_empty_message(self):
        self.client.login(username='customer', password='password123')
        response = self.client.get(reverse('stores:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your cart is empty')

    def test_cart_view_with_items(self):
        self.client.login(username='customer', password='password123')
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, item=self.item, quantity=1)
        response = self.client.get(reverse('stores:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item.name)
    def test_customer_cannot_access_other_cart(self):
        cart = Cart.objects.create(user=self.customer)
        other_customer = User.objects.create_user(username='other_customer', password='password123', role='customer')
        self.client.login(username='other_customer', password='password123')
        response = self.client.get(reverse('stores:cart'))
        # Assuming cart is filtered internally; cart should be empty
        self.assertNotContains(response, self.item.name)

    def test_update_cart_item_quantity(self):
        self.client.login(username='customer', password='password123')
        cart = Cart.objects.create(user=self.customer)
        cart_item = CartItem.objects.create(cart=cart, item=self.item, quantity=1)
        
        response = self.client.post(reverse('stores:update_cart', args=[cart_item.id]), {
            'quantity': 3
        })
        
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)
        self.assertRedirects(response, reverse('stores:cart'))

    



