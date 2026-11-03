from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("maintenance", "0005_accepted_status")]

    operations = [
        migrations.AddField(
            model_name="maintenanceticket",
            name="tenant_photo",
            field=models.ImageField(blank=True, null=True, upload_to="maintenance/reported/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="maintenanceticket",
            name="resolution_photo",
            field=models.ImageField(blank=True, null=True, upload_to="maintenance/resolved/%Y/%m/"),
        ),
    ]
