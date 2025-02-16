# Generated by Django 3.2.14 on 2022-10-19 03:15

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import common.db.fields


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0106_auto_20220916_1556'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutomationExecution',
            fields=[
                ('org_id',
                 models.CharField(blank=True, db_index=True, default='', max_length=36, verbose_name='Organization')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('status', models.CharField(default='pending', max_length=16)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_start', models.DateTimeField(db_index=True, null=True, verbose_name='Date start')),
                ('date_finished', models.DateTimeField(null=True, verbose_name='Date finished')),
                ('snapshot', common.db.fields.EncryptJsonDictTextField(blank=True, default=dict, null=True,
                                                                       verbose_name='Automation snapshot')),
                ('trigger', models.CharField(choices=[('manual', 'Manual trigger'), ('timing', 'Timing trigger')],
                                             default='manual', max_length=128, verbose_name='Trigger mode')),
            ],
            options={
                'verbose_name': 'Automation task execution',
            },
        ),
        migrations.CreateModel(
            name='BaseAutomation',
            fields=[
                ('created_by', models.CharField(blank=True, max_length=32, null=True, verbose_name='Created by')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date updated')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('org_id',
                 models.CharField(blank=True, db_index=True, default='', max_length=36, verbose_name='Organization')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('is_periodic', models.BooleanField(default=False, verbose_name='Periodic perform')),
                ('interval', models.IntegerField(blank=True, default=24, null=True, verbose_name='Cycle perform')),
                ('crontab', models.CharField(blank=True, max_length=128, null=True, verbose_name='Regularly perform')),
                ('accounts', models.JSONField(default=list, verbose_name='Accounts')),
                ('type', models.CharField(max_length=16, verbose_name='Type')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('comment', models.TextField(blank=True, verbose_name='Comment')),
                ('assets', models.ManyToManyField(blank=True, to='assets.Asset', verbose_name='Assets')),
                ('nodes', models.ManyToManyField(blank=True, to='assets.Node', verbose_name='Nodes')),
            ],
            options={
                'verbose_name': 'Automation task',
                'unique_together': {('org_id', 'name')},
            },
        ),
        migrations.AddField(
            model_name='label',
            name='created_by',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='Created by'),
        ),
        migrations.AddField(
            model_name='label',
            name='date_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Date updated'),
        ),
        migrations.AddField(
            model_name='label',
            name='updated_by',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='Updated by'),
        ),
        migrations.AlterField(
            model_name='platformprotocol',
            name='default',
            field=models.BooleanField(default=False, verbose_name='Default'),
        ),
        migrations.CreateModel(
            name='GatherFactsAutomation',
            fields=[
                ('baseautomation_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='assets.baseautomation')),
            ],
            options={
                'verbose_name': 'Gather asset facts',
            },
            bases=('assets.baseautomation',),
        ),
        migrations.CreateModel(
            name='PushAccountAutomation',
            fields=[
                ('baseautomation_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='assets.baseautomation')),
            ],
            options={
                'verbose_name': 'Push asset account',
            },
            bases=('assets.baseautomation',),
        ),
        migrations.CreateModel(
            name='VerifyAccountAutomation',
            fields=[
                ('baseautomation_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='assets.baseautomation')),
            ],
            options={
                'verbose_name': 'Verify asset account',
            },
            bases=('assets.baseautomation',),
        ),
        migrations.CreateModel(
            name='ChangeSecretRecord',
            fields=[
                ('created_by', models.CharField(blank=True, max_length=32, null=True, verbose_name='Created by')),
                ('updated_by', models.CharField(blank=True, max_length=32, null=True, verbose_name='Updated by')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date updated')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('old_secret', common.db.fields.EncryptTextField(blank=True, null=True, verbose_name='Old secret')),
                ('new_secret', common.db.fields.EncryptTextField(blank=True, null=True, verbose_name='Secret')),
                ('date_started', models.DateTimeField(blank=True, null=True, verbose_name='Date started')),
                ('date_finished', models.DateTimeField(blank=True, null=True, verbose_name='Date finished')),
                ('status', models.CharField(default='pending', max_length=16)),
                ('error', models.TextField(blank=True, null=True, verbose_name='Error')),
                ('account',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='assets.account')),
                ('execution',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assets.automationexecution')),
            ],
            options={
                'verbose_name': 'Change secret record',
            },
        ),
        migrations.AddField(
            model_name='automationexecution',
            name='automation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions',
                                    to='assets.baseautomation', verbose_name='Automation task'),
        ),
        migrations.CreateModel(
            name='ChangeSecretAutomation',
            fields=[
                ('baseautomation_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='assets.baseautomation')),
                ('secret_type', models.CharField(
                    choices=[('password', 'Password'), ('ssh_key', 'SSH key'), ('access_key', 'Access key'),
                             ('token', 'Token')], default='password', max_length=16, verbose_name='Secret type')),
                ('secret_strategy', models.CharField(
                    choices=[('specific', 'Specific'), ('random_one', 'All assets use the same random password'),
                             ('random_all', 'All assets use different random password')], default='specific',
                    max_length=16, verbose_name='Secret strategy')),
                ('secret', common.db.fields.EncryptTextField(blank=True, null=True, verbose_name='Secret')),
                ('password_rules', models.JSONField(default=dict, verbose_name='Password rules')),
                ('ssh_key_change_strategy', models.CharField(
                    choices=[('add', 'Append SSH KEY'), ('set', 'Empty and append SSH KEY'),
                             ('set_jms', 'Replace (The key generated by JumpServer) ')], default='add', max_length=16,
                    verbose_name='SSH key change strategy')),
                ('recipients',
                 models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='Recipient')),
            ],
            options={
                'verbose_name': 'Change secret automation',
            },
            bases=('assets.baseautomation',),
        ),
    ]
