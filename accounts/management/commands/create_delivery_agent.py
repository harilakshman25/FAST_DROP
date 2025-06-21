from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a delivery agent user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role='delivery_agent'
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created delivery agent "{username}"'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating delivery agent: {str(e)}')) 