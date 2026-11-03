                                                                   
from django.conf import settings
from django.db import migrations, models
import django.core.validators
import uuid
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("payment_method", models.CharField(choices=[("MOCK_CARD", "Mock Card"), ("MOCK_UPI", "Mock UPI"), ("MOCK_NET_BANKING", "Mock Net Banking")], default="MOCK_CARD", max_length=30)),
                ("transaction_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("SUCCESS", "Successful"), ("FAILED", "Failed")], db_index=True, default="PENDING", max_length=10)),
                ("card_last4", models.CharField(blank=True, max_length=4)),
                ("failure_reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("booking", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="bookings.booking")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
