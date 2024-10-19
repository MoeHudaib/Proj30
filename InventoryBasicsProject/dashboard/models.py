from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from datetime import date

class Category(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Inventory(models.Model):
    name = models.CharField(max_length=255)
    rows_number = models.IntegerField()
    columns_number = models.IntegerField()
    layers_number = models.IntegerField()

    class Meta:
        verbose_name_plural = "Inventories"

    def __str__(self):
        return self.name

class Stock(models.Model):
    UNIT_TYPES = [
        ('kg', 'Kilogram'),
        ('l', 'Liter'),
        ('m', 'Meter'),
    ]

    vocab_no = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255, null=True)
    description1 = models.TextField(null=True)
    description2 = models.TextField(null=True)
    image = models.ImageField(default= 'avatar.jpg', upload_to='stock_images/') 
    unit = models.CharField(max_length=255, choices=UNIT_TYPES, null=True)
    unit_cost = models.FloatField(null=True)
    stocks_on_hand = models.IntegerField(default=0)
    stocks_committed = models.IntegerField(default=0)
    stocks_availability = models.IntegerField(editable=False)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True)
    stored_stocks = models.IntegerField(default=0)
    exp_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)
    sn = models.IntegerField(default=0)
    threshold = models.FloatField(default=0)

    def is_low_stock(self):
        return self.stocks_availability < self.threshold
    
    def save(self, *args, **kwargs):
        if self.pk:
            material_inbounds= MaterialInbound.objects.filter(material=self)
            self.stocks_on_hand = sum(material.quantity for material in material_inbounds)
            material_orders_committed = MaterialOrderRequisition.objects.filter(
                material=self,
                order_requisition__done=False
            )
            self.stocks_committed = sum(material.quantity for material in material_orders_committed)
            material_orders_sold = MaterialOrderRequisition.objects.filter(
                material=self,
                order_requisition__done=True
            )
            self.sn = sum(material.quantity for material in material_orders_sold)

        self.stocks_availability = self.stocks_on_hand - self.stocks_committed
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class InventoryLocation(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, null=True)
    row = models.IntegerField(null=True)
    column = models.IntegerField(null=True)
    layer = models.IntegerField(null=True)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE, null=True, blank=True)
    reserved = models.BooleanField(default=True, null=True)

    class Meta:
        unique_together = ('inventory', 'row', 'column', 'layer')

    def __str__(self):
        return f"Row {self.row}, Column {self.column}, Layer {self.layer}"

class OrderRequisition(models.Model):
    SHIPPING_TYPES = [
        ('ground', 'Ground'),
    ]
    PAYMENT_TYPES = [
        ('cash', 'Cash'),
        ('credit card', 'Credit Card'),
    ]
    material_order = models.ManyToManyField('Stock', through='MaterialOrderRequisition', related_name='order_requisitions')
    inventory = models.ForeignKey('Inventory', on_delete=models.CASCADE, related_name='order_requisitions', null=True, blank=True)
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_requisitions')
    date_created = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateField()
    shipped_via = models.CharField(max_length=50, choices=SHIPPING_TYPES, null=True, blank=True)
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TYPES)
    total_price = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, default=0)
    done = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk:
            material_orders = MaterialOrderRequisition.objects.filter(order_requisition=self)
            self.total_price = sum(
                abs(material.quantity) * material.material.unit_cost
                for material in material_orders
                if material.material.unit_cost is not None
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order Requisition ID: {self.id} - Done: {self.done}'

    def generate_pdf(self):
        material_orders = MaterialOrderRequisition.objects.filter(order_requisition=self)
        context = {'order_requisition': self, 'material_orders': material_orders}
        html_string = render_to_string('temps/order_requisition_template.html', context)

        try:
            result = BytesIO()
            pdf = pisa.CreatePDF(BytesIO(html_string.encode('utf-8')), dest=result)
            if pdf.err:
                raise Exception("Error generating PDF")
            return result.getvalue()
        except Exception as e:
            # Handle the error appropriately (log it, raise, etc.)
            print(f"Failed to generate PDF: {e}")
            return None

class Outbound(models.Model):
    material_order = models.ManyToManyField('Stock', through='MaterialOutbound', related_name='outbound')
    material_order_report = models.ManyToManyField('Stock', through='MaterialOrderReport', related_name='outbound_reports')
    responsible_staff = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, default=0)
    order_requisition_number = models.ForeignKey('OrderRequisition', on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            material_orders = MaterialOrderReport.objects.filter(move_stock=self)
            self.total_price = sum(
                material.quantity * material.material.unit_cost
                for material in material_orders
                if material.material.unit_cost is not None
            )
        super().save(*args, **kwargs)

class Inbound(models.Model):
    material_inbound = models.ManyToManyField('Stock', through='MaterialInbound', related_name='inbound')
    material_inbound_report = models.ManyToManyField('Stock', through='MaterialOrderReport', related_name='inbound_reports')
    responsible_staff = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, default=0)
    exp_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            material_orders = MaterialInbound.objects.filter(inbound=self)
            self.total_price = sum(
                material.quantity * material.material.unit_cost
                for material in material_orders
                if material.material.unit_cost is not None
            )
        super().save(*args, **kwargs)

