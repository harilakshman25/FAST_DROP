from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order, OrderItem, OrderBatch
from stores.models import CartItem, Store
from django.db import transaction
from utils.google_maps import get_optimized_route
from django.conf import settings
from django.db.models import Count
from accounts.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from .forms import OrderForm
import logging

logger = logging.getLogger(__name__)

def is_manager(user):
    return user.role == 'manager'

def is_delivery_agent(user):
    return user.role == 'delivery_agent'

@login_required
def order_list(request):
    """View to display user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """View to display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def create_order(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('stores:cart')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Group cart items by store
                store_items = {}
                for cart_item in cart_items:
                    store = cart_item.item.store
                    if store not in store_items:
                        store_items[store] = []
                    store_items[store].append(cart_item)
                
                # Create separate orders for each store
                orders = []
                for store, items in store_items.items():
                    # Calculate total amount for this store's items
                    store_total = sum(item.subtotal for item in items)
                    
                    # Create the order for this store
                    order = Order.objects.create(
                        user=request.user,
                        store=store,
                        total_amount=store_total,
                        address=request.POST['address'],
                        city=request.POST['city'],
                        state=request.POST['state'],
                        pincode=request.POST['pincode'],
                        payment_method=request.POST['payment_method']
                    )
                    
                    # Create order items and update stock
                    for cart_item in items:
                        OrderItem.objects.create(
                            order=order,
                            item=cart_item.item,
                            quantity=cart_item.quantity,
                            price=cart_item.item.price
                        )
                        # Update stock
                        cart_item.item.stock -= cart_item.quantity
                        cart_item.item.save()
                    
                    orders.append(order)
                
                # Clear the cart
                cart_items.delete()
                
                messages.success(request, f'Successfully placed {len(orders)} orders!')
                return redirect('orders:order_list')
                
        except Exception as e:
            messages.error(request, 'An error occurred while placing your orders. Please try again.')
            return redirect('orders:create_order')
    
    # Group cart items by store for display
    store_items = {}
    for cart_item in cart_items:
        store = cart_item.item.store
        if store not in store_items:
            store_items[store] = []
        store_items[store].append(cart_item)
    
    # Calculate total amount
    total_amount = sum(item.subtotal for item in cart_items)
    
    return render(request, 'orders/order_form.html', {
        'store_items': store_items,
        'total_amount': total_amount
    })

@login_required
@user_passes_test(is_manager)
def store_orders(request):
    """View for store managers to see their store's orders"""
    store = get_object_or_404(Store, manager=request.user)
    
    # Get all orders for the store, grouped by status
    pending_orders = Order.objects.filter(store=store, status='PENDING').order_by('-created_at')
    confirmed_orders = Order.objects.filter(store=store, status='CONFIRMED').order_by('-created_at')
    picked_orders = Order.objects.filter(store=store, status='PICKED').order_by('-created_at')
    delivered_orders = Order.objects.filter(store=store, status='DELIVERED').order_by('-created_at')
    
    context = {
        'store': store,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'picked_orders': picked_orders,
        'delivered_orders': delivered_orders,
        'total_orders': Order.objects.filter(store=store).count(),
        'pending_count': pending_orders.count(),
        'confirmed_count': confirmed_orders.count(),
        'picked_count': picked_orders.count(),
        'delivered_count': delivered_orders.count(),
    }
    return render(request, 'orders/store_orders.html', context)

@login_required
@user_passes_test(is_manager)
def confirm_order(request, order_id):
    """View for store managers to confirm orders"""
    store = get_object_or_404(Store, manager=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)
    
    if order.status == 'PENDING':
        # Find other orders in the same group that need delivery
        group_orders = Order.objects.filter(
            group_id=order.group_id,
            status__in=['PENDING', 'CONFIRMED']
        ).exclude(id=order.id)
        
        # If there are other orders in the group, find a delivery agent with the least active deliveries
        if group_orders.exists():
            # Get delivery agents with their active delivery count
            delivery_agents = User.objects.filter(
                role='delivery_agent'
            ).annotate(
                active_deliveries=Count('deliveries', filter=models.Q(
                    deliveries__status__in=['CONFIRMED', 'PICKED']
                ))
            ).order_by('active_deliveries')
            
            if delivery_agents.exists():
                # Assign the delivery agent with the least active deliveries
                delivery_agent = delivery_agents.first()
                order.delivery_agent = delivery_agent
                # Assign the same delivery agent to other orders in the group
                group_orders.update(delivery_agent=delivery_agent)
        
        order.status = 'CONFIRMED'
        order.save()
        messages.success(request, 'Order confirmed successfully!')
    else:
        messages.error(request, 'Order cannot be confirmed.')
    
    return redirect('orders:store_orders')

@login_required
@user_passes_test(is_delivery_agent)
def delivery_agent_orders(request):
    """View for delivery agents to see their assigned deliveries"""
    orders = Order.objects.filter(
        delivery_agent=request.user,
        status__in=['CONFIRMED', 'PICKED']
    ).order_by('-created_at')
    
    # Get optimized route for the orders
    polyline, legs = get_optimized_route(orders)
    
    return render(request, 'orders/delivery_agent_orders.html', {
        'orders': orders,
        'polyline': polyline,
        'legs': legs,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

@csrf_exempt
@login_required
@user_passes_test(is_delivery_agent)
def update_order_status(request, order_id, status):
    """View for delivery agents to update order status"""
    try:
        order = Order.objects.get(id=order_id, delivery_agent=request.user)
        if status in ['PICKED', 'DELIVERED']:
            order.status = status
            order.save()
            return JsonResponse({'status': 'success', 'message': f'Order marked as {status}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid status provided'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'})

@login_required
@user_passes_test(is_delivery_agent)
def update_location(request):
    """View for delivery agents to update their location"""
    if request.method == 'POST':
        location = request.POST.get('location')
        if location:
            # Update all pending orders with the new location
            Order.objects.filter(
                delivery_agent=request.user,
                status__in=['CONFIRMED', 'PICKED']
            ).update(delivery_agent_location=location)
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def delivery_dashboard(request):
    try:
        # Get assigned orders for the current delivery agent
        assigned_orders = Order.objects.filter(
            delivery_agent=request.user,
            status__in=['CONFIRMED', 'PICKED']  # Only include orders that are not delivered
        ).prefetch_related(
            'items',
            'items__item',
            'store',
            'user'
        ).order_by('status', 'created_at')

        # Get available orders for pickup (all confirmed orders without a delivery agent)
        pickup_orders = Order.objects.filter(
            status='CONFIRMED',
            delivery_agent__isnull=True
        ).prefetch_related(
            'items',
            'store',
            'user'
        ).order_by('created_at')

        # Get optimized route only for orders that need to be picked up or delivered
        active_orders = assigned_orders.exclude(status='DELIVERED')
        maps_url = None
        optimized_waypoints = None
        if active_orders.exists():
            maps_url, optimized_waypoints, _ = get_optimized_route(active_orders)
        context = {
            'assigned_orders': assigned_orders,  # Show all assigned orders in the table
            'pickup_orders': pickup_orders,
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
            'maps_url': maps_url,
            'optimized_waypoints': optimized_waypoints,
        }
        return render(request, 'orders/delivery_dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in delivery dashboard: {str(e)}")
        context = {
            'assigned_orders': [],
            'pickup_orders': [],
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
            'error_message': 'There was an error loading the dashboard. Please try again later.'
        }
        return render(request, 'orders/delivery_dashboard.html', context)

@login_required
def accept_delivery(request, order_id):
    try:
        # Get the order and verify it exists and is in the correct state
        order = Order.objects.get(
            id=order_id,
            status='CONFIRMED',  # Only accept confirmed orders
            delivery_agent__isnull=True  # Only accept orders without a delivery agent
        )
        
        # Assign the order to the current delivery agent
        order.delivery_agent = request.user
        order.save()
        
        messages.success(request, f'Order #{order.id} has been assigned to you.')
    except Order.DoesNotExist:
        messages.error(request, 'Order not found or not available for pickup.')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('orders:delivery_dashboard')

@login_required
def update_delivery_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id, delivery_agent=request.user)
        new_status = request.POST.get('status')
        
        if new_status in ['PICKED', 'DELIVERED']:
            order.status = new_status
            order.save()
            
            if new_status == 'DELIVERED':
                # Send notification or update any other necessary data
                pass
            
            messages.success(request, f'Order #{order.id} has been marked as {new_status}')
        else:
            messages.error(request, 'Invalid status update requested')
            
        # Always redirect back to delivery dashboard to refresh the route
        return redirect('orders:delivery_dashboard')
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found or not assigned to you')
        return redirect('orders:delivery_dashboard')
    except Exception as e:
        logger.error(f"Error updating delivery status: {str(e)}")
        messages.error(request, 'An error occurred while updating the order status')
        return redirect('orders:delivery_dashboard')

@login_required
def batch_details(request, batch_id):
    batch = get_object_or_404(OrderBatch, id=batch_id, delivery_agent=request.user)
    
    orders = batch.orders.all().order_by('created_at')
    
    context = {
        'batch': batch,
        'orders': orders,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    return render(request, 'orders/batch_details.html', context)

@login_required
def create_batch(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        if date:
            date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # Check if batch already exists for this date
            if OrderBatch.objects.filter(delivery_agent=request.user, date=date).exists():
                messages.error(request, 'A batch already exists for this date.')
                return redirect('orders:delivery_dashboard')
            
            # Create new batch
            batch = OrderBatch.objects.create(
                delivery_agent=request.user,
                date=date,
                status='PENDING'
            )
            
            # Assign pending orders to the batch
            pending_orders = Order.objects.filter(
                status='PENDING',
                batch__isnull=True
            ).order_by('created_at')
            
            for order in pending_orders:
                order.batch = batch
                order.delivery_agent = request.user
                order.status = 'CONFIRMED'
                order.save()
            
            messages.success(request, f'Created new batch for {date} with {pending_orders.count()} orders.')
            return redirect('orders:batch_details', batch_id=batch.id)
    
    return redirect('orders:delivery_dashboard')