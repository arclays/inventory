# Generated by Django 5.2 on 2025-04-25 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_sys', '0006_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('canceled', 'Canceled')], default='pending', max_length=20),
        ),
    ]
