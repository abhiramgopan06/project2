from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("maintenance", "0002_messages_notifications"),
    ]

    operations = [
        migrations.AddField(
            model_name="technician",
            name="location",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="technician",
            name="experience",
            field=models.PositiveSmallIntegerField(default=0, help_text="Years of relevant work experience"),
        ),
        migrations.AddField(
            model_name="technician",
            name="description",
            field=models.TextField(blank=True, help_text="Describe the technician’s skills and services"),
        ),
    ]
