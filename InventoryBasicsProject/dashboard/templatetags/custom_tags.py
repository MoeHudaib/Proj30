from django import template
from django.contrib.auth.models import User
from dashboard.models import Stock, Inventory, InventoryLocation, OrderRequisition

register = template.Library()

@register.simple_tag
def user_count():
    return User.objects.count()

@register.simple_tag
def product_count():
    return Stock.objects.count()

@register.simple_tag
def order_count():
    return OrderRequisition.objects.count()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary."""
    return dictionary.get(key)

@register.simple_tag
def inventories():
    """
    Returns all objects from MyModel.
    """
    return Inventory.objects.all()

@register.simple_tag
def inventory_locations():
    return InventoryLocation.objects.all()

@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0
    
@register.filter
def filter_orders_by_user(orders, user):
    return orders.filter(staff=user)