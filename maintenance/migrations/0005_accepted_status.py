from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("maintenance", "0004_technician_reports_rejected_status")]

    operations = [
        migrations.AlterField(
            model_name="maintenanceticket",
            name="status",
            field=models.CharField(choices=[("OPEN", "Open"), ("ASSIGNED", "Assigned"), ("ACCEPTED", "Accepted by Technician"), ("IN_PROGRESS", "In Progress"), ("RESOLVED", "Resolved"), ("CLOSED", "Closed"), ("REJECTED", "Rejected by Technician")], db_index=True, max_length=15, default="OPEN"),
        ),
    ]
