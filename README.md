# Fast Drop - Delivery Management System

Fast Drop is a Django-based delivery management system that helps manage orders, deliveries, and optimize delivery routes for multiple stores.

## Features

- **Multi-Store Support**: Handle orders from multiple stores efficiently
- **Smart Route Optimization**: Automatically optimize delivery routes using Google Maps API
- **Real-time Order Tracking**: Track order status from confirmation to delivery
- **Delivery Agent Dashboard**: Manage deliveries with optimized routes
- **Store Manager Interface**: Manage store orders and inventory
- **Customer Portal**: Place orders and track delivery status

## System Requirements

- Python 3.8+
- Django 4.2+
- Redis (for Celery)
- Google Maps API key
- PostgreSQL (recommended) or SQLite

## Project Structure

```
fast_drop/
├── accounts/                    # User authentication and profiles
│   ├── migrations/             # Database migrations
│   ├── templates/              # Account-related templates
│   ├── __init__.py
│   ├── admin.py               # Admin configurations
│   ├── apps.py                # App configuration
│   ├── forms.py               # User forms
│   ├── models.py              # User models
│   ├── tests.py               # Test cases
│   ├── urls.py                # URL routing
│   └── views.py               # View functions
│
├── fast_drop/                  # Project configuration
│   ├── __init__.py
│   ├── asgi.py                # ASGI configuration
│   ├── celery.py              # Celery configuration
│   ├── settings.py            # Project settings
│   ├── urls.py                # Main URL routing
│   └── wsgi.py                # WSGI configuration
│
├── orders/                     # Order management
│   ├── migrations/            # Database migrations
│   ├── templates/             # Order-related templates
│   ├── __init__.py
│   ├── admin.py              # Admin configurations
│   ├── apps.py               # App configuration
│   ├── forms.py              # Order forms
│   ├── models.py             # Order models
│   ├── tasks.py              # Celery tasks
│   ├── tests.py              # Test cases
│   ├── urls.py               # URL routing
│   └── views.py              # View functions
│
├── static/                    # Static files (CSS, JS, images)
│   ├── css/                  # Stylesheets
│   └── images/               # Image assets
│
├── staticfiles/              # Collected static files (generated)
│   ├── admin/               # Admin static files
│   ├── css/                 # Collected CSS
│   └── images/              # Collected images
│
├── templates/                # Base templates
│   ├── base.html            # Base template
│   └── home.html            # Home page template
│
├── utils/                    # Utility functions
│   └── google_maps.py       # Google Maps integration
│
├── manage.py                 # Django management script
├── requirements.txt          # Project dependencies
└── README.md                # Project documentation
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/fast_drop.git
cd fast_drop
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Create a superuser:

```bash
python manage.py createsuperuser
```

7. Start Redis server:

```bash
redis-server
```

8. Start Celery worker:

```bash
celery -A fast_drop worker -l info
```

9. Run the development server:

```bash
python manage.py runserver
```

## Configuration

### Google Maps API

1. Get a Google Maps API key from the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the following APIs:
   - Maps JavaScript API
   - Directions API
   - Distance Matrix API
3. Add your API key to the `.env` file:

```
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### Database

The system uses SQLite by default. For production, it's recommended to use PostgreSQL:

1. Install PostgreSQL
2. Create a database
3. Update DATABASES in settings.py:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fast_drop',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Usage

### Delivery Agent Workflow

1. **View Assigned Orders**:

   - Log in to the delivery dashboard
   - View all assigned orders and their status
   - See optimized delivery route

2. **Accept New Orders**:

   - View available orders in the pickup section
   - Accept orders to add them to your delivery list

3. **Update Order Status**:

   - Mark orders as "Picked" when collected from store
   - Mark orders as "Delivered" when delivered to customer
   - Route automatically updates when status changes

4. **View Optimized Route**:
   - Click "View Updated Route on Maps" to see the optimized delivery path
   - Route ensures stores are visited before their respective deliveries

### Store Manager Workflow

1. **Manage Orders**:

   - View all orders for your store
   - Confirm orders for delivery
   - Track order status

2. **Inventory Management**:
   - Add/update products
   - Manage stock levels
   - View order history

### Customer Workflow

1. **Place Orders**:

   - Browse products from multiple stores
   - Add items to cart
   - Place orders with delivery details

2. **Track Orders**:
   - View order status
   - Track delivery progress
   - View delivery history

## API Documentation

The system provides REST APIs for integration:

- `/api/orders/` - Order management
- `/api/stores/` - Store information
- `/api/deliveries/` - Delivery tracking

For detailed API documentation, see `docs/api.md`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact support@fastdrop.com
