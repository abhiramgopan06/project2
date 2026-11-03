                                               

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0008_alter_maintenanceticket_status'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='maintenanceticket',
            options={'ordering': ['-created_at'], 'verbose_name': 'Maintenance Work Order', 'verbose_name_plural': 'Maintenance Work Orders'},
        ),
    ]
