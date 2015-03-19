# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import django.utils.timezone
from django.conf import settings
import cointrol.core.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', default=django.utils.timezone.now)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', default=False, help_text='Designates that this user has all permissions without explicitly assigning them.')),
                ('username', models.CharField(unique=True, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', verbose_name='username', max_length=30)),
                ('first_name', models.CharField(blank=True, verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(blank=True, verbose_name='last name', max_length=30)),
                ('email', models.EmailField(blank=True, verbose_name='email address', max_length=75)),
                ('is_staff', models.BooleanField(verbose_name='staff status', default=False, help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(verbose_name='active', default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('groups', models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', blank=True, related_query_name='user', to='auth.Group', verbose_name='groups', related_name='user_set')),
                ('user_permissions', models.ManyToManyField(help_text='Specific permissions for this user.', blank=True, related_query_name='user', to='auth.Permission', verbose_name='user permissions', related_name='user_set')),
            ],
            options={
                'db_table': 'user',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('api_key', models.CharField(blank=True, max_length=255)),
                ('api_secret', models.CharField(blank=True, max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(related_name='accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'account',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Balance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('inferred', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField()),
                ('usd_balance', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('btc_balance', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('usd_reserved', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('btc_reserved', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('btc_available', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('usd_available', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('fee', cointrol.core.fields.PercentField(decimal_places=3, max_digits=6)),
                ('account', models.ForeignKey(related_name='balances', to='core.Account')),
            ],
            options={
                'get_latest_by': 'timestamp',
                'ordering': ['-timestamp'],
                'db_table': 'bitstamp_balance',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('total', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('status', models.CharField(db_index=True, choices=[(0, 'buy'), (1, 'sell')], default=None, max_length=255)),
                ('status_changed', models.DateTimeField(blank=True, null=True)),
                ('price', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('amount', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('type', models.IntegerField(db_index=True, choices=[(0, 'buy'), (1, 'sell')], max_length=255)),
                ('datetime', models.DateTimeField()),
                ('account', models.ForeignKey(related_name='orders', to='core.Account')),
                ('balance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.Balance', null=True)),
            ],
            options={
                'get_latest_by': 'datetime',
                'ordering': ['-datetime'],
                'db_table': 'bitstamp_order',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Ticker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('volume', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('vwap', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('last', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('high', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('low', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('bid', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('ask', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
            ],
            options={
                'get_latest_by': 'timestamp',
                'ordering': ['-timestamp'],
                'db_table': 'bitstamp_ticker',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TradingSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(db_index=True, choices=[('queued', 'queued'), ('active', 'active'), ('finished', 'finished')], max_length=255)),
                ('became_active', models.DateTimeField(blank=True, null=True)),
                ('became_finished', models.DateTimeField(blank=True, null=True)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('repeat_times', models.PositiveSmallIntegerField(blank=True, null=True, default=None)),
                ('repeat_until', models.DateTimeField(blank=True, null=True)),
                ('account', models.ForeignKey(related_name='trading_sessions', to='core.Account')),
            ],
            options={
                'get_latest_by': 'created',
                'ordering': ['-created'],
                'db_table': 'trading_session',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TradingStrategyProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RelativeStrategyProfile',
            fields=[
                ('tradingstrategyprofile_ptr', models.OneToOneField(to='core.TradingStrategyProfile', serialize=False, parent_link=True, auto_created=True, primary_key=True)),
                ('buy', cointrol.core.fields.PercentField(decimal_places=3, max_digits=6)),
                ('sell', cointrol.core.fields.PercentField(decimal_places=3, max_digits=6)),
            ],
            options={
                'db_table': 'strategy_profile_relative',
            },
            bases=('core.tradingstrategyprofile',),
        ),
        migrations.CreateModel(
            name='FixedStrategyProfile',
            fields=[
                ('tradingstrategyprofile_ptr', models.OneToOneField(to='core.TradingStrategyProfile', serialize=False, parent_link=True, auto_created=True, primary_key=True)),
                ('buy', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('sell', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
            ],
            options={
                'db_table': 'strategy_profile_fixed',
            },
            bases=('core.tradingstrategyprofile',),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('datetime', models.DateTimeField()),
                ('btc', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('usd', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('fee', cointrol.core.fields.AmountField(decimal_places=8, default=0, max_digits=30)),
                ('btc_usd', cointrol.core.fields.PriceField(decimal_places=2, default=0, max_digits=30)),
                ('type', models.PositiveSmallIntegerField(db_index=True, choices=[(0, 'deposit'), (1, 'withdrawal'), (2, 'trade')], max_length=255)),
                ('account', models.ForeignKey(related_name='transactions', to='core.Account')),
                ('balance', models.ForeignKey(to='core.Balance', on_delete=django.db.models.deletion.PROTECT)),
                ('order', models.ForeignKey(to='core.Order', null=True, related_name='transactions')),
            ],
            options={
                'get_latest_by': 'datetime',
                'ordering': ['-datetime'],
                'db_table': 'bitstamp_transaction',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='tradingstrategyprofile',
            name='account',
            field=models.ForeignKey(to='core.Account'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tradingstrategyprofile',
            name='leaf_content_type',
            field=models.ForeignKey(verbose_name='leaf type', null=True, to='contenttypes.ContentType', editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tradingsession',
            name='strategy_profile',
            field=models.ForeignKey(to='core.TradingStrategyProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='trading_session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='core.TradingSession', null=True, related_name='orders'),
            preserve_default=True,
        ),
    ]
