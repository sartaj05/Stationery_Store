import uuid

from django.db import migrations, models
import django.db.models.deletion


def populate_quote_tokens(apps, schema_editor):
    BulkOrderRequest = apps.get_model("store", "BulkOrderRequest")
    database = schema_editor.connection.alias
    for request in BulkOrderRequest.objects.using(database).filter(quote_token__isnull=True):
        request.quote_token = uuid.uuid4()
        request.save(update_fields=["quote_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0012_deliveryzone_delivery_zone_fee_nonnegative"),
    ]

    operations = [
        migrations.AddField(
            model_name="bulkorderrequest",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="bulkorderrequest",
            name="quote_token",
            field=models.UUIDField(editable=False, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="bulkorderrequest",
            name="quote_valid_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bulkorderrequest",
            name="converted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(populate_quote_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="bulkorderrequest",
            name="quote_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="bulkorderrequest",
            name="orders",
            field=models.ManyToManyField(
                blank=True,
                related_name="bulk_requests",
                to="store.order",
            ),
        ),
        migrations.CreateModel(
            name="BulkQuoteLine",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("product_name_snapshot", models.CharField(max_length=200)),
                ("product_brand_snapshot", models.CharField(blank=True, max_length=100)),
                ("product_category_snapshot", models.CharField(blank=True, max_length=100)),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="bulk_quote_lines",
                        to="store.product",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quote_lines",
                        to="store.bulkorderrequest",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
    ]
