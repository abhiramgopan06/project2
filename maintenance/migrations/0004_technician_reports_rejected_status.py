from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("maintenance", "0003_technician_location_experience_description")]

    operations = [
        migrations.AlterField(
            model_name="maintenanceticket",
            name="status",
            field=models.CharField(
                choices=[("OPEN", "Open"), ("ASSIGNED", "Assigned"), ("IN_PROGRESS", "In Progress"), ("RESOLVED", "Resolved"), ("CLOSED", "Closed"), ("REJECTED", "Rejected by Technician")],
                db_index=True,
                max_length=15,
            ),
        ),
        migrations.CreateModel(
            name="TechnicianReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=180)),
                ("description", models.TextField(max_length=2000)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("REVIEWING", "Reviewing"), ("RESOLVED", "Resolved")], default="OPEN", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("technician", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="maintenance.technician")),
                ("ticket", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="technician_reports", to="maintenance.maintenanceticket")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
