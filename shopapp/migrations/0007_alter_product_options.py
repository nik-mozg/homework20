# Generated by Django 4.0.6 on 2023-01-23 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("shopapp", "0006_order_products"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="product",
            options={"ordering": ["name", "price"]},
        ),
    ]
