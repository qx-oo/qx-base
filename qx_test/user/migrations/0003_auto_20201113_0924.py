# Generated by Django 3.1 on 2020-11-13 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_post'),
    ]

    operations = [
        migrations.CreateModel(
            name='GPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='名称')),
            ],
        ),
        migrations.CreateModel(
            name='TGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='名称')),
                ('perms', models.ManyToManyField(to='user.GPermission', verbose_name='权限')),
            ],
        ),
        migrations.AddField(
            model_name='gpermission',
            name='groups',
            field=models.ManyToManyField(to='user.TGroup', verbose_name='组'),
        ),
    ]