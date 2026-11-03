                                               

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0007_maintenanceticket_materials_used_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maintenanceticket',
            name='status',
            field=models.CharField(choices=[('OPEN', 'New request'), ('ASSIGNED', 'Assigned'), ('ACCEPTED', 'Accepted'), ('IN_PROGRESS', 'In progress'), ('RESOLVED', 'Completed'), ('CLOSED', 'Closed'), ('REJECTED', 'Declined')], db_index=True, default='OPEN', max_length=15),
        ),
    ]
