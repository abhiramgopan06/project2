import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0002_property_latitude_property_longitude"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="verification_status",
            field=models.CharField(choices=[("PENDING", "Pending review"), ("VERIFIED", "Verified"), ("REJECTED", "Needs changes")], db_index=True, default="PENDING", max_length=12),
        ),
        migrations.AddField(
            model_name="property",
            name="verification_note",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.CreateModel(
            name="SavedProperty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_by", to="properties.property")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_properties", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="savedproperty",
            constraint=models.UniqueConstraint(fields=("user", "property"), name="unique_saved_property_per_user"),
        ),
        migrations.CreateModel(
            name="PropertyVerificationDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document", models.FileField(upload_to="verification_documents/%Y/%m/")),
                ("description", models.CharField(blank=True, max_length=180)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_documents", to="properties.property")),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
    ]
