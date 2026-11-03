from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Admin"),
                    ("OWNER", "Property Owner"),
                    ("TENANT", "Tenant"),
                    ("TECHNICIAN", "Technician"),
                ],
                default="TENANT",
                max_length=10,
            ),
        ),
    ]
