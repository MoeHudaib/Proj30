from django.shortcuts import render,redirect,get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import Stock, Inventory, InventoryLocation, OrderRequisition, MoveStock, MaterialOrder, MaterialOrderRequisition, MaterialOrderReport
from .models import MaterialInbound, CartItem
from .forms import CreateStockForm, UpdateStockForm, CategoryForm, OutboundForm, InboundForm
from django.contrib import messages #Flash messages
from .forms import MoveStockForm, OrderRequisitionForm
from .utils import generate_rgba_colors, prepare_inventory_data, top_10_stocks_chart, process_move_stock, MaterialOrderFormset
from .utils import process_order_requisition, MaterialOrderFormNewSet, process_material_order_formset, MaterialOutboundFormset, MaterialInboundFormset, process_inbound, process_outbound
from django.db import models
from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Sum, F

# Create your views here. JUST TO LET YOU KNOW MOHAMMAD, Making Flash Messages resolve the refresh browser issue
#""""""""  DUPLICATED VALUES """"""""""
#Make an AI Model That predict the threshold of a product based on its sales frequency
#Make locations having value that is set to 0 and when adding a product into that location it must be increased by 1

@login_required(login_url='user:user-login')
@require_POST
def report_stock_issue(request):
    issue_type = request.POST.get('issue_type')  # 'low_stock' or 'expiry'
    items = request.POST.getlist('items')  # List of item IDs

    if not items:
        return JsonResponse({'status': 'error', 'message': 'No items selected.'}, status=400)

    if issue_type == 'low_stock':
        subject = 'Low Stock Report'
        item_list = ", ".join(items)  # Join IDs for clarity
        message = f'The following items are low in stock: {item_list}'
    elif issue_type == 'expiry':
        subject = 'Expiration Date Report'
        item_list = ", ".join(items)  # Join IDs for clarity
        message = f'The following items are nearing expiration: {item_list}'
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid issue type.'}, status=400)

    # Send email
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],  # Ensure ADMIN_EMAIL is set in your settings
            fail_silently=False,
        )
        return JsonResponse({'status': 'success', 'message': 'Report submitted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error sending email: {str(e)}'}, status=500)

def test(request):
    formset = MaterialOrderFormNewSet(request.POST or None)
    
    if request.method == 'POST':
        process_material_order_formset(formset, request)
        return redirect('dashboard:dashboard-index')
    
    return render(request, 'dashboard/test.html', {'formset': formset})

@login_required(login_url='user:user-login')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard:dashboard-index')
    else:
        form = CategoryForm()
    
    return render(request, 'dashboard/add_category.html', {'form': form})

@login_required(login_url='user:user-login')
def staff_order_history(request):

    orders = OrderRequisition.objects.filter(staff=request.user)
    completed_orders = orders.filter(done=True)

    context = {
        'orders': completed_orders,
    }
    return render(request, 'dashboard/orders_history.html', context)

