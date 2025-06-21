from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()


class AccountsTestCase(TestCase):
    """Test cases for user authentication and profile management."""

    def setUp(self):
        """Set up test users for different roles."""
        self.customer = User.objects.create_user(username='customer_user', password='testpass', role='customer')
        self.manager = User.objects.create_user(username='manager_user', password='testpass', role='manager')
        self.delivery_agent = User.objects.create_user(username='delivery_user', password='testpass', role='delivery_agent')

    ## 1. User Signup Test
    def test_signup_view(self):
        """Test if a new user can sign up successfully."""
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'new_user',
            'email': 'newuser@example.com',
            'role': 'customer',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        self.assertTrue(User.objects.filter(username='new_user').exists())

    ## 2. User Login Test
    def test_login_view(self):
        """Test if a registered user can log in successfully."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'customer_user',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertEqual(response.url, reverse('accounts:customer_dashboard'))

    ## 3. Invalid Login Test
    def test_invalid_login(self):
        """Test login with incorrect credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'customer_user',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password!")

    

    ## 5. Logout Test
    def test_logout_view(self):
        """Test if a user can log out successfully."""
        self.client.login(username='customer_user', password='testpass')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect to home

    ## 6. Profile Update Test
    def test_profile_update(self):
        """Test if a logged-in user can update their profile."""
        self.client.login(username='customer_user', password='testpass')
        response = self.client.post(reverse('accounts:profile'), {
            'email': 'updated@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to profile page

        # Verify profile update
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.email, 'updated@example.com')
        self.assertEqual(self.customer.first_name, 'John')
        self.assertEqual(self.customer.last_name, 'Doe')

    ## 7. Password Change Test
    def test_change_password(self):
        """Test if a user can change their password successfully."""
        self.client.login(username='customer_user', password='testpass')

        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'testpass',
            'new_password1': 'NewTestPass123',
            'new_password2': 'NewTestPass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to profile page

        # Verify the new password works
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password('NewTestPass123'))

    ## 8. Access Control Tests
    def test_unauthorized_access(self):
        """Ensure unauthorized users cannot access certain views."""
        protected_urls = [
            reverse('accounts:customer_dashboard'),
            reverse('accounts:manager_dashboard'),
            reverse('accounts:delivery_dashboard'),
            reverse('accounts:profile')
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirect to login page
            self.assertIn(reverse('accounts:login'), response.url)  # Redirects to login


    
    def test_manager_login_redirect(self):
        """Test manager is redirected to their dashboard on login."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'manager_user',
            'password': 'testpass'
        })
        self.assertRedirects(response, reverse('accounts:manager_dashboard'))

    def test_change_password_with_wrong_old_password(self):
        """Test password change fails with incorrect current password."""
        self.client.login(username='customer_user', password='testpass')
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'wrongoldpass',
            'new_password1': 'NewPass123',
            'new_password2': 'NewPass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your old password was entered incorrectly.")

    def test_manager_login_redirect(self):
        """Test manager is redirected to their dashboard on login."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'manager_user',
            'password': 'testpass'
        })
        self.assertRedirects(response, reverse('accounts:manager_dashboard'))





