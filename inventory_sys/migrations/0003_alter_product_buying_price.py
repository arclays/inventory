# Generated by Django 5.1.6 on 2025-03-21 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_sys', '0002_rename_manufacturer_date_product_manufacture_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='buying_price',
            field=models.FloatField(),
        ),
    ]
