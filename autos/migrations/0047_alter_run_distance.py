# Generated by Django 5.1.7 on 2025-06-06 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autos', '0046_alter_run_distance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='distance',
            field=models.FloatField(null=True),
        ),
    ]
