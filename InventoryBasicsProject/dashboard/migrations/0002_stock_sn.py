# Generated by Django 5.1.1 on 2024-09-16 12:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="stock",
            name="sn",
            field=models.IntegerField(null=True),
        ),
    ]
