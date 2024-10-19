# your_app/management/commands/refresh_data.py

from django.core.management.base import BaseCommand
from dashboard.models import Stock, MoveStock, OrderRequisition, MaterialOrder, MaterialOrderRequisition # Import your models

class Command(BaseCommand):
    help = 'Refresh data in the database'

    def handle(self, *args, **kwargs):
        # Example: refresh stock availability
        stocks = Stock.objects.all()
        for stock in stocks:
            stock.save()  # or update specific fields as necessary
        self.stdout.write(self.style.SUCCESS('Successfully refreshed data'))
        
        ms = MoveStock.objects.all()
        for m in ms:
            m.save()  # or update specific fields as necessary
        self.stdout.write(self.style.SUCCESS('Successfully refreshed data'))
        
        orders = OrderRequisition.objects.all()
        for order in orders:
            order.save()  # or update specific fields as necessary
        self.stdout.write(self.style.SUCCESS('Successfully refreshed data'))

        mos = MaterialOrder.objects.all()
        for mo in mos:
            mo.save()  # or update specific fields as necessary
        self.stdout.write(self.style.SUCCESS('Successfully refreshed data'))

        mors = MaterialOrderRequisition.objects.all()
        for mor in mors:
            mor.save()
        self.stdout.write(self.style.SUCCESS('Successfully refreshed data'))

