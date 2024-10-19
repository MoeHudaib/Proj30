import random
from .models import Inventory, Stock, InventoryLocation
from django.db import connection
import pandas as pd
import plotly.express as px
import plotly.io as pio
from django.shortcuts import get_object_or_404
from .models import Stock, OrderRequisition, MaterialOrder,MaterialOrderRequisition, MaterialOrderReport, MaterialOutbound, MaterialInbound
from django.db import transaction
from django.forms import formset_factory
from .forms import MaterialOrderForm, MaterialOrderFormNew, MaterialInboundForm, MaterialOutboundForm
from django.contrib import messages

MaterialOrderFormset = formset_factory(MaterialOrderFormNew, extra=3, can_delete=True)
MaterialOrderFormNewSet = formset_factory(MaterialOrderFormNew, extra=2, can_delete=True)
MaterialInboundFormset = formset_factory(MaterialInboundForm, extra = 3, can_delete=True)
MaterialOutboundFormset = formset_factory(MaterialOutboundForm, extra=3, can_delete=True)

def process_material_order_formset(formset, request):
    messages_list = []
    counter = 1

    if formset.is_valid():
        for form in formset:
            material = form.cleaned_data.get('material')
            quantity = form.cleaned_data.get('quantity')
            exp_date = form.cleaned_data.get('expiration_date')
            if material and quantity and exp_date:
                created, _ = MaterialOrder.objects.update_or_create(
                    material=material,
                    expiration_date=exp_date,
                    defaults={'quantity': quantity}
                )
                if created:
                    messages_list.append(f'All Good BB {counter}')
                    counter += 1
                    continue

                else:
                    messages_list.append(f'Object is not created {counter}')
                    counter += 1
                    continue
            else:
                messages_list.append(f'Prob Your date is invalid {counter}')
            counter += 1
            continue
    else:
        messages_list.append(f'There is a Problem with your Form {counter}')
    for message in messages_list:
        messages.add_message(request, messages.INFO, message)
    return messages_list

def process_move_stock(form, formset, user):
    with transaction.atomic():
        instance = form.save(commit=False)
        instance.responsible_staff = user
        instance.save()

        messages_list = []
        success = True

        for form in formset:
            if not form.cleaned_data:
                continue

            material = form.cleaned_data.get('material')
            quantity = form.cleaned_data.get('quantity')
            exp_date = form.cleaned_data.get('expiration_date')  # Corrected

            if material and quantity is not None: # Ensure quantity is not None
                stock = get_object_or_404(Stock, id=material.id)

                if instance.movement_type == "procurement" and exp_date:

                    # Create or update MaterialOrder instance
                    material_order, created = MaterialOrder.objects.update_or_create(
                        material=material,
                        move_stock=instance,
                        expiration_date=exp_date,
                        defaults={'quantity': quantity}  # Update quantity if exists
                    )
                    material_order_report, created_ = MaterialOrderReport.objects.update_or_create(
                        material=material,
                        move_stock=instance,
                        expiration_date=exp_date,
                        defaults={'quantity': quantity}  # Update quantity if exists
                    )
                    if created and created_:
                        messages_list.append(f'Procurement for {material.name} has been successfully created.')
                    else:
                        messages_list.append(f'Procurement for {material.name} has been successfully updated.')

                elif instance.movement_type == "fulfillment":
                    if not instance.order_requisition_number.done:     
                        if stock.stocks_committed >= quantity:
                            material_order_report, created_ = MaterialOrderReport.objects.update_or_create(
                                material=material,
                                move_stock=instance,
                                user = instance.order_requisition_number.staff,
                                defaults={'quantity': quantity}  # Update quantity if exists
                            )

                            # Create or update MaterialOrder instance
                            material_orders = MaterialOrder.objects.filter(material = material).order_by('expiration_date')
                            for material in material_orders:
                                if material.quantity > 0:
                                    if  quantity> 0 and material.quantity > quantity:
                                        material.quantity -= quantity
                                        material.number_sold +=quantity
                                        material.save()
                                        print(material.quantity)
                                        quantity = 0
                                        break
                                    elif  quantity> 0 and material.quantity < quantity:
                                        quantity -= material.quantity
                                        material.number_sold += material.quantity
                                        material.quantity = 0
                                        print(quantity)
                                        material.save()
                                        continue
                                    elif  quantity > 0 and material.quantity == quantity:
                                        material.number_sold += quantity
                                        quantity = 0
                                        material.quantity = 0
                                        material.save()
                                        break
                                        

                            if created_:
                                messages_list.append(f'Order Voucher for {material.material.name} has been successfully created.')
                            else:
                                messages_list.append(f'Order Voucher for {material.material.name} has been successfully updated.')
                        else:
                            messages_list.append(f'The quantity in Order Voucher for {stock.name} is greater than the available stock.')
                            success = False
                    else:
                        messages_list.append('The Order Voucher has already been created!')
                        success = False

                else:
                    messages_list.append('Unsupported Transaction!')
                    success = False

        # Mark OrderRequisition as done if applicable
        if instance.order_requisition_number and not instance.order_requisition_number.done:
            po = get_object_or_404(OrderRequisition, id=instance.order_requisition_number.id)
            po.done = True
            po.save()

        # Update total price based on material orders
        material_orders = MaterialOrder.objects.filter(move_stock=instance)
        instance.total_price = sum(
            material.quantity * material.material.unit_cost
            for material in material_orders
        )
        instance.save()

        if success:
            messages_list.append('All transactions have been processed successfully.')
        else:
            if not any('successfully' in msg for msg in messages_list):
                messages_list.append('Some transactions could not be processed due to errors.')

    return messages_list

