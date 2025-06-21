from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('create/', views.create_order, name='create_order'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Store Manager URLs
    path('store/orders/', views.store_orders, name='store_orders'),
    path('store/orders/<int:order_id>/confirm/', views.confirm_order, name='confirm_order'),
    
    # Delivery Agent URLs
    path('delivery/orders/', views.delivery_agent_orders, name='delivery_agent_orders'),
    path('delivery/orders/<int:order_id>/status/<str:status>/', views.update_order_status, name='update_order_status'),
    path('delivery/location/update/', views.update_location, name='update_location'),
    path('delivery/dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/accept/<int:order_id>/', views.accept_delivery, name='accept_delivery'),
    path('delivery/status/<int:order_id>/', views.update_delivery_status, name='update_delivery_status'),
] 