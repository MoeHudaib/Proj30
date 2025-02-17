# Generated by Django 5.1.1 on 2024-09-09 16:35

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
            ],
            options={
                "verbose_name_plural": "Categories",
            },
        ),
        migrations.CreateModel(
            name="Inventory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("rows_number", models.IntegerField()),
                ("columns_number", models.IntegerField()),
                ("layers_number", models.IntegerField()),
            ],
            options={
                "verbose_name_plural": "Inventories",
            },
        ),
        migrations.CreateModel(
            name="Stock",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("vocab_no", models.CharField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=255, null=True)),
                ("description1", models.TextField(null=True)),
                ("description2", models.TextField(null=True)),
                (
                    "unit",
                    models.CharField(
                        choices=[("kg", "Kilogram"), ("l", "Liter"), ("m", "Meter")],
                        max_length=255,
                        null=True,
                    ),
                ),
                ("unit_cost", models.FloatField(null=True)),
                ("stocks_on_hand", models.IntegerField(null=True)),
                ("stocks_committed", models.IntegerField(default=0, null=True)),
                ("stocks_availability", models.IntegerField(editable=False)),
                ("stored_stocks", models.IntegerField(default=0, null=True)),
                ("exp_date", models.DateField(null=True)),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="dashboard.category",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OrderRequisition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("material_name", models.CharField(max_length=55, null=True)),
                ("material_description", models.TextField(blank=True)),
                ("unit_type", models.CharField(blank=True, max_length=50)),
                (
                    "unit_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "customer_address",
                    models.CharField(default="None", max_length=255, null=True),
                ),
                ("customer_number", models.CharField(max_length=50, null=True)),
                ("date", models.DateTimeField(default=django.utils.timezone.now)),
                ("delivery_date", models.DateField()),
                (
                    "shipped_via",
                    models.CharField(
                        choices=[("ground", "Ground")], max_length=50, null=True
                    ),
                ),
                (
                    "payment_terms",
                    models.CharField(
                        choices=[("cash", "Cash"), ("credit card", "Credit Card")],
                        max_length=50,
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                (
                    "total_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("done", models.BooleanField(default=False)),
                (
                    "inventory",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_requisition",
                        to="dashboard.inventory",
                    ),
                ),
                (
                    "staff",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_requisition",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "material_number",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_requisition",
                        to="dashboard.stock",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveBigIntegerField()),
                (
                    "date",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "staff",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oreder",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "stock",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order",
                        to="dashboard.stock",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MoveStock",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.IntegerField()),
                (
                    "movement_type",
                    models.CharField(
                        choices=[
                            ("procurement", "Procurement"),
                            ("fulfillment", "Fulfillment"),
                        ],
                        max_length=50,
                    ),
                ),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("total_price", models.FloatField(null=True)),
                ("exp_date", models.DateField(null=True)),
                ("source", models.CharField(max_length=100, null=True)),
                (
                    "responsible_staff",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "order_requisition_number",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="dashboard.orderrequisition",
                    ),
                ),
                (
                    "stock",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="dashboard.stock",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InventoryLocation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("row", models.IntegerField(null=True)),
                ("column", models.IntegerField(null=True)),
                ("layer", models.IntegerField(null=True)),
                ("reserved", models.BooleanField(default=True, null=True)),
                (
                    "inventory",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="dashboard.inventory",
                    ),
                ),
                (
                    "stock",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_locations",
                        to="dashboard.stock",
                    ),
                ),
            ],
            options={
                "unique_together": {("inventory", "row", "column", "layer")},
            },
        ),
    ]