def process_inbound(form, formset, user):
    with transaction.atomic():
        instance = form.save(commit=False)
        instance.responsible_staff = user
        instance.save()

        messages_list = []
        success = True

        for form in formset:
            if not form.cleaned_data:
                continue

            material = form.cleaned_data.get('material')
            quantity = form.cleaned_data.get('quantity')
            exp_date = form.cleaned_data.get('expiration_date')  # Corrected

            if material and quantity and exp_date is not None: # Ensure quantity is not None
                material_inbound, created = MaterialInbound.objects.update_or_create(
                    inbound=instance,
                    material=material,
                    expiration_date=exp_date,
                    defaults={'quantity': quantity}  # Update quantity if exists
                )
                material_inbound_report, created_ = MaterialOrderReport.objects.update_or_create(
                    inbound=instance,
                    material=material,
                    expiration_date=exp_date,
                    user = user,
                    defaults={'quantity': quantity}  # Update quantity if exists
                )
                if created and created_:
                    messages_list.append(f'Procurement for {material.name} has been successfully created.')
                    stock = get_object_or_404(Stock, pk = material.id)
                    stock.save()
                else:
                    messages_list.append(f'Procurement for {material.name} has been successfully updated.')

        if success:
            messages_list.append('All transactions have been processed successfully.')
        else:
            if not any('successfully' in msg for msg in messages_list):
                messages_list.append('Some transactions could not be processed due to errors.')

    return messages_list

def process_outbound(form, formset, user):
    with transaction.atomic():
        instance = form.save(commit=False)
        instance.responsible_staff = user
        instance.save()

        messages_list = []
        success = True
        print(-1)
        for form in formset:
            if not form.cleaned_data:
                print(0)
                continue
                
            print(1)
            material = form.cleaned_data.get('material')
            quantity = form.cleaned_data.get('quantity')

            if material and quantity is not None: # Ensure quantity is not None
                print(2)
                stock = get_object_or_404(Stock, id=material.id)
                if not instance.order_requisition_number.done: 
                    print(3)    
                    if stock.stocks_committed >= quantity:
                        print(4)
                        material_order_report, created_ = MaterialOutbound.objects.update_or_create(
                            material=material,
                            outbound=instance,
                            defaults={'quantity': quantity}  # Update quantity if exists
                        )

                        #Continue from where should you decrease stocks on hand 
                        material_orders = MaterialInbound.objects.filter(material = material).order_by('expiration_date')
                        for material in material_orders:
                            print(5)
                            if material.quantity > 0:
                                if  quantity> 0 and material.quantity > quantity:
                                    material.quantity -= quantity
                                    #material.number_sold +=quantity
                                    material.save()
                                    print(material.quantity)
                                    quantity = 0
                                    break
                                elif  quantity> 0 and material.quantity < quantity:
                                    quantity -= material.quantity
                                    #material.number_sold += material.quantity
                                    material.quantity = 0
                                    print(quantity)
                                    material.save()
                                    continue
                                elif  quantity > 0 and material.quantity == quantity:
                                    #material.number_sold += quantity
                                    quantity = 0
                                    material.quantity = 0
                                    material.save()
                                    break
                                    

                        if created_:
                            messages_list.append(f'Order Voucher for {material.material.name} has been successfully created.')
                        else:
                            messages_list.append(f'Order Voucher for {material.material.name} has been successfully updated.')
                    else:
                        messages_list.append(f'The quantity in Order Voucher for {stock.name} is greater than the available stock.')
                        success = False
                else:
                    messages_list.append('The Order Voucher has already been created!')
                    success = False
                # Mark OrderRequisition as done if applicable
        if instance.order_requisition_number and not instance.order_requisition_number.done:
            print(6)
            po = get_object_or_404(OrderRequisition, id=instance.order_requisition_number.id)
            po.done = True
            po.save()
            stock.save()
        if success:
            messages_list.append('All transactions have been processed successfully.')
        else:
            if not any('successfully' in msg for msg in messages_list):
                messages_list.append('Some transactions could not be processed due to errors.')

    return messages_list

