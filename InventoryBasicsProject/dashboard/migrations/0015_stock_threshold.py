# Generated by Django 5.1.1 on 2024-09-19 22:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0014_remove_materialbound_in_movestock_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="stock",
            name="threshold",
            field=models.FloatField(default=0, editable=False),
            preserve_default=False,
        ),
    ]
