from django.urls import path
from . import views

app_name='stores'

urlpatterns = [
    path('', views.items_list, name='items_list'),
    path('stores/', views.stores_list, name='stores'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/add-item/', views.add_item, name='add_item'),
    path('items/', views.items_list, name='items_list'),
    path('add-item/', views.add_item, name='add_item'),
    # path('orders/', views.orders_list, name='orders_list'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('<int:store_id>/', views.store_detail, name='store_detail'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'), 
    path('manager/orders/<int:store_id>/', views.manager_orders, name='manager_orders'), 
]