# Create Order Requistion From Cart Object

def process_order_requisition(form, formset, user):
    with transaction.atomic():
        # Save the OrderRequisition instance
        instance = form.save(commit=False)
        instance.staff = user
        instance.save()

        messages_list = []
        success = True

        i = 0
        for form in formset:
            print(i)
            i +=1
        for form in formset:
            if not form.cleaned_data:
                continue

            material = form.cleaned_data.get('material')
            quantity = form.cleaned_data.get('quantity')

            if material and quantity:
                stock = get_object_or_404(Stock, id=material.id)
                
                # Handle stock adjustment and MaterialOrder creation
                if instance:
                    
                    MaterialOrderRequisition.objects.create(
                        material=material,
                        order_requisition=instance,
                        quantity = quantity,
                    )
                    stock.stocks_committed += quantity
                    stock.save()
                    messages_list.append(f'Order Voucher for {material.name} has been successfully processed.')

                else:
                    messages_list.append('Order Requisition could not be processed.')
                    success = False
        material_orders = MaterialOrderRequisition.objects.filter(order_requisition=instance)
        instance.total_price = sum(
                material.quantity * material.material.unit_cost
                for material in material_orders
            )
        instance.save()
        if success:
            messages_list.append('All transactions have been processed successfully.')
        else:
            if not any('successfully' in msg for msg in messages_list):
                messages_list.append('Some transactions could not be processed due to errors.')

    return messages_list

def generate_rgba_colors(n, seed=210):
    colors = []
    random.seed(seed)  # Set the seed for reproducibility
    for _ in range(n):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        a = 1  # Fixed alpha value
        color = f'rgba({r}, {g}, {b}, {a})'
        colors.append(color)
    return colors

def prepare_inventory_data():
    inventories = Inventory.objects.all()
    stocks = Stock.objects.all()
    inventory_data = []
    stock_counter = 0
    for inventory in inventories:
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

        inventory_data.append({
            'inventory': inventory,
            'rows': rows,
        })

    return {
        'inventory_data': inventory_data,
        'stocks': stocks,
    }

def fetch_top_stocks():
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM dashboard_stock ORDER BY sn DESC LIMIT 10;')
        rows = cursor.fetchall()
        # Assuming the columns are known and in the correct order
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
    return df

def top_10_stocks_chart():
    stocks = Stock.objects.raw('SELECT * FROM dashboard_stock;')  # Fetch all stock items
    data = fetch_top_stocks()  # Fetch the top 10 selling items data
    chart_type = 'bar'

    try:
        # Check if data is not empty and has the necessary columns
        if not data.empty and 'name' in data.columns and 'sn' in data.columns:
            if chart_type == 'bar':
                fig = px.bar(
                    data,
                    x='name',  # Column name for the x-axis (item names)
                    y='sn',  # Column name for the y-axis (selling numbers)
                    title='Top 10 Selling Items',
                    color='name'  # Optional: Color bars by item names
                )
                
                fig.update_layout(
                    xaxis_title='Item Name',
                    yaxis_title='Selling Number'
                )
                
            # Convert Plotly figure to HTML
            plot_html = pio.to_html(fig, full_html=False)
        else:
            plot_html = None
            context ={
                'error': 'Data is empty or missing necessary columns.',
                'chart_type': chart_type,
                'stocks':stocks,
            }
            return context

    except Exception as e:
        plot_html = None
        context =  {
            'error': f'Error generating plot: {e}',
            'chart_type': chart_type,
            'stocks':stocks,
        }
        return context

    context = {
        'plot_html': plot_html,
        'chart_type': chart_type,
        'stocks':stocks,
    }
    return context
