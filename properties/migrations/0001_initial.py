                                                    
from django.conf import settings
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Amenity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "Amenities"},
        ),
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("property_type", models.CharField(choices=[("APARTMENT", "Apartment"), ("HOUSE", "House"), ("VILLA", "Villa"), ("STUDIO", "Studio"), ("PG", "PG / Shared Accommodation"), ("OFFICE", "Office"), ("OTHER", "Other")], max_length=20)),
                ("location", models.CharField(db_index=True, max_length=150)),
                ("address", models.TextField()),
                ("number_of_rooms", models.PositiveIntegerField(default=1)),
                ("rent", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("available", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="properties", to=settings.AUTH_USER_MODEL)),
                ("amenities", models.ManyToManyField(blank=True, related_name="properties", to="properties.amenity")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PropertyImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="properties/%Y/%m/")),
                ("caption", models.CharField(blank=True, max_length=200)),
                ("is_primary", models.BooleanField(default=False)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("property", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="images", to="properties.property")),
            ],
            options={"ordering": ["-is_primary", "-uploaded_at"]},
        ),
        migrations.CreateModel(
            name="Room",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("room_number", models.CharField(max_length=50)),
                ("room_type", models.CharField(choices=[("SINGLE", "Single"), ("DOUBLE", "Double"), ("SHARED", "Shared"), ("MASTER", "Master"), ("OTHER", "Other")], default="SINGLE", max_length=20)),
                ("rent", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("available", models.BooleanField(default=True)),
                ("description", models.TextField(blank=True)),
                ("property", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="rooms", to="properties.property")),
            ],
            options={"ordering": ["room_number"]},
        ),
        migrations.AddConstraint(
            model_name="room",
            constraint=models.UniqueConstraint(fields=("property", "room_number"), name="unique_room_number_per_property"),
        ),
    ]
