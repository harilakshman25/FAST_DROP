from django.shortcuts import render,redirect, get_object_or_404
from .models import Store, Item, Cart, CartItem
from orders.models import Order
from .forms import ItemForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# from . import forms
# Create your views here.
def stores_list(request):
    # return('uvan') 
    stores = Store.objects.all().order_by('created_at')
    return render(request,'stores/stores_list.html',{'stores':stores})

def items_list(request):
    """ New view to display all items from all stores """
    items = Item.objects.all()
    return render(request, 'stores/items_list.html', {'items': items})

# def store_details(request,slug):
#     # return HttpResponse(slug)
#     store = Store.objects.get(slug=slug)
#     return render(request,'stores/stores_detail.html',{'store':store})
# @login_required(login_url="/accounts/login/")
# def store_create(request):
#     if request.method == 'POST':
#         form=forms.CreateStore(request.POST,request.FILES)
#         if form.is_valid():
#             #save to database
#             instance = form.save(commit=False)
#             instance.author = request.user
#             instance.save()
#             return redirect('stores:list')
#     else:
#         form = forms.CreateStore()
#     return render(request,'stores/store_create.html',{'form':form})
@login_required
def add_item(request):
    if request.user.role != 'manager':
        messages.error(request, 'Only managers can add items.')
        return redirect('stores:items_list')
    
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.store = request.user.store
            item.save()
            messages.success(request, 'Item added successfully.')
            return redirect('stores:items_list')
    else:
        form = ItemForm()
    
    return render(request, 'stores/add_item.html', {'form': form})

@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        messages.error(request, 'Only managers can access this page.')
        return redirect('stores:items_list')
    
    store = get_object_or_404(Store, manager=request.user)
    items = store.items.all()
    
    # Get orders for the store
    orders = Order.objects.filter(store=store).order_by('-created_at')
    
    context = {
        'store': store,
        'items': items,
        'orders': orders,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='PENDING').count(),
        'confirmed_orders': orders.filter(status='CONFIRMED').count(),
        'picked_orders': orders.filter(status='PICKED').count(),
        'delivered_orders': orders.filter(status='DELIVERED').count(),
    }
    return render(request, 'stores/manager_dashboard.html', context)

@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > item.stock:
        messages.error(request, 'Not enough stock available.')
        return redirect('stores:items_list')
    
    # Get or create cart for user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        item=item,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{item.name} added to cart.')
    return redirect('stores:items_list')

@login_required
def cart_view(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart_items = []
    
    return render(request, 'stores/cart.html', {
        'cart_items': cart_items,
        'total_amount': sum(item.subtotal for item in cart_items)
    })

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > cart_item.item.stock:
        messages.error(request, 'Not enough stock available.')
        return redirect('stores:cart')
    
    cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, 'Cart updated successfully.')
    return redirect('stores:cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    messages.success(request, 'Item removed from cart.')
    return redirect('stores:cart')

def store_detail(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    return render(request, 'stores/store_detail.html', {'store': store})

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, 'stores/item_detail.html', {'item': item})

@login_required
def manager_orders(request, store_id):
    store = get_object_or_404(Store, id=store_id, manager=request.user)
    cart_items = CartItem.objects.filter(item__store=store).select_related('cart__user', 'item')

    context = {
        'cart_items': cart_items,
        'store': store,
    }
    return render(request, 'stores/manager_orders.html', context)