class MoveStock(models.Model):
    MOVE_TYPE = [
        ('procurement', 'Procurement'),
        ('fulfillment', 'Fulfillment'),
    ]

    material_order = models.ManyToManyField('Stock', through='MaterialOrder', related_name='move_stocks')
    material_order_report = models.ManyToManyField('Stock', through='MaterialOrderReport', related_name='move_stock_reports')
    responsible_staff = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    movement_type = models.CharField(max_length=50, choices=MOVE_TYPE)
    date_created = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, default=0)
    order_requisition_number = models.ForeignKey('OrderRequisition', on_delete=models.CASCADE, null=True, blank=True)
    exp_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            material_orders = MaterialOrderReport.objects.filter(move_stock=self)
            self.total_price = sum(
                material.quantity * material.material.unit_cost
                for material in material_orders
                if material.material.unit_cost is not None
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.movement_type

    def generate_pdf(self):
        material_orders = MaterialOrderReport.objects.filter(move_stock=self)
        context = {'move_stock': self, 'material_orders': material_orders}
        html_string = render_to_string('temps/stock_movement_template.html', context)
        result = BytesIO()
        pdf = pisa.CreatePDF(BytesIO(html_string.encode('utf-8')), dest=result)
        return result.getvalue()

class MaterialOrder(models.Model):
    move_stock = models.ForeignKey('MoveStock', on_delete=models.CASCADE, related_name='material_orders', null=True, blank=True)
    material = models.ForeignKey('Stock', on_delete=models.CASCADE)#
    quantity = models.PositiveIntegerField()#
    expiration_date = models.DateField(null=True)
    sold_date = models.DateField(null=True)#
    number_sold = models.IntegerField(default=0)#
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.material.name} - Ordered quantity: {self.quantity}'

    def save(self, *args, **kwargs):
        if self.quantity <= 0:
            self.active = False  # Set to inactive instead of deleting
        super().save(*args, **kwargs)

    def is_expiring_soon(self, days_threshold=30):
        return self.expiration_date and (self.expiration_date - date.today()).days <= days_threshold

class MaterialInbound(models.Model):
    material = models.ForeignKey('Stock', on_delete=models.CASCADE)
    inbound = models.ForeignKey('Inbound', on_delete=models.CASCADE, related_name='material_inbounds', null=True, blank=True)  # Add this line
    quantity = models.PositiveIntegerField()
    expiration_date = models.DateField(null=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.quantity <= 0:
            self.active = False  # Set to inactive instead of deleting
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.material} - {self.quantity}'
    
    def is_expiring_soon(self, days_threshold=30):
        return self.expiration_date and (self.expiration_date - date.today()).days <= days_threshold

class MaterialOutbound(models.Model):
    material = models.ForeignKey('Stock', on_delete=models.CASCADE)
    outbound = models.ForeignKey('Outbound', on_delete=models.CASCADE, related_name='material_outbounds', null=True, blank=True)  # Add this line
    quantity = models.PositiveIntegerField()
    sold_date = models.DateField(null=True)
    number_sold = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.material} - {self.quantity}'

class MaterialOrderRequisition(models.Model):
    order_requisition = models.ForeignKey('OrderRequisition', on_delete=models.CASCADE, related_name='material_orders', null=True, blank=True)
    material = models.ForeignKey('Stock', on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(null=True)
    sold_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    number_sold = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.order_requisition.done and self.active:
            self.sold_date = timezone.now()
            self.active = False
        super().save(*args, **kwargs)

class MaterialOrderReport(models.Model):
    outbound = models.ForeignKey('Outbound', models.CASCADE, related_name='material_outbound_reports', null=True, blank=True)
    inbound = models.ForeignKey('Inbound', models.CASCADE, related_name='material_inbound_reports', null=True, blank=True)
    move_stock = models.ForeignKey('MoveStock', models.CASCADE, related_name='material_order_reports', null=True, blank=True)
    material = models.ForeignKey('Stock', models.CASCADE)
    quantity = models.IntegerField()
    expiration_date = models.DateField(null=True)
    user = models.ForeignKey(User, models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.material.name} - Ordered quantity: {self.quantity}'

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    total_items = models.PositiveIntegerField(default=0, null=True, blank=True)
    total_price = models.FloatField(default=0.0, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Cart for {self.user} - Status: {self.status}"

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        ordering = ['-date_created']


class CartItem(models.Model):
    product = models.ForeignKey('Stock', on_delete=models.CASCADE, null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.FloatField(null=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Cart ID {self.cart.id if self.cart else 'N/A'}"

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ('product', 'cart')  # Ensure a product can only appear once per cart
