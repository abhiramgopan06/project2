                                               

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_booking_agreement_file_booking_agreement_notes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='deposit_status',
            field=models.CharField(choices=[('NOT_COLLECTED', 'Not collected'), ('HELD', 'Held by owner'), ('PARTIALLY_RETURNED', 'Partially returned'), ('RETURNED', 'Returned'), ('DEDUCTED', 'Deducted after inspection')], default='NOT_COLLECTED', max_length=20),
        ),
        migrations.AddField(
            model_name='booking',
            name='move_in_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='move_out_notes',
            field=models.TextField(blank=True),
        ),
    ]
