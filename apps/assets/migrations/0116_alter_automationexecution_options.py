# Generated by Django 3.2.16 on 2022-12-22 11:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0115_auto_20221220_1956'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='automationexecution',
            options={'permissions': [('view_changesecretexecution', 'Can view change secret execution'), ('add_changesecretexection', 'Can add change secret execution'), ('view_gatheraccountsexecution', 'Can view gather accounts execution'), ('add_gatheraccountsexecution', 'Can add gather accounts execution')], 'verbose_name': 'Automation task execution'},
        ),
    ]
