# Generated by Django 5.2 on 2025-05-16 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_sys', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='id',
        ),
        migrations.AddField(
            model_name='product',
            name='product_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
