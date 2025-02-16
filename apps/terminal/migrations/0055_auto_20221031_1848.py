# Generated by Django 3.2.14 on 2022-10-31 10:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('terminal', '0054_auto_20221027_1125'),
    ]

    operations = [
        migrations.AddField(
            model_name='applet',
            name='hosts',
            field=models.ManyToManyField(through='terminal.AppletPublication', to='terminal.AppletHost', verbose_name='Hosts'),
        ),
        migrations.AddField(
            model_name='applethost',
            name='date_inited',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date inited'),
        ),
        migrations.AddField(
            model_name='applethost',
            name='inited',
            field=models.BooleanField(default=False, verbose_name='Inited'),
        ),
        migrations.AddField(
            model_name='applethostdeployment',
            name='date_finished',
            field=models.DateTimeField(null=True, verbose_name='Date finished'),
        ),
        migrations.AddField(
            model_name='applethostdeployment',
            name='date_start',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Date start'),
        ),
        migrations.AlterField(
            model_name='appletpublication',
            name='applet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='publications', to='terminal.applet', verbose_name='Applet'),
        ),
        migrations.AlterField(
            model_name='appletpublication',
            name='host',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='publications', to='terminal.applethost', verbose_name='Host'),
        ),
    ]
