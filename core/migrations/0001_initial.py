from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("properties", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="PropertyReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(choices=[("INACCURATE", "Inaccurate Information"), ("SCAM", "Suspected Scam"), ("DUPLICATE", "Duplicate Listing"), ("UNAVAILABLE", "Property Unavailable"), ("INAPPROPRIATE", "Inappropriate Content"), ("OTHER", "Other")], max_length=20)),
                ("description", models.TextField(validators=[django.core.validators.MinLengthValidator(10)])),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("REVIEWING", "Under Review"), ("RESOLVED", "Resolved"), ("DISMISSED", "Dismissed")], db_index=True, default="OPEN", max_length=12)),
                ("admin_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="properties.property")),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="property_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
