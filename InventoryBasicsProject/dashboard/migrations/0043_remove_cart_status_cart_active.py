# Generated by Django 5.1.1 on 2024-10-17 18:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0042_alter_cartitem_options_cartitem_date_created_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cart",
            name="status",
        ),
        migrations.AddField(
            model_name="cart",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]
