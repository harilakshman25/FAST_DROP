from fast_drop import settings
import requests
from requests.exceptions import RequestException
import logging
import googlemaps
from itertools import permutations

logger = logging.getLogger(__name__)

def get_optimized_route(orders):
    """Fetch optimized route including stores and delivery addresses."""
    api_key = settings.GOOGLE_MAPS_API_KEY

    try:
        # Create a mapping of orders by store
        store_orders = {}
        for order in orders:
            if order.store not in store_orders:
                store_orders[order.store] = []
            store_orders[order.store].append(order)

        waypoints = []
        addresses = set()

        # First, add all store locations
        for store, store_orders_list in store_orders.items():
            if store and store.address and store.address not in addresses:
                addresses.add(store.address)
                waypoints.append({
                    'address': store.address,
                    'type': 'store',
                    'name': store.name,
                    'store_id': store.id,
                    'orders': [order.id for order in store_orders_list]
                })

        # Then, add all delivery addresses
        for store, store_orders_list in store_orders.items():
            for order in store_orders_list:
                delivery_address = f"{order.address}, {order.city}, {order.state}, {order.pincode}"
                if delivery_address not in addresses:
                    addresses.add(delivery_address)
                    waypoints.append({
                        'address': delivery_address,
                        'type': 'delivery',
                        'name': f"Deliver to {order.user.get_full_name() or order.user.username}",
                        'order_id': order.id,
                        'store_id': store.id
                    })

        if not waypoints:
            logger.warning("No addresses found for route optimization")
            return None, None, None

        # Initialize Google Maps client
        gmaps = googlemaps.Client(key=api_key)

        # Get distance matrix
        addresses_list = [wp['address'] for wp in waypoints]
        distance_matrix = []
        for i, origin in enumerate(addresses_list):
            row = []
            for j, destination in enumerate(addresses_list):
                if i == j:
                    row.append(0)
                else:
                    result = gmaps.distance_matrix(origin, destination, mode="driving")
                    distance = result["rows"][0]["elements"][0]["distance"]["value"] / 1000  # Distance in km
                    row.append(distance)
            distance_matrix.append(row)

        # Find optimal route ensuring stores are visited before their deliveries
        n = len(waypoints)
        store_indices = [i for i, wp in enumerate(waypoints) if wp['type'] == 'store']
        delivery_indices = [i for i, wp in enumerate(waypoints) if wp['type'] == 'delivery']
        
        # Create a mapping of store_id to its index
        store_id_to_index = {waypoints[i]['store_id']: i for i in store_indices}
        
        # Create a mapping of delivery points to their required store index
        delivery_to_store = {i: store_id_to_index[waypoints[i]['store_id']] for i in delivery_indices}

        # Initialize path with stores first
        path = store_indices.copy()
        unvisited_deliveries = set(delivery_indices)

        # For each store, add its deliveries based on nearest neighbor
        while unvisited_deliveries:
            last = path[-1]
            valid_next = [i for i in unvisited_deliveries 
                         if delivery_to_store[i] in set(store_indices[:path.index(last) + 1])]
            
            if not valid_next:
                # If no valid deliveries found, move to next store
                remaining_stores = [i for i in store_indices if i not in path]
                if remaining_stores:
                    path.append(min(remaining_stores, key=lambda x: distance_matrix[last][x]))
                    continue
                # If no more stores, add remaining deliveries in nearest neighbor order
                next_point = min(unvisited_deliveries, key=lambda x: distance_matrix[last][x])
                path.append(next_point)
                unvisited_deliveries.remove(next_point)
            else:
                # Add nearest valid delivery point
                next_point = min(valid_next, key=lambda x: distance_matrix[last][x])
                path.append(next_point)
                unvisited_deliveries.remove(next_point)

        # Create optimized waypoints list
        optimized_waypoints = [waypoints[idx] for idx in path]

        # Generate Google Maps URL
        base_url = "https://www.google.com/maps/dir/?api=1"
        origin = addresses_list[path[0]]
        destination = addresses_list[path[-1]]
        waypoints_url = "|".join(addresses_list[idx] for idx in path[1:-1])
        maps_url = f"{base_url}&origin={origin.replace(' ', '+')}&destination={destination.replace(' ', '+')}&waypoints={waypoints_url.replace(' ', '+')}&travelmode=driving"

        return maps_url, optimized_waypoints, distance_matrix

    except Exception as e:
        logger.error(f"Error in get_optimized_route: {str(e)}")
        return None, None, None
