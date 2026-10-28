from django.conf import settings
from django.db import migrations
from django.db.models import F, Q


def make_auth_activity_private(apps, schema_editor):
    ActivityLog = apps.get_model("log", "ActivityLog")
    ActivityLog.objects.filter(
        user__isnull=False,
        recipient__isnull=True,
    ).filter(
        Q(details__endswith=" logged in.")
        | Q(details__endswith=" logged out.")
        | Q(details__endswith=" logged out when their tab closed.")
    ).update(recipient_id=F("user_id"))


class Migration(migrations.Migration):

    dependencies = [
        ("log", "0005_activitylog_recipient"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(make_auth_activity_private, migrations.RunPython.noop),
    ]