@login_required(login_url='user:user-login')
def index(request):
    # Get all OrderRequisitions
    orders = OrderRequisition.objects.all().order_by('-date_created')
    pending_orders = OrderRequisition.objects.filter(done=False).order_by('-date_created')
    completed_orders = OrderRequisition.objects.filter(done = True).order_by('-date_created')
    # Fetch reports and stocks
    material_order_report = MaterialOrderReport.objects.filter(user=request.user)
    low_stock_items = Stock.objects.filter(stocks_availability__lt=F('threshold')).order_by('stocks_availability')

    # Define your expiry alert threshold
    expiring_soon_threshold = 30  
    expiring_items = MaterialInbound.objects.filter(
        expiration_date__lte=date.today() + timedelta(days=expiring_soon_threshold),
        active=True
    ).order_by('expiration_date')

    # Prepare data for chart
    order_labels = []
    order_data = []
    colors = []
    total_quantity = 0

    # Generate a distinct color for each order
    order_count = orders.count()
    color_list = generate_rgba_colors(order_count)

    for i, order in enumerate(orders):
        material_orders = MaterialOrderRequisition.objects.filter(order_requisition=order)
        order_total = material_orders.aggregate(total=Sum('quantity'))['total']

        if order_total:
            order_labels.append(f'Order ID {order.id}')
            order_data.append(order_total)
            total_quantity += order_total
            
            # Assign a color to each order
            colors.append(color_list[i])

    # Generate colors for products
    product_count = Stock.objects.count()+1
    p_color_list = generate_rgba_colors(product_count)

    context = {
        'pending_orders':pending_orders,
        'orders': orders,
        'p_color_list': p_color_list,
        'products': Stock.objects.all(),
        'order_labels': order_labels,
        'order_data': order_data,
        'colors': colors,
        'expiring_items': expiring_items,
        'low_stock_items': low_stock_items,
        'inventoris': Inventory.objects.all(),
        'material_order_report': material_order_report,
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required(login_url='user:user-login')
def staff(request):
    workers = User.objects.all()

    context = {
        'workers':workers,
    }
    return render(request, 'dashboard/staff.html', context)

@login_required(login_url='user:user-login')
def staff_detail(request, pk):
    worker = get_object_or_404(User,id=pk)

    context = {
        'worker':worker
    }
    return render(request, 'dashboard/staff_detail.html',context)

@login_required(login_url='user:user-login')
def product(request):
    context = top_10_stocks_chart()
    return render(request, 'dashboard/product.html', context)

@login_required(login_url='user:user-login')
def create_product(request):
    if request.method == "POST":
        form = CreateStockForm(request.POST, request.FILES)
        if not form.is_valid():
            print(form.errors)  # This will print the errors to the console
        if form.is_valid():
            form.save()
            stock_name = form.cleaned_data.get('name')
            messages.success(request, f'{stock_name} has been successfully added.')
            return redirect('dashboard:dashboard-product')
        else:
            messages.warning(request, 'Form is not valid. Please correct the errors below.')
            return render(request, 'dashboard/create_product.html', {'form': form})
    else:
        form = CreateStockForm()
        return render(request, 'dashboard/create_product.html', {'form': form})

@login_required(login_url='user:user-login')
def delete_product(request, pk):
    if request.method == 'POST':
        stock = get_object_or_404(Stock, id=pk)
        stock_name = stock.name
        stock.delete()
        messages.success(request, f'{stock_name} has been successfully deleted.')
        return redirect('dashboard:dashboard-index')
    else:
        stock = get_object_or_404(Stock, id=pk)
        return render(request, 'dashboard/delete_product.html',{'stock':stock})

@login_required(login_url='user:user-login')
def update_product(request, pk):
    stock = get_object_or_404(Stock, id = pk)
    if request.method == 'POST':
        form = UpdateStockForm(request.POST, request.FILES, instance=stock)
        if form.is_valid():
            form.save()
            stock_name = form.cleaned_data.get('name')
            messages.success(request, f'{stock_name} has been successfully Updated.')
            return redirect('dashboard:dashboard-product')
        else:
            form = UpdateStockForm(instance=stock)
            messages.warning(request, 'Form is not valid. Please correct the errors below.')
            return render(request, 'dashboard/update_product.html', {'form': form})
    else:
        form = UpdateStockForm(instance=stock)
        return render(request, 'dashboard/update_product.html',{'form':form, 'stock':stock})

@login_required(login_url='user:user-login')
def order(request):
    orders = OrderRequisition.objects.all().order_by('-date_created')

    context = {
        'orders':orders
    }
    return render(request, 'dashboard/order.html',context)

@login_required(login_url='user:user-login')
def make_order(request):
    if request.method == 'POST':
        form = OrderRequisitionForm(request.POST)
        formset = MaterialOrderFormNewSet(request.POST)
        if form.is_valid() and formset.is_valid():
            messages_list = process_order_requisition(form, formset, request.user)
            for message in messages_list:
                messages.add_message(request, messages.INFO, message)
            return redirect('dashboard:dashboard-index')
        else:
            messages.add_message(request, messages.WARNING, 'There was an error with your submission.')
            return redirect('dashboard:dashboard-index')
    else:
        form = OrderRequisitionForm()
        formset = MaterialOrderFormNewSet()
        return render(request, 'dashboard/make_order.html', {'form': form, 'formset': formset})

@login_required(login_url='user:user-login')
def print_order_requisition(request, pk):
    order_requisition = get_object_or_404(OrderRequisition, pk=pk)
    pdf = order_requisition.generate_pdf()
    
    if pdf is None:
        return HttpResponse("Error generating PDF", status=500)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_requisition_{pk}.pdf"'
    return response

@login_required(login_url='user:user-login')
def show_inventory_layout(request, pk, row_id=None):
    inventory = get_object_or_404(Inventory, id=pk)

    if row_id:
        columns = []
        for column_num in range(1, inventory.columns_number + 1):
            total_layers = inventory.layers_number
            reserved_layers = InventoryLocation.objects.filter(
                inventory=inventory, row=row_id, column=column_num, reserved=True
            ).count()
            available_layers = total_layers - reserved_layers
            columns.append({
                'column': column_num,
                'empty_spaces': available_layers
            })

        locations = InventoryLocation.objects.filter(
            inventory=inventory, row=row_id
        ).order_by('column', 'layer')

        return render(request, 'dashboard/row_detail.html', {
            'inventory': inventory,
            'row_id': row_id,
            'columns': columns,
            'locations': locations
        })

    rows = []
    for row_num in range(1, inventory.rows_number + 1):
        total_spaces = inventory.columns_number * inventory.layers_number
        reserved_spaces = InventoryLocation.objects.filter(
            inventory=inventory, row=row_num, reserved=True
        ).count()
        available_spaces = total_spaces - reserved_spaces
        rows.append({
            'row': row_num,
            'empty_spaces': available_spaces
        })

    return render(request, 'dashboard/row_detail.html', {
        'inventory': inventory,
        'rows': rows
    })

@login_required(login_url='user:user-login')
def inventory(request):
    context = prepare_inventory_data()
    return render(request, 'dashboard/inventory.html', context)

@login_required(login_url='user:user-login')
def show_column_layout(request, pk, row_id, column_id):
    inventory = get_object_or_404(Inventory, id=pk)

    layers = []
    for layer_id in range(1, inventory.layers_number + 1):
        reserved_layer = InventoryLocation.objects.filter(
            inventory=inventory, row=row_id, column=column_id, layer=layer_id, reserved=True
        ).count()
        available_layer = 1 - reserved_layer

        # Fetch the stock associated with this layer, if any
        location = InventoryLocation.objects.filter(
            inventory=inventory, row=row_id, column=column_id, layer=layer_id, reserved=True
        ).first()
        stock_id = location.stock.id if location and location.stock else None
        layers.append({
            'layer_id': layer_id,
            'available_layer': available_layer,
            'stock_id': stock_id
        })
    
    layers = list(reversed(layers))
    locations = InventoryLocation.objects.filter(
        inventory=inventory, row=row_id, column=column_id
    ).order_by('layer')

    return render(request, 'dashboard/column_detail.html', {
        'inventory': inventory,
        'row_id': row_id,
        'column_id': column_id,
        'layers': layers,
        'locations': locations
    })

# if stock movement is fulfillment it must be created based on Order Requisition and the quantity in
#  fulfillment transaction must match the quantity in PO if applicable if not the less only
@login_required(login_url='user:user-login')
def move_stock_view(request):
    if request.method == 'POST':
        form = MoveStockForm(request.POST)
        formset = MaterialOrderFormset(request.POST)
        
        if form.is_valid() and formset.is_valid():
            messages_list = process_move_stock(form, formset, request.user)
            for message in messages_list:
                messages.add_message(request, messages.INFO, message)
            return redirect('dashboard:dashboard-index')
        else:
            messages.warning(request, 'There was a problem with your submission. Please correct the errors below.')
    
    else:
        form = MoveStockForm()
        formset = MaterialOrderFormset()
    
    return render(request, 'dashboard/move_stocks.html', {
        'form': form,
        'formset': formset,
    })

@login_required(login_url='user:user-login')
def inbound(request):
    if request.method == 'POST':
        form = InboundForm(request.POST)
        formset = MaterialInboundFormset(request.POST)

        if form.is_valid() and formset.is_valid():
            messages_list = process_inbound(form, formset, request.user)
            for message in messages_list:
                messages.add_message(request, messages.INFO, message)
                return redirect('dashboard:dashboard-product')
        else:
            messages.warning(request, 'There was a problem with your submission. Please correct the errors below.')
            return redirect('dashboard:dashboard-product')

    else:
        form = InboundForm()
        formset = MaterialInboundFormset()
    
    return render(request, 'dashboard/inbound.html', {
        'form': form,
        'formset': formset,
    })

@login_required(login_url='user:user-login')
def outbound(request):
    if request.method == 'POST':
        form = OutboundForm(request.POST)
        formset = MaterialOutboundFormset(request.POST)

        if form.is_valid() and formset.is_valid():
            messages_list = process_outbound(form, formset, request.user)
            for message in messages_list:
                messages.add_message(request, messages.INFO, message)
                return redirect('dashboard:dashboard-product')
        else:
            messages.warning(request, 'There was a problem with your submission. Please correct the errors below.')
            return redirect('dashboard:dashboard-product')
    else:        
        form = OutboundForm()
        formset = MaterialOutboundFormset()
    
    return render(request, 'dashboard/outbound.html', {
        'form': form,
        'formset': formset,
    })

@login_required(login_url='user:user-login')
def stock_movement_history(request):
    smhs = MoveStock.objects.all().order_by('-id')

    context = {
        'smhs':smhs,
    }
    return render(request, 'dashboard/stock_movement_history.html', context)

@login_required(login_url='user:user-login')
def print_move_stock(request, pk):
    move_stock = get_object_or_404(MoveStock, pk=pk)
    pdf = move_stock.generate_pdf()
    
    if pdf is None:
        return HttpResponse("Error generating PDF", status=500)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="stock_movement_{pk}.pdf"'
    return response

@login_required
def stock_page(request, pk):
    prodcut = get_object_or_404(Stock, id=pk)
    material_orders = MaterialInbound.objects.filter(material=prodcut, active=True).order_by('expiration_date')
    material_order_requisitions = MaterialOrderRequisition.objects.filter(
        material=prodcut,
        order_requisition__done=True,
        active = False
    )
    sn = sum(material.quantity for material in material_orders)
    # Initialize revenue and sales frequency lists for each month
    revenue_data = [0] * 12
    sales_frequency_data = [0] * 12

    # Loop through material orders to populate revenue and frequency data
    for order in material_order_requisitions:
        month = order.sold_date.month - 1  # Zero-indexed month
        revenue_data[month] += order.material.unit_cost * order.quantity
        sales_frequency_data[month] += order.quantity

    context = {
        'product': prodcut,
        'material_orders': material_orders,
        'revenue_data': revenue_data,
        'sales_frequency_data': sales_frequency_data,
    }
    return render(request, 'dashboard/stock_page.html', context)

from django.http import JsonResponse
from .models import Cart, CartItem, Stock

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Stock, id=product_id)
    
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user, active=True)
    
    # Check if the product is already in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:  # If the product already exists in the cart
        cart_item.quantity += 1  # Increase quantity
    cart_item.price = product.unit_cost
    cart_item.save()

    # Update cart totals
    cart.total_items = sum(item.quantity for item in cart.cartitem_set.all())
    cart.total_price = sum(item.quantity * item.price for item in cart.cartitem_set.all())
    cart.save()

    return redirect('dashboard:cart_view')

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    if request.method == 'POST':
        new_quantity = request.POST.get("quantity")
        
        # Validate the new quantity
        if new_quantity and new_quantity.isdigit() and int(new_quantity) > 0:
            cart_item.quantity = int(new_quantity)
            cart_item.save()

            # Update cart totals
            cart = cart_item.cart
            cart.total_items = sum(item.quantity for item in cart.cartitem_set.all())
            cart.total_price = sum(item.quantity * item.price for item in cart.cartitem_set.all())
            cart.save()

            return redirect('dashboard:cart_view')
        else:
            # Handle invalid quantity input
            return render(request, 'cart/update_item.html', {
                'cart_item': cart_item,
                'error': 'Invalid quantity. Please enter a positive number.'
            })
    else:
        return render(request, 'cart/update_item.html', {'cart_item': cart_item})


@login_required
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = cart_item.cart
    cart_item.delete()

    # Update cart totals
    cart.total_items = sum(item.quantity for item in cart.cartitem_set.all())
    cart.total_price = sum(item.quantity * item.price for item in cart.cartitem_set.all())
    cart.save()

    return redirect('dashboard:cart_view')

@login_required
def cart_view(request):
    
    cart, created = Cart.objects.get_or_create(user=request.user, active=True)
    cart_items = cart.cartitem_set.all()

    return render(request, 'dashboard/cart.html', {'cart': cart, 'cart_items': cart_items})

def checkout(request, pk):
    cart = get_object_or_404(Cart, id = pk)
    cart_items = CartItem.objects.filter(cart = cart)
    