from django.contrib import admin
from .models import Stock, Category, MaterialOrder, InventoryLocation, OrderRequisition, Inventory, MoveStock, MaterialOrderRequisition, MaterialOrderReport
from .models import Inbound, Outbound, MaterialInbound, MaterialOutbound
from django.contrib.auth.models import Group
# Register your models here.

admin.site.site_header = 'Dashboard'

class productAdmin(admin.ModelAdmin):
    list_display = ('name', 'category',) # Note that a tuple has a trailing comma otherwise it fails when running
    list_filter = ['category'] # Note that a list has no trailing comma

class MaterialOrderAdmin(admin.ModelAdmin):
    list_display = ('material', 'quantity',)
    list_filter = ('material', 'quantity',)

class MaterialOrderReportInline(admin.TabularInline):
    model = MaterialOrderReport
    extra = 1  # Number of empty forms to display
    fields = ('material', 'quantity', 'expiration_date')
    readonly_fields = ('material', 'quantity', 'expiration_date')

class MoveStockAdmin(admin.ModelAdmin):
    list_display = ('movement_type', 'date_created', 'total_price', 'responsible_staff')
    inlines = [MaterialOrderReportInline]  # Include the inline for material orders

    # Optionally, you can also add search and filter options
    search_fields = ('movement_type', 'responsible_staff__username')
    list_filter = ('movement_type', 'responsible_staff')

admin.site.register(Stock, productAdmin)
admin.site.register(Category)
admin.site.register(MaterialOrder, MaterialOrderAdmin)
admin.site.register(InventoryLocation)
admin.site.register(OrderRequisition)
admin.site.register(Inventory)
admin.site.register(MoveStock, MoveStockAdmin)
admin.site.register(MaterialOrderRequisition)
admin.site.register(MaterialOrderReport)
admin.site.register(Inbound)
admin.site.register(Outbound)
admin.site.register(MaterialInbound)
admin.site.register(MaterialOutbound)
#This is how you unregister something from the admin site and it's based on your project scenario
#admin.site.unregister(Group)