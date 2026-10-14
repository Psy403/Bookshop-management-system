from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0003_delete_purchase_delete_return"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="book",
            name="publication_date",
        ),
        migrations.AlterField(
            model_name="stock",
            name="quantity",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
