# Generated by Django 3.2.14 on 2022-08-17 07:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0104_auto_20220816_1022'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalauthbook',
            name='asset',
        ),
        migrations.RemoveField(
            model_name='historicalauthbook',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicalauthbook',
            name='systemuser',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='assets',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='nodes',
        ),
        migrations.RemoveField(
            model_name='systemuser',
            name='users',
        ),
        migrations.AlterUniqueTogether(
            name='authbook',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='authbook',
            name='asset',
        ),
        migrations.RemoveField(
            model_name='authbook',
            name='systemuser',
        ),
        migrations.DeleteModel(
            name='Cluster',
        ),
        migrations.DeleteModel(
            name='AdminUser',
        ),
        migrations.DeleteModel(
            name='HistoricalAuthBook',
        ),
        migrations.DeleteModel(
            name='AuthBook',
        ),
    ]
