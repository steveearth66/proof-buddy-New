# Generated manually on 2025-12-29
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('induction_api', '0004_inductionproofline_selected_node'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='inductionproofline',
            constraint=models.UniqueConstraint(
                fields=['proof', 'case', 'side', 'line_number'],
                name='unique_proof_line',
            ),
        ),
    ]
