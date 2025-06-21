from celery import shared_task
from django.utils.timezone import now, timedelta
from .models import Order
import googlemaps
from django.conf import settings


API_KEY = "AIzaSyC1VqOkQRTBxksbgjRp0-M6k8kDR1s6Exg"  # Replace with your API key
gmaps = googlemaps.Client(key=API_KEY)


@shared_task
def group_and_generate_route():
    time_threshold = now() - timedelta(minutes=4)
    ungrouped_orders = Order.objects.filter(group_id__isnull=True, status='CONFIRMED', created_at__gte=time_threshold)
    
    if ungrouped_orders.exists():
        group_id = f"group_{int(now().timestamp())}"
        waypoints = []

        for order in ungrouped_orders:
            order.group_id = group_id
            order.save()
            waypoints.append(f"{order.address}, {order.city}, {order.state}, {order.pincode}")
        
        # Generate route
        if waypoints:
            create_delivery_route(group_id, waypoints)


def create_delivery_route(group_id, waypoints):
    origin = "Current+Location"  # Delivery agent's location
    destination = waypoints[-1]
    waypoints_url = "|".join(waypoints[:-1])

    maps_url = (
        f"https://www.google.com/maps/dir/?api=1&origin={origin}"
        f"&destination={destination}&waypoints={waypoints_url}&travelmode=driving"
    )

    print(f"🌐 View optimized route for {group_id}: {maps_url}")
    return maps_url
