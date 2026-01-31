# Generated manually on 2025-12-29
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('induction_api', '0004_inductionproofline_selected_node'),
    ]

    operations = [
        # First, remove duplicate proof lines (keep the most recent one for each unique combination)
        # MySQL-compatible version using a temporary table approach
        migrations.RunSQL(
            sql="""
                DELETE t1 FROM induction_api_inductionproofline t1
                INNER JOIN induction_api_inductionproofline t2 
                WHERE 
                    t1.proof_id = t2.proof_id AND
                    t1.case = t2.case AND
                    t1.side = t2.side AND
                    t1.line_number = t2.line_number AND
                    t1.id < t2.id;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # Then add the unique constraint
        migrations.AddConstraint(
            model_name='inductionproofline',
            constraint=models.UniqueConstraint(
                fields=['proof', 'case', 'side', 'line_number'],
                name='unique_proof_line'
            ),
        ),
    ]
