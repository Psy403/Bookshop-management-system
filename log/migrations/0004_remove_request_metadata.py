from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("log", "0003_activitylogread"),
    ]

    operations = [
        migrations.RemoveField(model_name="activitylog", name="action"),
        migrations.RemoveField(model_name="activitylog", name="path"),
        migrations.RemoveField(model_name="activitylog", name="status_code"),
        migrations.RemoveField(model_name="activitylog", name="ip_address"),
        migrations.AlterField(
            model_name="activitylog",
            name="details",
            field=models.TextField(verbose_name="Event"),
        ),
    ]
