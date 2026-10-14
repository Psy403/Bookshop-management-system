import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0002_saleitem"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sale",
            name="book",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="books.book",
            ),
        ),
        migrations.AlterField(
            model_name="sale",
            name="total_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name="sale",
            name="quantity",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
