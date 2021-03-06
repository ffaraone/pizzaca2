# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-29 15:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CA',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CN', models.CharField(help_text='CA Common Name', max_length=255, verbose_name='Common Name')),
                ('O', models.CharField(help_text='Organization info', max_length=255, verbose_name='Organization')),
                ('OU', models.CharField(help_text='Organizational unit', max_length=255, verbose_name='Organizational Unit')),
                ('C', models.CharField(choices=[('ES', 'Spain'), ('IT', 'Italy'), ('GB', 'United Kingdom'), ('US', 'United States')], default='ES', help_text='Country', max_length=2, verbose_name='Country')),
                ('not_before', models.DateTimeField(blank=True, help_text='Not before', null=True, verbose_name='Not before')),
                ('not_after', models.DateTimeField(blank=True, help_text='Not after', null=True, verbose_name='Not after')),
                ('status', models.CharField(choices=[('new', 'New'), ('active', 'Active'), ('expired', 'Expired')], default='new', help_text='Current CA status', max_length=10, verbose_name='CA Status')),
            ],
        ),
        migrations.CreateModel(
            name='SubCA',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CN', models.CharField(help_text='CA Common Name', max_length=255, verbose_name='Common Name')),
                ('OU', models.CharField(help_text='Organizational unit', max_length=255, verbose_name='Organizational Unit')),
                ('kind', models.CharField(choices=[('component', 'Component'), ('identity', 'Identity')], default='identity', help_text='SubCA Kind', max_length=10, verbose_name='SubCA Kind')),
                ('not_before', models.DateTimeField(blank=True, help_text='Not before', null=True, verbose_name='Not before')),
                ('not_after', models.DateTimeField(blank=True, help_text='Not after', null=True, verbose_name='Not after')),
                ('status', models.CharField(choices=[('new', 'New'), ('active', 'Active'), ('expired', 'Expired')], default='new', help_text='Current SubCA status', max_length=10, verbose_name='SubCA Status')),
                ('ca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_cas', to='ca.CA')),
                ('operators', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
