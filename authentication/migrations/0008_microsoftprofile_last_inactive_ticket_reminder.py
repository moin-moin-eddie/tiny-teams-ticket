# Generated by Django 3.2.4 on 2021-09-22 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_merge_0006_auto_20210920_1649_0006_auto_20210921_0750'),
    ]

    operations = [
        migrations.AddField(
            model_name='microsoftprofile',
            name='last_inactive_ticket_reminder',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
