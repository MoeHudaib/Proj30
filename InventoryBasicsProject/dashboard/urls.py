from . import views
from django.urls import path

app_name = "dashboard"

urlpatterns = [
    path('',views.index, name = 'dashboard-index'),
    path('inventory/', views.inventory, name='inventory'),
    path('staff/',views.staff,name="dashboard-staff"),
    path('staff/detail/<int:pk>/',views.staff_detail,name="dashboard-staff-detail"),
    path('product/',views.product,name="dashboard-product"),
    path('order/',views.order,name="dashboard-order"),
    path('create-order/', views.make_order, name='make-order'),
    path('create-product', views.create_product, name="create-product"),
    path('product/delete/<int:pk>/', views.delete_product,name='delete-product'),
    path('product/update/<int:pk>/',views.update_product,name='update-product'),
    path('<int:pk>/<int:row_id>/', views.show_inventory_layout, name='show_inventory_layout'),
    path('<int:pk>/<int:row_id>/<int:column_id>/', views.show_column_layout, name='show_column_layout'),
    path('inbound/', views.inbound, name='inbound'),
    path('outbound/', views.outbound, name='outbound'),
    path('move/', views.move_stock_view, name ='move_stock_view'),
    path('add_categ/', views.add_category, name='add_category'),
    path('print/<int:pk>/', views.print_order_requisition, name='print_order_requisition'),
    path('print-sm/<int:pk>/', views.print_move_stock, name='print_move_stock'),
    path('report/', views.stock_movement_history, name='stock_movement_history'),
    path('report_stock_issue/', views.report_stock_issue, name='report_stock_issue'),
    path('oh/', views.staff_order_history, name = 'orders-history'),
    path('test/', views.test, name='test'),
    path('sp/<int:pk>/', views.stock_page, name='stock_page'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/', views.cart_view, name='cart_view'),  # View to display the cart
]