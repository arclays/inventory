# Generated by Django 5.2 on 2025-04-23 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_sys', '0005_rename_qty_productbatch_initial_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(default='pending', max_length=50),
        ),
    ]
