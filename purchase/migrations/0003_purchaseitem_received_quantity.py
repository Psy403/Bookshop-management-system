from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchase", "0002_remove_purchase_expected_delivery_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchaseitem",
            name="received_quantity",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
