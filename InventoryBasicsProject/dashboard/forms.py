from django import forms
from .models import Stock, Category, Inventory, InventoryLocation, OrderRequisition, MoveStock, MaterialOrder, Inbound, Outbound, MaterialOutbound, MaterialInbound, CartItem
from django.forms import formset_factory

class UpdateStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        exclude = ['stocks_availability', 'stocks_on_hand', 'material_order', 'stocks_committed', 'exp_date', 'sn']
        widgets = {
            'description1': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter description'}),
            'description2': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter additional description'}),
            'unit_cost': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter unit cost'}),
            'threshold': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter stock threshold'}),
            'source': forms.TextInput(attrs={'placeholder': 'Enter source'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class CreateStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            'vocab_no',
            'name',
            'description1',
            'description2',
            'unit',
            'unit_cost',
            'category',
            'image',
        ]
        widgets = {
            'description1': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter description'}),
            'description2': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter additional description'}),
            'unit_cost': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Enter unit cost'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'rows_number', 'columns_number', 'layers_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rows_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'columns_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'layers_number': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class InventoryLocationForm(forms.ModelForm):
    class Meta:
        model = InventoryLocation
        fields = ['inventory', 'row', 'column', 'layer', 'stock']
        widgets = {
            'inventory': forms.Select(attrs={'class': 'form-control'}),
            'row': forms.NumberInput(attrs={'class': 'form-control'}),
            'column': forms.NumberInput(attrs={'class': 'form-control'}),
            'layer': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.Select(attrs={'class': 'form-control'}),
            
        }

class OrderRequisitionForm(forms.ModelForm):
    class Meta:
        model = OrderRequisition
        fields = [
            'delivery_date',
            'shipped_via',
            'payment_terms'
        ]
        widgets = {
            'delivery_date': forms.SelectDateWidget(years=range(2024, 2031)),  # Adjust years as needed
        }

class MaterialOrderForm(forms.ModelForm):
    class Meta:
        model = MaterialOrder
        exclude = ['move_stock']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}), # Adjust years as needed
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['expiration_date'].required = False

class MaterialOrderFormNew(forms.Form):
    material = forms.ModelChoiceField(queryset=Stock.objects.all(), label="Material", required=False)
    quantity = forms.IntegerField(min_value=1, label="Quantity", required=False)
    expiration_date = forms.DateField(widget=forms.SelectDateWidget(), label="Expiration Date", required=False)

class InboundForm(forms.ModelForm):
    class Meta:
        model = Inbound
        fields = ['source']  # Exclude date_created and total_price

    source = forms.CharField(
        max_length=100,
        required=False,
        label="Source"
    )

class OutboundForm(forms.ModelForm):
    class Meta:
        model = Outbound
        fields = ['order_requisition_number']  # Exclude date_created and total_price


    order_requisition_number = forms.ModelChoiceField(
        queryset=OrderRequisition.objects.all(),
        required=True,
        label="Order Requisition"
    )

class MaterialOutboundForm(forms.ModelForm):
    class Meta:
        model = MaterialOutbound
        fields = ['material', 'quantity']

    material = forms.ModelChoiceField(
        queryset= Stock.objects.all(),
        required= False,
        label= "Material"
    )

    quantity = forms.IntegerField(
        min_value=1,  # Optionally enforce a minimum quantity
        required=False,  # Set to True if you want to require this field
        label="Quantity"
    )


class MaterialInboundForm(forms.ModelForm):
    class Meta:
        model = MaterialInbound
        fields = ['material', 'quantity', 'expiration_date']

    material = forms.ModelChoiceField(
        queryset= Stock.objects.all(),
        required= False,
        label= "Material"
    )

    quantity = forms.IntegerField(
        min_value=1,  # Optionally enforce a minimum quantity
        required=False,  # Set to True if you want to require this field
        label="Quantity"
    )

    expiration_date = forms.DateField(
        widget=forms.SelectDateWidget(),  # You can use a different widget if you prefer
        required=False,
        label="Expiration Date"
    )

class MoveStockForm(forms.ModelForm):
    class Meta:
        model = MoveStock
        fields = ['movement_type', 'order_requisition_number', 'exp_date', 'source']
        widgets = {
            'exp_date': forms.SelectDateWidget(years=range(2024, 2031)),  # Adjust years as needed
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        movement_type = self.initial.get('movement_type') or self.data.get('movement_type')

        if movement_type == 'fulfillment':
            self.fields['order_requisition_number'] = forms.ModelChoiceField(
                queryset=OrderRequisition.objects.filter(done=False),
                required=True,
                empty_label="Select Order Requisition"
            )
        else:
            self.fields['order_requisition_number'] = forms.ModelChoiceField(
                queryset=OrderRequisition.objects.all(),
                required=False,
                empty_label="Optional"
            )
        
        if movement_type == 'procurement':
            self.fields['exp_date'].required = True
            self.fields['source'].required = True
        else:
            self.fields['exp_date'].required = False
            self.fields['source'].required = False

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        order_requisition_number = cleaned_data.get('order_requisition_number')
        exp_date = cleaned_data.get('exp_date')
        source = cleaned_data.get('source')

        if movement_type == 'fulfillment' and order_requisition_number is None:
            self.add_error('order_requisition_number', 'This field is required when making a fulfillment.')
        elif movement_type == 'procurement':
            if exp_date is None:
                self.add_error('exp_date', 'This field is required when making a procurement.')
            if source is None:
                self.add_error('source', 'This field is required when making a procurement.')
        return cleaned_data

