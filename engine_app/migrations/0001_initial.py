# Generated by Django 3.0.7 on 2020-08-13 14:19

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
            name='Betrag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=None, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Custom_1',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Custom_2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Custom_3',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Custom_4',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Dimensions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dimensionName', models.CharField(max_length=255)),
                ('new_name', models.CharField(default=None, max_length=100, null=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Document_Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Imported_Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reporting_event', models.CharField(default=None, max_length=255, null=True)),
                ('reporting_period', models.CharField(default=None, max_length=255, null=True)),
                ('entity', models.CharField(default=None, max_length=255, null=True)),
                ('konto', models.CharField(default=None, max_length=255, null=True)),
                ('partner', models.CharField(default=None, max_length=255, null=True)),
                ('movement_type', models.CharField(default=None, max_length=255, null=True)),
                ('investe', models.CharField(default=None, max_length=255, null=True)),
                ('document_type', models.CharField(default=None, max_length=255, null=True)),
                ('value_in_lc', models.CharField(default=None, max_length=255, null=True)),
                ('value_in_gc', models.CharField(default=None, max_length=255, null=True)),
                ('value_in_tc', models.CharField(default=None, max_length=255, null=True)),
                ('quantity', models.CharField(default=None, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Investe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Konto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Mapping_Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('new_name', models.CharField(default=None, max_length=100, null=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Mapping_Rules_Main',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ruleName', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Mapping_Sets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('setName', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='mapping_t_1',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_10',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_3',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_4',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_5',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_6',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_7',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_8',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='mapping_t_9',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Mapping_Table',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mtName', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Master_Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Movement_Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Output_Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reporting_event', models.CharField(default=None, max_length=255, null=True)),
                ('reporting_period', models.CharField(default=None, max_length=255, null=True)),
                ('entity', models.CharField(default=None, max_length=255, null=True)),
                ('konto', models.CharField(default=None, max_length=255, null=True)),
                ('partner', models.CharField(default=None, max_length=255, null=True)),
                ('movement_type', models.CharField(default=None, max_length=255, null=True)),
                ('investe', models.CharField(default=None, max_length=255, null=True)),
                ('document_type', models.CharField(default=None, max_length=255, null=True)),
                ('custom_1', models.CharField(default=None, max_length=255, null=True)),
                ('custom_2', models.CharField(default=None, max_length=255, null=True)),
                ('custom_3', models.CharField(default=None, max_length=255, null=True)),
                ('custom_4', models.CharField(default=None, max_length=255, null=True)),
                ('value_in_lc', models.CharField(default=None, max_length=255, null=True)),
                ('value_in_gc', models.CharField(default=None, max_length=255, null=True)),
                ('value_in_tc', models.CharField(default=None, max_length=255, null=True)),
                ('quantity', models.CharField(default=None, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Reporting_Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Reporting_Period',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=None, max_length=4, null=True)),
                ('long_descr', models.CharField(default=None, max_length=30, null=True)),
                ('short_descr', models.CharField(default=None, max_length=120, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Mapping_Rules',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default=None, max_length=255, null=True)),
                ('row', models.CharField(default=None, max_length=255, null=True)),
                ('dimField', models.CharField(default=None, max_length=255, null=True)),
                ('mtField', models.CharField(default=None, max_length=255, null=True)),
                ('dimensionName', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='engine_app.Dimensions')),
                ('mtName', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='engine_app.Mapping_Data')),
                ('ruleName', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='engine_app.Mapping_Rules_Main')),
                ('setName', models.ManyToManyField(to='engine_app.Mapping_Sets')),
            ],
        ),
        migrations.CreateModel(
            name='Log_Reporting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(default=None, max_length=255, null=True)),
                ('period', models.CharField(default=None, max_length=7, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('comment', models.CharField(default=None, max_length=255, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Log_Mapping_Performe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=255)),
                ('period', models.CharField(max_length=7)),
                ('timestampImportD', models.DateTimeField(auto_now_add=True)),
                ('lastRun', models.DateTimeField(auto_now_add=True)),
                ('setName', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='engine_app.Mapping_Sets')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
